import { useConfirm } from '../components/ConfirmProvider';
import { useI18n } from '../i18n';
import { lazy, Suspense, useState, type FormEvent } from 'react';
import { Pencil, Plus, Trash2, Users, BriefcaseBusiness, Layers, Activity } from 'lucide-react';
import { useData } from '../hooks/useData';
import { useAuth } from '../hooks/Auth';
import { api } from '../services/api';
import { Empty, ErrorBox, Field, Loading, PageTitle, Success, levelNames } from '../components/UI';
import Modal from '../components/Modal';
import { TechnologyPicker } from './Portfolio';


const HHImportDialog = lazy(() => import('../components/HHImportDialog'));

export default function Admin() {
  const { t, enumLabel } = useI18n();
  const tabs: Record<string, string> = { jobs: t('common.jobs'), users: t('admin.users'), skills: t('common.skills'), 'skill-categories': t('admin.skillCategories'), 'career-roles': t('admin.roles'), 'job-categories': t('admin.jobCategories') };

  const { user } = useAuth();
  const [tab, setTab] = useState('jobs');
  const records = useData<any[]>('/admin/' + tab);
  const stats = useData('/admin/statistics');
  const catalog = useData<any[]>('/catalog/skills');
  const roles = useData<any[]>('/catalog/career-roles');
  const skillCategories = useData<any[]>('/catalog/skill-categories');
  const jobCategories = useData<any[]>('/catalog/job-categories');
  const [importing, setImporting] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [requirements, setRequirements] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState('');
  const [success, setSuccess] = useState('');
  function edit(item: any = {}) { setEditing(item); setRequirements(item.skills?.map((s: any) => ({ skill_id: s.skill_id, required: s.required, level: s.level, weight: s.weight })) || []); setFailure(''); }
  function refresh() { records.reload(); stats.reload(); catalog.reload(); roles.reload(); skillCategories.reload(); jobCategories.reload(); }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setFailure('');
    const body: any = Object.fromEntries(new FormData(event.currentTarget));
    if (tab === 'jobs') {
      body.role_id = Number(body.role_id); body.category_id = Number(body.category_id);
      body.salary_min = body.salary_min ? Number(body.salary_min) : null; body.salary_max = body.salary_max ? Number(body.salary_max) : null;
      body.skills = requirements;
    } else if (tab === 'skills') { body.category_id = Number(body.category_id); body.aliases = String(body.aliases || '').split(',').map(x => x.trim()).filter(Boolean); }
    try { await api(`/admin/${tab}${editing.id ? '/' + editing.id : ''}`, { method: editing.id ? 'PUT' : 'POST', body }); setEditing(null); setSuccess('admin.saved'); refresh(); }
    catch (err: any) { setFailure(err.message); } finally { setBusy(false); }
  }
  const confirm = useConfirm();
  async function remove(item: any) {
    if (!await confirm(item.title || item.name || item.email)) return;
    setBusy(true); setFailure('');
    try { await api(`/admin/${tab}/${item.id}`, { method: 'DELETE' }); setSuccess('admin.deleted'); refresh(); }
    catch (err: any) { setFailure(err.message); } finally { setBusy(false); }
  }
  async function updateUser(item: any, changes: any) {
    setBusy(true); setFailure('');
    try { await api(`/admin/users/${item.id}`, { method: 'PUT', body: { active: item.active, role: item.role, ...changes } }); records.reload(); }
    catch (err: any) { setFailure(err.message); } finally { setBusy(false); }
  }
  return <><PageTitle eyebrow={t('admin.eyebrow')} title={t('common.admin')} description={t('admin.description')} />{stats.error && <ErrorBox message={stats.error} retry={stats.reload} />}<div className="admin-stats">{[['users', t('admin.users'), Users], ['jobs', t('common.jobs'), BriefcaseBusiness], ['skills', t('common.skills'), Layers], ['matches', t('admin.matches'), Activity]].map(([key, label, Icon]: any) => <div className="stat-card" key={key}><Icon size={21} /><strong>{stats.data?.[key] ?? '—'}</strong><span className="muted">{label}</span></div>)}</div><div className="tabs">{Object.entries(tabs).map(([key, label]) => <button className={tab === key ? 'active' : ''} key={key} onClick={() => { setTab(key); setFailure(''); setSuccess(''); }}>{label}</button>)}</div>{success && <Success message={success} />}{failure && !editing && <ErrorBox message={failure} />}<section className="panel"><div className="panel-heading"><h2>{tabs[tab]}</h2>{tab === 'jobs' && <button className="button outline small" onClick={() => setImporting(true)}>{t('admin.hhTitle')}</button>}{tab !== 'users' && <button className="button primary small" onClick={() => edit()}><Plus size={16} />{t('common.add')}</button>}</div>{records.loading ? <Loading /> : records.error ? <ErrorBox message={records.error} retry={records.reload} /> : !records.data?.length ? <Empty title={t('common.emptyRecords')} /> : <div className="table-wrap"><table><thead><tr><th>{tab === 'users' ? t('admin.user') : t('common.name')}</th><th>{tab === 'jobs' ? t('common.company') : tab === 'users' ? t('admin.role') : t('admin.details')}</th><th>{t('admin.actions')}</th></tr></thead><tbody>{records.data.map(item => <tr key={item.id}><td><strong>{item.title || item.name}</strong>{tab === 'users' && <small>{item.email}</small>}</td><td>{tab === 'jobs' ? item.company : tab === 'users' ? <select aria-label={t('admin.userRole', { email: item.email })} value={item.role} disabled={busy || item.id === user?.id} onChange={e => updateUser(item, { role: e.target.value })}><option value="graduate">{t('admin.graduate')}</option><option value="admin">{t('common.administrator')}</option></select> : item.category || '—'}</td><td><div className="table-actions">{tab === 'users' ? <button className="button outline small" disabled={busy || item.id === user?.id} onClick={() => updateUser(item, { active: !item.active })}>{item.active ? t('admin.block') : t('admin.activate')}</button> : <button className="icon-button" aria-label={t('common.editItem', { name: item.title || item.name })} onClick={() => edit(item)}><Pencil size={16} /></button>}<button className="icon-button danger" aria-label={t('common.deleteItem', { name: item.title || item.name || item.email })} disabled={busy || (tab === 'users' && item.id === user?.id)} onClick={() => remove(item)}><Trash2 size={16} /></button></div></td></tr>)}</tbody></table></div>}</section>{importing && <Suspense fallback={<Loading />}><HHImportDialog roles={roles.data || []} categories={jobCategories.data || []} close={() => setImporting(false)} completed={refresh} /></Suspense>}{editing && <Modal title={editing.id ? t('admin.editRecord') : t('admin.addRecord')} close={() => setEditing(null)}>{failure && <ErrorBox message={failure} />}<form className="editor-form" onSubmit={submit}>{tab === 'jobs' ? <><div className="form-grid">{[['title', t('common.position')], ['company', t('common.company')], ['location', t('common.location')]].map(([name, label]) => <Field label={label} key={name}><input name={name} defaultValue={editing[name] || ''} required minLength={2} maxLength={150} /></Field>)}<Field label={t('admin.careerRole')}><select name="role_id" defaultValue={editing.role_id || ''} required><option value="" disabled>{t('admin.selectRole')}</option>{roles.data?.map(item => <option value={item.id} key={item.id}>{item.name}</option>)}</select></Field><Field label={t('admin.jobCategory')}><select name="category_id" defaultValue={editing.category_id || ''} required><option value="" disabled>{t('common.selectCategory')}</option>{jobCategories.data?.map(item => <option value={item.id} key={item.id}>{item.name}</option>)}</select></Field><Field label={t('admin.experienceLevel')}><select name="experience_level" defaultValue={editing.id ? editing.experience_level ?? '' : 'Junior'}>{editing.id && !['Intern', 'Junior', 'Middle', 'Senior'].includes(editing.experience_level) && <option value={editing.experience_level ?? ''}>{editing.experience_level}</option>}{['Intern', 'Junior', 'Middle', 'Senior'].map(x => <option key={x} value={x}>{enumLabel(x)}</option>)}</select></Field><Field label={t('admin.employment')}><select name="employment_type" defaultValue={editing.id ? editing.employment_type ?? '' : 'Full-time'}>{editing.id && !['Full-time', 'Part-time', 'Internship', 'Freelance'].includes(editing.employment_type) && <option value={editing.employment_type ?? ''}>{editing.employment_type}</option>}{['Full-time', 'Part-time', 'Internship', 'Freelance'].map(x => <option key={x} value={x}>{enumLabel(x)}</option>)}</select></Field><Field label={t('admin.salaryMin')}><input name="salary_min" type="number" min={0} defaultValue={editing.salary_min ?? ''} /></Field><Field label={t('admin.salaryMax')}><input name="salary_max" type="number" min={0} defaultValue={editing.salary_max ?? ''} /></Field><Field label={t('admin.currency')}><input name="currency" defaultValue={editing.currency || 'KZT'} required pattern="[A-Z]{3}" maxLength={3} /></Field></div><Field label={t('common.description')}><textarea name="description" defaultValue={editing.description || ''} required minLength={20} maxLength={15000} rows={5} /></Field><TechnologyPicker catalog={catalog.data || []} selected={requirements.map(s => s.skill_id)} setSelected={ids => setRequirements(ids.map(id => requirements.find(s => s.skill_id === id) || { skill_id: id, required: true, level: 1, weight: 2 }))} />{requirements.length > 0 && <div className="requirement-editor">{requirements.map((s, index) => <div className="requirement-row" key={s.skill_id}><strong>{catalog.data?.find(x => x.id === s.skill_id)?.name}</strong><label><input type="checkbox" checked={s.required} onChange={e => setRequirements(current => current.map((x, i) => i === index ? { ...x, required: e.target.checked, weight: e.target.checked ? 2 : 1 } : x))} /> {t('common.required')}</label><select aria-label={t('admin.requirementLevel', { id: s.skill_id })} value={s.level} onChange={e => setRequirements(current => current.map((x, i) => i === index ? { ...x, level: Number(e.target.value) } : x))}>{Object.entries(levelNames).map(([id, name]) => <option key={id} value={id}>{t(name)}</option>)}</select><label>{t('admin.weight')} <input aria-label={t('admin.requirementWeight', { id: s.skill_id })} type="number" min={0.1} max={10} step={0.1} value={s.weight} onChange={e => setRequirements(current => current.map((x, i) => i === index ? { ...x, weight: Number(e.target.value) } : x))} /></label></div>)}</div>}<p className="data-note">{t('admin.requirementsHint')}</p></> : <><Field label={t('common.name')}><input name="name" defaultValue={editing.name || ''} required minLength={2} maxLength={100} /></Field>{tab === 'skills' && <><Field label={t('common.category')}><select name="category_id" defaultValue={editing.category_id || ''} required><option value="" disabled>{t('common.selectCategory')}</option>{skillCategories.data?.map(x => <option value={x.id} key={x.id}>{x.name}</option>)}</select></Field><Field label={t('admin.aliases')}><input name="aliases" defaultValue={editing.aliases?.join(', ') || ''} placeholder="JS, JavaScript Development" /></Field></>}</>}<div className="form-actions"><button type="button" className="button outline" onClick={() => setEditing(null)}>{t('common.cancel')}</button><button className="button primary" type="submit" disabled={busy}>{busy ? t('common.saving') : t('common.save')}</button></div></form></Modal>}</>;
}
