import { useI18n } from '../i18n';
import { useEffect, useState } from 'react';
import { Search } from 'lucide-react';
import { useData } from '../hooks/useData';
import { Empty, ErrorBox, JobCard, Loading, PageTitle } from '../components/UI';

export default function Jobs({ saved = false }: { saved?: boolean }) {
  const { t, enumLabel } = useI18n();
  const [search, setSearch] = useState('');
  const [query, setQuery] = useState('');
  const [role, setRole] = useState('');
  const [location, setLocation] = useState('');
  const [employment, setEmployment] = useState('');
  const [sort, setSort] = useState('match');
  const [page, setPage] = useState(1);
  const roles = useData<any[]>('/catalog/career-roles');
  useEffect(() => { const timer = setTimeout(() => { setQuery(search); setPage(1); }, 300); return () => clearTimeout(timer); }, [search]);
  const params = new URLSearchParams({ q: query, location, employment_type: employment, sort, page: String(page), limit: '12' });
  if (role) params.set('role_id', role);
  const { data, loading, error, reload } = useData(saved ? '/saved-jobs' : '/jobs?' + params);
  const items = saved ? data || [] : data?.items || [];
  const total = saved ? items.length : data?.total || 0;
  return <><PageTitle eyebrow={t('dashboard.next')} title={saved ? t('jobs.savedTitle') : t('jobs.title')} description={saved ? t('jobs.savedDescription') : t('jobs.description')} />{!saved && <div className="jobs-filters"><div className="search-input"><Search size={18} /><input aria-label={t('jobs.search')} placeholder={t('jobs.searchPlaceholder')} value={search} onChange={e => setSearch(e.target.value)} /></div><select aria-label={t('profile.direction')} value={role} onChange={e => { setRole(e.target.value); setPage(1); }}><option value="">{t('jobs.allDirections')}</option>{roles.data?.map(item => <option value={item.id} key={item.id}>{item.name}</option>)}</select><select aria-label={t('common.location')} value={location} onChange={e => { setLocation(e.target.value); setPage(1); }}><option value="">{t('jobs.allLocations')}</option>{['Astana', 'Almaty', 'Remote'].map(value => <option key={value} value={value}>{enumLabel(value)}</option>)}</select><select aria-label={t('common.employment')} value={employment} onChange={e => { setEmployment(e.target.value); setPage(1); }}><option value="">{t('jobs.anyEmployment')}</option>{['Full-time', 'Part-time', 'Internship', 'Freelance'].map(value => <option key={value} value={value}>{enumLabel(value)}</option>)}</select></div>}{roles.error && <ErrorBox message={roles.error} retry={roles.reload} />}<div className="list-toolbar"><span className="muted">{t('common.jobCount', { count: total })}</span>{!saved && <select aria-label={t('jobs.sort')} value={sort} onChange={e => { setSort(e.target.value); setPage(1); }}><option value="match">{t('jobs.byMatch')}</option><option value="recent">{t('jobs.recent')}</option></select>}</div>{error ? <ErrorBox message={error} retry={reload} /> : loading ? <Loading /> : items.length ? <div className="jobs-grid">{items.map((job: any) => <JobCard key={job.id} job={{ ...job, saved: saved || job.saved }} onChange={saved ? reload : undefined} />)}</div> : <Empty title={saved ? t('jobs.noSaved') : t('jobs.notFound')} description={saved ? t('jobs.saveHint') : t('jobs.filtersHint')} />}{!saved && total > 12 && <div className="pagination"><button className="button outline" disabled={page === 1} onClick={() => setPage(p => p - 1)}>{t('common.back')}</button><span>{page} / {Math.ceil(total / 12)}</span><button className="button outline" disabled={page * 12 >= total} onClick={() => setPage(p => p + 1)}>{t('common.next')}</button></div>}<p className="data-note">{t('jobs.demoNote')}</p></>;
}
