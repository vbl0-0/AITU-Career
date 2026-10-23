import { useI18n } from '../i18n';
import { useState, type FormEvent } from 'react';
import { Save, UserRound } from 'lucide-react';
import { useData } from '../hooks/useData';
import { useAuth } from '../hooks/Auth';
import { api } from '../services/api';
import { ErrorBox, Field, Loading, PageTitle, Success } from '../components/UI';
import Portfolio from './Portfolio';

export default function Profile() {
  const { t, enumLabel } = useI18n();
  const { data, loading, error, reload } = useData('/profile');
  const roles = useData<any[]>('/catalog/career-roles');
  const { updateName } = useAuth();
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState('');
  const [success, setSuccess] = useState('');
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setFailure(''); setSuccess(''); setBusy(true);
    const body: any = Object.fromEntries(new FormData(event.currentTarget));
    body.desired_role_id = body.desired_role_id ? Number(body.desired_role_id) : null;
    try { const result = await api('/profile', { method: 'PUT', body }); updateName(result.name); setSuccess('profile.updated'); reload(); }
    catch (err: any) { setFailure(err.message); } finally { setBusy(false); }
  }
  if (loading) return <Loading />;
  if (error) return <ErrorBox message={error} retry={reload} />;
  return <><PageTitle eyebrow={t('profile.eyebrow')} title={t('common.profile')} description={t('profile.description')} />{success && <Success message={success} />}{failure && <ErrorBox message={failure} />}<div className="profile-grid"><aside className="profile-summary"><div className="profile-avatar"><UserRound size={43} /></div><h2>{data.name}</h2><p>{data.email}</p><span className="pill">{t('profile.community')}</span><hr /><strong>{t('profile.direction')}</strong><p>{data.desired_role || t('profile.notSelected')}</p><p className="data-note">{t('profile.completeness')}</p></aside><div><form className="panel profile-form" onSubmit={submit} key={data.revision}><h2>{t('profile.personal')}</h2><div className="form-grid"><Field label={t('common.fullName')}><input name="name" defaultValue={data.name} required minLength={2} maxLength={150} /></Field><Field label={t('profile.phone')}><input type="tel" name="phone" defaultValue={data.phone} maxLength={40} /></Field><Field label={t('profile.city')}><input name="location" defaultValue={data.location} maxLength={150} /></Field><Field label={t('common.email')}><input value={data.email} disabled /></Field></div><Field label={t('profile.about')}><textarea name="bio" defaultValue={data.bio} rows={3} maxLength={4000} /></Field><h2>{t('profile.preferences')}</h2>{roles.error && <ErrorBox message={roles.error} retry={roles.reload} />}<div className="form-grid"><Field label={t('profile.targetRole')}><select name="desired_role_id" defaultValue={data.desired_role_id || ''} disabled={roles.loading}><option value="">{t('profile.selectDirection')}</option>{roles.data?.map(role => <option key={role.id} value={role.id}>{role.name}</option>)}</select></Field><Field label={t('common.employment')}><select name="employment_type" defaultValue={data.employment_type}>{['Full-time', 'Part-time', 'Internship', 'Freelance'].map(type => <option key={type} value={type}>{enumLabel(type)}</option>)}</select></Field><Field label={t('profile.location')}><input name="preferred_location" defaultValue={data.preferred_location} maxLength={150} /></Field><Field label={t('profile.technologies')}><input name="preferred_technologies" defaultValue={data.preferred_technologies} maxLength={500} placeholder="Python, React…" /></Field></div><div className="form-actions"><button type="submit" className="button primary" disabled={busy || roles.loading || !!roles.error}><Save size={17} />{busy ? t('common.saving') : t('profile.save')}</button></div></form><section className="panel education-panel"><Portfolio kind="education" embedded /></section></div></div></>;
}
