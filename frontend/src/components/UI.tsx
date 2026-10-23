import { useI18n } from '../i18n';
import { cloneElement, isValidElement, useId, type ReactNode } from 'react';
import { ArrowUpRight, Check, LoaderCircle, MapPin, Bookmark, BookmarkCheck, Sparkles, AlertCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { useState } from 'react';

export function PageTitle({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return <div className="page-title"><div>{eyebrow && <p className="eyebrow">{eyebrow}</p>}<h1>{title}</h1>{description && <p className="muted">{description}</p>}</div>{action}</div>;
}
export function Loading() {
  const { t } = useI18n(); return <div className="loading" role="status"><LoaderCircle className="spin" size={25} /> {t('common.loading')}</div>; }
export function ErrorBox({ message, retry }: { message: string; retry?: () => void }) {
  const { t, message: translateMessage } = useI18n();
  return <div className="error" role="alert"><AlertCircle size={18} /><span>{translateMessage(message)}</span>{retry && <button className="text-button" onClick={retry}>{t('common.retry')}</button>}</div>;
}
export function Empty({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return <div className="empty"><Sparkles size={30} /><h3>{title}</h3><p className="muted">{description}</p>{action}</div>;
}
export function Score({ value, large = false }: { value: number | null; large?: boolean }) {
  const { number } = useI18n();
  return <span className={`score ${large ? 'large' : ''} ${(value ?? 0) >= 70 ? 'good' : (value ?? 0) >= 40 ? 'medium' : 'low'}`}>{value === null ? '—' : `${number(Math.round(value))}%`}</span>;
}
export function Ring({ value, label }: { value: number; label?: string }) {
  const { t, number } = useI18n();
  label ||= t('common.readinessLabel');
  return <div className="ring" role="img" aria-label={`${number(Math.round(value))}% ${label}`}><svg viewBox="0 0 180 180"><circle cx="90" cy="90" r="73" className="ring-track" /><circle cx="90" cy="90" r="73" className="ring-fill" strokeDasharray={`${Math.max(0, Math.min(100, value)) * 4.5867} 458.67`} /></svg><div><strong>{number(Math.round(value))}<small>%</small></strong><span>{label}</span></div></div>;
}
export function Tags({ items, tone = '' }: { items: string[]; tone?: string }) { return <div className="tags">{items.map(item => <span className={`tag ${tone}`} key={item}>{item}</span>)}</div>; }
export function SaveButton({ id, saved, onChange }: { id: number; saved: boolean; onChange?: () => void }) {
  const { t, message: translateMessage } = useI18n();
  const [value, setValue] = useState(saved);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function toggle() {
    setBusy(true); setError('');
    try { await api(`/saved-jobs/${id}`, { method: value ? 'DELETE' : 'POST' }); setValue(!value); onChange?.(); }
    catch (err: any) { setError(err.message); } finally { setBusy(false); }
  }
  return <div><button className={`icon-button ${value ? 'selected' : ''}`} aria-label={value ? t('common.unsaveJob') : t('common.saveJob')} onClick={toggle} disabled={busy}>{busy ? <LoaderCircle className="spin" size={18} /> : value ? <BookmarkCheck size={19} /> : <Bookmark size={19} />}</button>{error && <span role="alert" className="small-error">{translateMessage(error)}</span>}</div>;
}
export function JobCard({ job, onChange }: { job: any; onChange?: () => void }) {
  const { t, number, enumLabel } = useI18n();
  return <article className="job-card"><div className="job-top"><div className="company-icon">{job.company.slice(0, 1)}</div><div><span className="company-name">{job.company}</span><span className="job-location"><MapPin size={12} />{job.location}</span></div><SaveButton key={`${job.id}-${job.saved}`} id={job.id} saved={job.saved ?? false} onChange={onChange} /></div><Link className="job-title" to={`/jobs/${job.id}`}>{job.title}</Link><div className="job-meta">{job.experience_level}{job.experience_level && job.employment_type && <span>·</span>}{job.employment_type ? enumLabel(job.employment_type) : ''}</div>{job.skills && <Tags items={job.skills.filter((s: any) => s.required).slice(0, 4).map((s: any) => s.name)} />}<div className="job-bottom"><div>{job.score !== undefined ? <><Score value={job.score} /><span className="match-label"> {t('common.matchLabel')}</span></> : <span className="muted">{job.salary_min == null && job.salary_max == null ? t('jobs.noSalary') : <>{job.salary_min === null || job.salary_min === undefined ? '…' : number(job.salary_min)}–{job.salary_max === null || job.salary_max === undefined ? '…' : number(job.salary_max)} {job.currency}</>}</span>}</div><Link to={`/jobs/${job.id}`} className="icon-link" aria-label={t('common.open', { name: job.title })}><ArrowUpRight size={20} /></Link></div>{job.is_active === false && <span className="demo-label">{t('jobs.closed')}</span>}{job.source === 'hh' && job.source_url && <a className="demo-label inline-link" href={job.source_url} target="_blank" rel="noopener noreferrer">{t('jobs.original')}</a>}{job.is_demo && <span className="demo-label">{t('common.demoJob')}</span>}</article>;
}
export function Success({ message }: { message: string }) {
  const { message: translateMessage } = useI18n(); return <div className="success" role="status"><Check size={17} />{translateMessage(message)}</div>; }
export const levelNames: Record<number, string> = { 1: 'common.levelBeginner', 2: 'common.levelIntermediate', 3: 'common.levelAdvanced' };
export function Field({ label, children }: { label: string; children: ReactNode }) {
  const id = useId();
  return <div className="field"><label htmlFor={id}>{label}</label>{isValidElement<{ id?: string }>(children) ? cloneElement(children, { id }) : children}</div>;
}
