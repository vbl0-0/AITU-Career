/** Synchronize existing issue cards from current GitHub data; never close issues. */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

export function referencedIssues(body = '', repository) {
  const plain = body.replace(/<!--[\s\S]*?-->/g, '').replace(/```[\s\S]*?```|~~~[\s\S]*?~~~/g, '');
  const numbers = new Set();
  for (const line of plain.split(/\r?\n/)) {
    if (!/^\s*(?:task\s*:|refs?\b|close[sd]?\b|fix(?:e[sd])?\b|resolve[sd]?\b)/i.test(line)) continue;
    const tokens = line.matchAll(/https:\/\/github\.com\/([\w.-]+\/[\w.-]+)\/issues\/(\d+)|(?<![\w./-])(?:([\w.-]+\/[\w.-]+))?#(\d+)/g);
    for (const token of tokens) {
      const target = token[1] || token[3];
      const number = Number(token[2] || token[4]);
      if ((!target || target.toLowerCase() === repository.toLowerCase()) && Number.isSafeInteger(number) && number > 0) numbers.add(number);
    }
  }
  return [...numbers];
}

export function trackedPullRequests(pulls, config, defaultBranch) {
  return pulls.filter(pr => pr.head?.repo?.full_name?.toLowerCase() === config.repository.toLowerCase()
    && pr.base?.ref === defaultBranch && config.team.includes(pr.user?.login));
}

export function desiredStatus(issue, current, pulls, event, eventName, config) {
  if (issue.state === 'CLOSED') return issue.stateReason === 'NOT_PLANNED' ? 'To Do' : 'Done';
  const related = pulls.filter(pr => referencedIssues(pr.body || '', config.repository).includes(issue.number));
  if (related.some(pr => !pr.draft)) return 'Review';
  if (related.length) return 'In Progress';
  const fromPr = event.pull_request;
  if (fromPr && config.team.includes(fromPr.user?.login)
      && fromPr.head?.repo?.full_name?.toLowerCase() === config.repository.toLowerCase()
      && fromPr.base?.ref === (config.defaultBranch || 'main')
      && referencedIssues(fromPr.body || '', config.repository).includes(issue.number)
      && event.action === 'closed') return 'In Progress';
  if (eventName === 'push' && config.team.includes(event.sender?.login)) {
    const branch = /^refs\/heads\/AITU-(\d+)-/.exec(event.ref || '');
    if (branch && Number(branch[1]) === issue.number) return 'In Progress';
  }
  if ((eventName === 'issues' && event.action === 'reopened' && event.issue?.number === issue.number) || current === 'Done') return 'To Do';
  return current || 'To Do';
}

export class GitHubClient {
  constructor(token, fetcher = fetch) { this.token = token; this.fetcher = fetcher; }
  async request(path, payload) {
    const response = await this.fetcher('https://api.github.com' + path, {
      method: payload ? 'POST' : 'GET', redirect: 'error', signal: AbortSignal.timeout(30000),
      headers: { Authorization: `Bearer ${this.token}`, Accept: 'application/vnd.github+json',
        'Content-Type': 'application/json', 'User-Agent': 'AITU-Career-project-sync', 'X-GitHub-Api-Version': '2022-11-28' },
      ...(payload ? { body: JSON.stringify(payload) } : {}),
    });
    if (!response.ok) throw new Error(`GitHub API HTTP ${response.status}; check token permissions and Actions logs.`);
    const data = await response.json();
    if (data.errors?.length) throw new Error('GitHub GraphQL rejected the request; check project permissions and field configuration.');
    return data;
  }
  async graphql(query, variables) { return (await this.request('/graphql', { query, variables })).data; }
  async list(path) {
    const items = [];
    for (let page = 1; ; page++) {
      const batch = await this.request(`${path}${path.includes('?') ? '&' : '?'}per_page=100&page=${page}`);
      if (!Array.isArray(batch)) throw new Error('Unexpected paginated GitHub response.');
      items.push(...batch);
      if (batch.length < 100) return items;
    }
  }
}

export async function synchronize(client, config, event = {}, eventName = '', log = console.log) {
  if (event.repository && event.repository.full_name?.toLowerCase() !== config.repository.toLowerCase()) throw new Error('Unexpected repository.');
  const projectData = await client.graphql(`query($owner:String!,$number:Int!){user(login:$owner){projectV2(number:$number){id fields(first:100){pageInfo{hasNextPage} nodes{... on ProjectV2SingleSelectField{id name options{id name}}}}}}}`, { owner: config.owner, number: config.number });
  const project = projectData.user?.projectV2;
  if (!project) throw new Error('Project is unavailable to this token.');
  if (project.fields.pageInfo.hasNextPage) throw new Error('Too many project fields; refusing partial configuration.');
  const field = project.fields.nodes.find(field => field.name === 'Status');
  const options = Object.fromEntries((field?.options || []).map(option => [option.name, option.id]));
  if (!field || ['To Do', 'In Progress', 'Review', 'Done'].some(name => !options[name])) throw new Error('Expected four Status options were not found.');
  const items = [];
  let after = null;
  do {
    const data = await client.graphql(`query($id:ID!,$after:String){node(id:$id){... on ProjectV2{items(first:100,after:$after){pageInfo{hasNextPage endCursor} nodes{id content{... on Issue{id number state stateReason repository{nameWithOwner}}} fieldValueByName(name:"Status"){... on ProjectV2ItemFieldSingleSelectValue{name}}}}}}}`, { id: project.id, after });
    const connection = data.node?.items;
    if (!connection) throw new Error('Project items are unavailable.');
    items.push(...connection.nodes);
    after = connection.pageInfo.hasNextPage ? connection.pageInfo.endCursor : null;
    if (connection.pageInfo.hasNextPage && !after) throw new Error('Missing project pagination cursor.');
  } while (after);
  const [repo, allPulls] = await Promise.all([
    client.request(`/repos/${config.repository}`), client.list(`/repos/${config.repository}/pulls?state=open`),
  ]);
  const pulls = trackedPullRequests(allPulls, config, repo.default_branch);
  let updated = 0;
  for (const item of items) {
    const issue = item.content;
    if (!issue?.id || issue.repository?.nameWithOwner?.toLowerCase() !== config.repository.toLowerCase()) continue;
    const current = item.fieldValueByName?.name;
    const next = desiredStatus(issue, current, pulls, event, eventName, { ...config, defaultBranch: repo.default_branch });
    if (next === current) continue;
    await client.graphql(`mutation($input:UpdateProjectV2ItemFieldValueInput!){updateProjectV2ItemFieldValue(input:$input){clientMutationId}}`, {
      input: { projectId: project.id, itemId: item.id, fieldId: field.id, value: { singleSelectOptionId: options[next] } },
    });
    updated++;
    log(`#${issue.number}: ${current || 'unset'} → ${next}`);
  }
  return { checked: items.length, updated };
}

async function main() {
  const token = process.env.PROJECTS_TOKEN;
  if (!token) {
    console.log('::warning::Project sync is inactive: add the PROJECTS_TOKEN Actions secret. No board changes made.');
    return;
  }
  const config = JSON.parse(readFileSync(resolve(import.meta.dirname, '../project-sync.json'), 'utf8'));
  if (process.env.GITHUB_REPOSITORY?.toLowerCase() !== config.repository.toLowerCase()) throw new Error('Workflow repository does not match configuration.');
  const event = JSON.parse(readFileSync(process.env.GITHUB_EVENT_PATH, 'utf8'));
  const result = await synchronize(new GitHubClient(token), config, event, process.env.GITHUB_EVENT_NAME);
  console.log(`Checked ${result.checked} existing cards; updated ${result.updated}. No issues were closed by this script.`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main().catch(error => { console.error(error.message); process.exitCode = 1; });
}
