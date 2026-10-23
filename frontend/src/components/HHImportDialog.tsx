import { useState, type FormEvent } from 'react';
import { useI18n } from '../i18n';
import { api } from '../services/api';
import Modal from './Modal';
import { ErrorBox, Field, Success } from './UI';

type Result = { created: number; updated: number; unchanged: number; archived: number; skipped: number };
export default function HHImportDialog({ roles, categories, close, completed }: {
  roles: { id: number; name: string }[]; categories: { id: number; name: string }[];
  close: () => void; completed: () => void;
}) {
  const { t } = useI18n();
  const [mode, setMode] = useState('import');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<Result | null>(null);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(''); setResult(null);
    const form = new FormData(event.currentTarget);
    const role = Number(form.get('role_id'));
    const body = mode === 'sync' ? { role_id: role || null, limit: Number(form.get('limit')) }
      : { text: form.get('text'), role_id: role, category_id: Number(form.get('category_id')), limit: Number(form.get('limit')), area_id: '40', experience: form.get('experience') };
    try {
      setResult(await api<Result>(`/admin/jobs/${mode}/hh`, { method: 'POST', body, timeoutMs: 120000 }));
      completed();
    } catch (error: unknown) { setError(error instanceof Error ? error.message : 'errors.request'); }
    finally { setBusy(false); }
  }
  return <Modal title={t('admin.hhTitle')} close={() => { if (!busy) close(); }}>
    <p className="data-note">{t('admin.hhHelp')}</p>
    {error && <ErrorBox message={error} />}
    {result && <Success message={t('admin.hhResult', result)} />}
    <form onSubmit={submit} className="editor-form">
      <Field label={t('admin.hhMode')}><select value={mode} disabled={busy} onChange={event => { setMode(event.target.value); setResult(null); setError(''); }}>
        <option value="import">{t('admin.hhImport')}</option><option value="sync">{t('admin.hhSync')}</option>
      </select></Field>
      {mode === 'import' && <Field label={t('admin.hhQuery')}><input name="text" required minLength={2} maxLength={150} placeholder="Python OR FastAPI" disabled={busy} /></Field>}
      <div className="form-grid">
        <Field label={t('admin.careerRole')}><select name="role_id" required={mode === 'import'} defaultValue="" disabled={busy}>
          <option value="">{mode === 'sync' ? t('jobs.allDirections') : t('admin.selectRole')}</option>
          {roles.map(role => <option key={role.id} value={role.id}>{role.name}</option>)}
        </select></Field>
        {mode === 'import' && <><Field label={t('admin.jobCategory')}><select name="category_id" required defaultValue="" disabled={busy}>
          <option value="" disabled>{t('common.selectCategory')}</option>{categories.map(category => <option key={category.id} value={category.id}>{category.name}</option>)}
        </select></Field>
          <Field label={t('admin.experienceLevel')}><select name="experience" defaultValue="noExperience" disabled={busy}>
            <option value="noExperience">{t('admin.hhNoExperience')}</option><option value="between1And3">{t('admin.hhJunior')}</option><option value="">{t('admin.hhAnyExperience')}</option>
          </select></Field></>}
        <Field label={t('admin.hhLimit')}><input type="number" name="limit" min={1} max={20} defaultValue={10} required disabled={busy} /></Field>
      </div>
      <div className="form-actions"><button type="button" className="button outline" disabled={busy} onClick={close}>{t('common.close')}</button>
        <button type="submit" className="button primary" disabled={busy}>{busy ? t('common.loading') : mode === 'import' ? t('admin.hhImport') : t('admin.hhSync')}</button>
      </div>
    </form>
  </Modal>;
}
