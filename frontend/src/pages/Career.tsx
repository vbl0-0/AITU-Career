import { Link } from 'react-router-dom';
import { ArrowUpRight, Sparkles } from 'lucide-react';
import { useData } from '../hooks/useData';
import { profileAction, useI18n } from '../i18n';
import { Empty, ErrorBox, Loading, PageTitle, Ring, Score } from '../components/UI';

export default function Career() {
  const { t, number, list } = useI18n();
  const { data, loading, error, reload } = useData('/recommendations');
  const componentNames: Record<string, string> = { market: t('career.market'), projects: t('career.projects'), experience: t('career.experience'), certificates: t('common.certificates'), education: t('common.education') };
  if (loading) return <Loading />;
  if (error) return <ErrorBox message={error} retry={reload} />;
  return <><PageTitle eyebrow={t('career.eyebrow')} title={t('career.title')} description={t('career.description')} />
    <div className="career-grid"><section className="panel"><h2>{t('career.priorities')}</h2>
      {data.skill_gaps.length ? data.skill_gaps.map((gap: any, index: number) => <div className="recommendation-row" key={gap.skill}>
        <span className="step-dot">{number(index + 1)}</span><div><h3>{gap.skill}</h3><p>{t('career.practice', { skill: gap.skill })}</p>
          <small className="muted">{t('career.priority', { priority: number(gap.priority) })}</small></div>
        <Link to="/projects" className="icon-link" aria-label={t('career.addProjectWith', { skill: gap.skill })}><ArrowUpRight size={20} /></Link>
      </div>) : <Empty title={t('career.noGaps')} description={t('career.noGapsHint')} />}
      <div className="career-project-idea"><Sparkles size={21} /><div><strong>{t('career.idea')}</strong>
        <p>{data.skill_gaps.length ? t('career.extend', { skills: list(data.skill_gaps.slice(0, 2).map((gap: any) => gap.skill)) }) : t('career.addPortfolio')}</p>
      </div></div>
    </section><aside className="panel readiness-breakdown"><h2>{t('common.readiness')}</h2><Ring value={data.readiness} />
      <div>{Object.entries(data.readiness_contributions).map(([key, value]: any) => <div className="breakdown-row" key={key}><span>{componentNames[key]}</span><strong>+{number(value, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</strong></div>)}</div>
      <details><summary>{t('common.howScore')}</summary><p>{t('career.formula')}</p><p>{t('career.formulaDescription')}</p>
        <p>{t('career.weights', { weights: Object.entries(data.readiness_weights).map(([key, value]: any) => `${componentNames[key]} ${number(value * 100, { maximumFractionDigits: 0 })}%`).join('; ') })}</p>
        <p>{t('career.sample', { count: data.market_sample_size })}</p>
      </details>
    </aside></div>
    <section className="panel recommendation-panel"><h2>{t('career.directions')}</h2>{data.career_directions.map((direction: any) => <div className="direction-row" key={direction.role}><strong>{direction.role}</strong><div className="progress-track"><span style={{ width: `${direction.score}%` }} /></div><Score value={direction.score} /></div>)}<p className="data-note">{t('career.directionsNote')}</p></section>
    {data.profile_improvements.length > 0 && <section className="panel"><h2>{t('career.improve')}</h2>{data.profile_improvements.map((text: string) => <p key={text}>{t(profileAction(text).key)}</p>)}<Link className="button outline" to="/profile">{t('career.goProfile')} <ArrowUpRight size={17} /></Link></section>}
  </>;
}
