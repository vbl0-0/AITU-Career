import { useConfirm } from '../components/ConfirmProvider';
import { useI18n } from '../i18n';
import { useState, type FormEvent } from 'react';
import { Award, BriefcaseBusiness, FolderGit2, GraduationCap, Layers, Pencil, Plus, Trash2, ExternalLink } from 'lucide-react';
import { useData } from '../hooks/useData';
import { api } from '../services/api';
import { Empty, ErrorBox, Field, Loading, PageTitle, Success, Tags, levelNames } from '../components/UI';
import Modal from '../components/Modal';

type Kind = 'skills' | 'projects' | 'certificates' | 'experience' | 'education';
type Spec = { name: string; label: string; type?: string; required?: boolean; options?: string[]; max?: number; min?: number };


export function TechnologyPicker({ catalog, selected, setSelected }: { catalog: any[]; selected: number[]; setSelected: (value: number[]) => void }) {
  const { t } = useI18n();
  const [search, setSearch] = useState('');
  return <div className="field"><span>{t('portfolio.technologies')}</span><input aria-label={t('portfolio.findTechnology')} placeholder={t('portfolio.findTechnologyPlaceholder')} value={search} onChange={e => setSearch(e.target.value)} /><div className="technology-picker">{catalog.filter(s => s.name.toLowerCase().includes(search.toLowerCase())).map(s => <label key={s.id}><input type="checkbox" checked={selected.includes(s.id)} onChange={e => setSelected(e.target.checked ? [...selected, s.id] : selected.filter(id => id !== s.id))} />{s.name}</label>)}</div><small className="muted">{t('portfolio.selected', { count: selected.length })}</small></div>;
}

