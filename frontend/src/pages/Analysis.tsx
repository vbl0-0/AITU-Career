import { useI18n } from '../i18n';
import { Link, useParams } from 'react-router-dom';
import { RefreshCw } from 'lucide-react';
import { useData } from '../hooks/useData';
import { ErrorBox, Loading, PageTitle, Score } from '../components/UI';
import { MatchGroups } from './JobDetail';

export default function Analysis() {
  const { t, number, date, matchExplanation } = useI18n();
  const { id } = useParams();
  const { data, loading, error, reload } = useData('/matches/' + id);
  if (loading) return <Loading />;
  if (error) return <ErrorBox message={error} retry={reload} />;
  return <><PageTitle eyebrow={t('match.eyebrow')} title={t('match.title')} description={data.job_title} action={<Score value={data.score} large />} />{data.stale && <div className="demo-notice">{t('match.stale')} <Link to={`/jobs/${data.job_id}`}>{t('match.recalculateAnalysis')} <RefreshCw size={14} /></Link></div>}<div className="panel analysis-explanation"><p>{matchExplanation(data)}</p><div className="formula"><code>{data.formula}</code><span>{t('match.formula', { earned: number(data.weighted_earned), total: number(data.weighted_total) })}</span></div><p className="data-note">{t('match.weightsNote')}</p></div><MatchGroups match={data} /><section className="panel recommendation-panel"><h2>{t('match.recommendations')}</h2>{data.recommendations.length ? data.recommendations.map((rec: any, index: number) => <div className="recommendation-row" key={rec.skill}><span className="step-dot">{index + 1}</span><div><h3>{rec.skill}</h3><p>{t('match.practice')}</p></div><Link to="/skills">{t('match.mySkills')}</Link></div>) : <p className="muted">{t('match.covered')}</p>}</section><p className="data-note">{t('match.metadata', { algorithm: data.algorithm_version, mode: data.mode, date: date(data.created_at, true) })}</p></>;
}
