import { test } from 'node:test';
import assert from 'node:assert/strict';
import { desiredStatus, referencedIssues, trackedPullRequests, GitHubClient, synchronize } from './project-sync.mjs';

const config = { repository: 'vbl0-0/AITU-Career', owner: 'vbl0-0', number: 1, team: ['vbl0-0', 'igiiaw'] };
const issue = { id: 'ISSUE_8', number: 8, state: 'OPEN', stateReason: null, repository: { nameWithOwner: config.repository } };
const pr = { body: 'Task: #8\nRefs #8', draft: false, user: { login: 'igiiaw' }, head: { repo: { full_name: config.repository } }, base: { ref: 'main' } };

test('only explicit local task lines are linked, deduplicated and kept out of quoted examples', () => {
  assert.deepEqual(referencedIssues('Task: #8\nRefs #8, #9\nCloses vbl0-0/AITU-Career#12\nRefs https://github.com/vbl0-0/AITU-Career/issues/14\nRefs stranger/project#15\nExample #16\n```\nCloses #17\n```\n<!--\nTask: #18\n-->', config.repository), [8, 9, 12, 14]);
  assert.deepEqual(referencedIssues('Task: #0\nTask: #999999999999999999999\nRefs https://github.com/other/project/issues/22', config.repository), []);
});

test('forks, unknown authors and PRs to another base are ignored', () => {
  const candidates = [pr, { ...pr, head: { repo: { full_name: 'stranger/fork' } } },
    { ...pr, user: { login: 'outsider' } }, { ...pr, base: { ref: 'feature' } }];
  assert.deepEqual(trackedPullRequests(candidates, config, 'main'), [pr]);
});

test('a ready PR requests Review; a draft or task branch indicates In Progress', () => {
  assert.equal(desiredStatus(issue, 'To Do', [pr], {}, '', config), 'Review');
  assert.equal(desiredStatus(issue, 'To Do', [{ ...pr, draft: true }], {}, '', config), 'In Progress');
  const event = { ref: 'refs/heads/AITU-8-frontend-delivery', sender: { login: 'igiiaw' } };
  assert.equal(desiredStatus(issue, 'To Do', [], event, 'push', config), 'In Progress');
  assert.equal(desiredStatus(issue, 'To Do', [], { ...event, sender: { login: 'outsider' } }, 'push', config), 'To Do');
});

test('a ready PR keeps Review during pushes and wins over a second draft', () => {
  const event = { ref: 'refs/heads/AITU-8-frontend-delivery', sender: { login: 'igiiaw' } };
  assert.equal(desiredStatus(issue, 'Review', [pr, { ...pr, draft: true }], event, 'push', config), 'Review');
});

test('merging a partial PR never completes an open issue; cancellation is not completion', () => {
  const event = { action: 'closed', pull_request: { ...pr, merged: true } };
  assert.equal(desiredStatus(issue, 'Review', [], event, 'pull_request', config), 'In Progress');
  assert.equal(desiredStatus({ ...issue, state: 'CLOSED', stateReason: 'COMPLETED' }, 'Review', [], event, 'pull_request', config), 'Done');
  assert.equal(desiredStatus({ ...issue, state: 'CLOSED', stateReason: 'NOT_PLANNED' }, 'Review', [], event, 'pull_request', config), 'To Do');
  assert.equal(desiredStatus(issue, 'To Do', [], { ...event, pull_request: { ...pr, base: { ref: 'other-feature' } } }, 'pull_request', config), 'To Do');
});

test('reopened issues leave Done, while manual open-work status is preserved', () => {
  assert.equal(desiredStatus(issue, 'Done', [], {}, 'schedule', config), 'To Do');
  assert.equal(desiredStatus(issue, 'Review', [], { action: 'reopened', issue: { number: 8 } }, 'issues', config), 'To Do');
  assert.equal(desiredStatus(issue, 'In Progress', [], {}, 'schedule', config), 'In Progress');
});

test('API client paginates and rejects HTTP and GraphQL errors without printing credentials', async () => {
  const calls = [];
  const client = new GitHubClient('test-not-a-real-token', async (url, options) => {
    calls.push({ url, options });
    return { ok: true, json: async () => calls.length === 1 ? Array(100).fill({ number: 1 }) : [{ number: 2 }] };
  });
  assert.equal((await client.list('/repos/vbl0-0/AITU-Career/pulls?state=open')).length, 101);
  assert.match(calls[1].url, /page=2/);
  assert.equal(calls[0].options.redirect, 'error');
  const denied = new GitHubClient('sensitive', async () => ({ ok: false, status: 403 }));
  await assert.rejects(() => denied.request('/graphql'), error => !error.message.includes('sensitive') && /403/.test(error.message));
  const invalid = new GitHubClient('sensitive', async () => ({ ok: true, json: async () => ({ data: {}, errors: [{ message: 'private data' }] }) }));
  await assert.rejects(() => invalid.graphql('query {}'), /GraphQL rejected/);
});

function fixture(current = 'To Do', options = {}) {
  const writes = [], reads = [];
  const client = {
    request: async () => ({ default_branch: 'main' }),
    list: async () => options.pulls ?? [pr],
    graphql: async (query, variables) => {
      if (query.startsWith('mutation')) { writes.push(variables.input); return {}; }
      if (query.includes('fields(first:100)')) return { user: { projectV2: { id: 'PROJECT', fields: {
        pageInfo: { hasNextPage: false }, nodes: [{ id: 'STATUS', name: 'Status', options:
          ['To Do', 'In Progress', 'Review', 'Done'].map(name => ({ name, id: name.toUpperCase() })) }],
      } } } };
      reads.push(variables.after);
      if (!variables.after && options.paginate) return { node: { items: { pageInfo: { hasNextPage: true, endCursor: 'NEXT' }, nodes: [
        { id: 'OTHER_ITEM', content: { ...issue, id: 'OTHER_ISSUE', repository: { nameWithOwner: 'other/repo' } }, fieldValueByName: { name: 'To Do' } },
      ] } } };
      return { node: { items: { pageInfo: { hasNextPage: false, endCursor: null }, nodes: [
        { id: 'ITEM_8', content: issue, fieldValueByName: { name: current } }, { id: 'DRAFT', content: {} },
      ] } } };
    },
  };
  return { client, writes, reads };
}

test('integration updates only the existing local issue card, without closing issues or adding duplicates', async () => {
  const { client, writes, reads } = fixture('To Do', { paginate: true });
  const result = await synchronize(client, config, {}, 'schedule', () => {});
  assert.deepEqual(reads, [null, 'NEXT']);
  assert.deepEqual(result, { checked: 3, updated: 1 });
  assert.deepEqual(writes, [{ projectId: 'PROJECT', itemId: 'ITEM_8', fieldId: 'STATUS', value: { singleSelectOptionId: 'REVIEW' } }]);
});

test('unchanged cards cause no mutations and an unexpected repository is rejected before API access', async () => {
  const { client, writes } = fixture('Review');
  assert.equal((await synchronize(client, config, {}, 'schedule', () => {})).updated, 0);
  assert.equal(writes.length, 0);
  await assert.rejects(() => synchronize({}, config, { repository: { full_name: 'other/repo' } }), /Unexpected repository/);
});