export default function Portfolio({ kind, embedded = false }: { kind: Kind; embedded?: boolean }) {
  const { t, date, enumLabel } = useI18n();
  const configs: Record<Kind, { title: string; subtitle: string; icon: typeof Layers; fields: Spec[] }> = {
  skills: { title: t('portfolio.skillsTitle'), subtitle: t('portfolio.skillsDescription'), icon: Layers, fields: [] },
  projects: { title: t('portfolio.projectsTitle'), subtitle: t('portfolio.projectsDescription'), icon: FolderGit2, fields: [
    { name: 'name', label: t('portfolio.projectName'), required: true, max: 150 }, { name: 'description', label: t('common.description'), type: 'textarea', max: 5000 },
    { name: 'github_url', label: t('portfolio.repositoryUrl'), type: 'url', max: 500 }, { name: 'project_type', label: t('portfolio.projectType'), options: ['Academic', 'Personal', 'Commercial', 'Open source'] }] },
  certificates: { title: t('portfolio.certificatesTitle'), subtitle: t('portfolio.certificatesDescription'), icon: Award, fields: [
    { name: 'name', label: t('portfolio.certificateName'), required: true, max: 150 }, { name: 'issuer', label: t('portfolio.issuer'), required: true, max: 150 },
    { name: 'issued_date', label: t('portfolio.issuedDate'), type: 'date', required: true }, { name: 'credential_url', label: t('portfolio.credentialUrl'), type: 'url', max: 500 }] },
  experience: { title: t('portfolio.experienceTitle'), subtitle: t('portfolio.experienceDescription'), icon: BriefcaseBusiness, fields: [
    { name: 'company', label: t('common.company'), required: true, max: 150 }, { name: 'position', label: t('common.position'), required: true, max: 150 },
    { name: 'description', label: t('portfolio.tasks'), type: 'textarea', max: 5000 },
    { name: 'employment_type', label: t('common.employment'), options: ['Internship', 'Part-time', 'Full-time', 'Freelance'] },
    { name: 'start_date', label: t('portfolio.startDate'), type: 'date', required: true }, { name: 'end_date', label: t('portfolio.endDate'), type: 'date' }] },
  education: { title: t('common.education'), subtitle: t('portfolio.educationDescription'), icon: GraduationCap, fields: [
    { name: 'university', label: t('portfolio.university'), required: true, max: 200 }, { name: 'degree', label: t('portfolio.degree'), required: true, max: 80 },
    { name: 'program', label: t('portfolio.program'), required: true, max: 150 }, { name: 'graduation_year', label: t('portfolio.graduationYear'), type: 'number', required: true, min: 1950, max: 2100 }] },
};

  const config = configs[kind];
  const { data, loading, error, reload } = useData<any[]>('/' + kind);
  const catalog = useData<any[]>('/catalog/skills');
  const [editing, setEditing] = useState<any | null>(null);
  const [selected, setSelected] = useState<number[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [failure, setFailure] = useState('');
  const [search, setSearch] = useState('');
  const Icon = config.icon;
  function edit(item: any = {}) { setEditing(item); setSelected(item.skill_ids || []); setFailure(''); setMessage(''); }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setFailure('');
    const body: any = Object.fromEntries(new FormData(event.currentTarget));
    if (kind === 'skills') { body.skill_id = Number(body.skill_id); body.level = Number(body.level); }
    if (kind === 'projects') body.skill_ids = selected;
    if (kind === 'education') body.graduation_year = Number(body.graduation_year);
    if (kind === 'experience' && !body.end_date) body.end_date = null;
    try { await api(`/${kind}${editing.id ? '/' + editing.id : ''}`, { method: editing.id ? 'PUT' : 'POST', body }); setEditing(null); setMessage('portfolio.saved'); reload(); }
    catch (err: any) { setFailure(err.message); } finally { setBusy(false); }
  }
  const confirm = useConfirm();
  async function remove(item: any) {
    if (!await confirm(item.name || item.position || item.program)) return;
    setFailure(''); setBusy(true);
    try { await api(`/${kind}/${item.id}`, { method: 'DELETE' }); reload(); setMessage('portfolio.deleted'); }
    catch (err: any) { setFailure(err.message); } finally { setBusy(false); }
  }
  const available = catalog.data || [];
  const filtered = (data || []).filter(item => `${item.name || item.position || item.program} ${item.company || ''}`.toLowerCase().includes(search.toLowerCase()));
  return <div className={embedded ? 'embedded-manager' : ''}>{embedded ? <div className="panel-heading"><h2>{config.title}</h2><button className="button outline small" onClick={() => edit()}><Plus size={16} />{t('common.add')}</button></div> : <PageTitle eyebrow={t('portfolio.eyebrow')} title={config.title} description={config.subtitle} action={<button className="button primary" onClick={() => edit()}><Plus size={17} />{t(`portfolio.add.${kind}`)}</button>} />}{message && <Success message={message} />}{failure && !editing && <ErrorBox message={failure} />}{error && <ErrorBox message={error} retry={reload} />}{loading ? <Loading /> : !data?.length ? <Empty title={t(`portfolio.empty.${kind}`)} description={config.subtitle} action={<button className="button outline" onClick={() => edit()}><Plus size={16} />{t('common.add')}</button>} /> : <><div className="list-toolbar"><input aria-label={t('portfolio.search')} placeholder={t('portfolio.searchPlaceholder')} value={search} onChange={e => setSearch(e.target.value)} /><span className="muted">{t('common.records', { count: data.length })}</span></div><div className={kind === 'skills' ? 'skills-grid' : 'record-list'}>{filtered.map(item => <article className="record-card" key={item.id}><span className={`record-icon ${kind === 'certificates' ? 'info' : ''}`}><Icon size={23} /></span><div className="record-content"><h3>{item.name || item.position || item.program}</h3>{kind === 'skills' && <><p>{item.category}</p><span className={`level-badge level-${item.level}`}>{t(levelNames[item.level])}</span></>}{kind === 'projects' && <><p>{item.description}</p><Tags items={item.technologies} />{item.github_url && <a className="inline-link" href={item.github_url} target="_blank" rel="noreferrer">{t('portfolio.repository')} <ExternalLink size={13} /></a>}</>}{kind === 'certificates' && <><p>{item.issuer} · {date(item.issued_date)}</p>{item.credential_url && <a className="inline-link" href={item.credential_url} target="_blank" rel="noreferrer">{t('portfolio.certificate')} <ExternalLink size={13} /></a>}</>}{kind === 'experience' && <><p>{item.company} · {enumLabel(item.employment_type)}</p><small className="muted">{date(item.start_date)} — {item.end_date ? date(item.end_date) : t('portfolio.present')}</small><p>{item.description}</p></>}{kind === 'education' && <p>{item.university} · {item.degree} · {item.graduation_year}</p>}</div><div className="record-actions"><button className="icon-button" aria-label={t('common.editItem', { name: item.name || item.position || item.program })} onClick={() => edit(item)}><Pencil size={16} /></button><button className="icon-button danger" aria-label={t('common.deleteItem', { name: item.name || item.position || item.program })} disabled={busy} onClick={() => remove(item)}><Trash2 size={16} /></button></div></article>)}</div>{!filtered.length && <Empty title={t('common.noResults')} description={t('common.changeQuery')} />}</>}{editing && <Modal title={t(`portfolio.${editing.id ? 'edit' : 'add'}.${kind}`)} close={() => setEditing(null)}>{failure && <ErrorBox message={failure} />}<form onSubmit={submit} className="editor-form">{kind === 'skills' ? <>{catalog.loading ? <Loading /> : catalog.error ? <ErrorBox message={catalog.error} retry={catalog.reload} /> : <><Field label={t('common.skill')}><select name="skill_id" required defaultValue={editing.skill_id || ''}><option value="" disabled>{t('portfolio.selectSkill')}</option>{available.filter(s => editing.skill_id === s.id || !(data || []).some(item => item.skill_id === s.id)).map(s => <option key={s.id} value={s.id}>{s.name} · {s.category}</option>)}</select></Field><Field label={t('common.proficiency')}><select name="level" defaultValue={editing.level || 2}>{Object.entries(levelNames).map(([id, name]) => <option key={id} value={id}>{t(name)}</option>)}</select></Field><p className="data-note">{t('portfolio.levelHint')}</p></>}</> : config.fields.map(field => <Field key={field.name} label={field.label}>{field.type === 'textarea' ? <textarea name={field.name} defaultValue={editing[field.name] || ''} maxLength={field.max} rows={4} /> : field.options ? <select name={field.name} defaultValue={editing[field.name] || field.options[0]}>{field.options.map(option => <option key={option} value={option}>{enumLabel(option)}</option>)}</select> : <input type={field.type || 'text'} name={field.name} defaultValue={editing[field.name] || (field.name === 'university' ? 'Astana IT University' : field.name === 'degree' ? 'Bachelor' : '')} required={field.required} minLength={field.required && !field.type ? 2 : undefined} min={field.type === 'number' ? field.min : undefined} max={field.type === 'number' ? field.max : undefined} maxLength={field.type !== 'number' ? field.max : undefined} />}</Field>)}{kind === 'projects' && (catalog.loading ? <Loading /> : catalog.error ? <ErrorBox message={catalog.error} retry={catalog.reload} /> : <TechnologyPicker catalog={available} selected={selected} setSelected={setSelected} />)}<div className="form-actions"><button type="button" className="button outline" onClick={() => setEditing(null)}>{t('common.cancel')}</button><button type="submit" className="button primary" disabled={busy || ((kind === 'skills' || kind === 'projects') && (!catalog.data || catalog.loading))}>{busy ? t('common.saving') : t('common.save')}</button></div></form></Modal>}</div>;
}
