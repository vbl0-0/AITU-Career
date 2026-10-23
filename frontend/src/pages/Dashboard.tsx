import { useI18n } from '../i18n';
import { Link } from 'react-router-dom';
import { ArrowRight, ArrowUpRight, BriefcaseBusiness, Layers, MapPin, Sparkles, Target } from 'lucide-react';
import { useAuth } from '../hooks/Auth';
import { useData } from '../hooks/useData';
import { profileAction } from '../i18n';
import { Empty, ErrorBox, Loading, PageTitle, Ring, SaveButton, Score, Tags, levelNames } from '../components/UI';

type Factor = 'market' | 'projects' | 'experience' | 'certificates' | 'education';
type RecommendedJob = {
  id: number; title: string; company: string; location?: string; employment_type?: string;
  score: number | null; saved: boolean; is_demo: boolean;
  skills?: { name: string; required: boolean }[];
};
type DashboardData = {
  readiness: number; readiness_components: Record<Factor, number>;
  readiness_contributions: Record<Factor, number>; readiness_weights: Record<Factor, number>;
  market_sample_size: number; competency_count: number; desired_role?: string | null;
  recommended_job_count?: number; skill_gap_count?: number;
  top_skills: { skill_id: number; name: string; level: number; inferred: boolean; sources: string[] }[];
  skill_gaps: { skill: string; priority: number; action: string }[];
  recommended_jobs: RecommendedJob[]; profile_improvements: string[];
};



function ReadinessDetails({ data }: { data: DashboardData }) {
  const { t, number } = useI18n();
  const factors: { key: Factor; label: string; description: string }[] = [
  { key: 'market', label: t('dashboard.skillsMarket'), description: t('dashboard.marketDescription') },
  { key: 'projects', label: t('common.projects'), description: t('dashboard.projectsDescription') },
  { key: 'experience', label: t('common.experience'), description: t('dashboard.experienceDescription') },
  { key: 'certificates', label: t('common.certificates'), description: t('dashboard.certificatesDescription') },
  { key: 'education', label: t('common.education'), description: t('dashboard.educationDescription') },
];

  const totalWeight = Object.values(data.readiness_weights).reduce((sum, value) => sum + value, 0);
  return <details className="dashboard-assessment">
    <summary><Target size={18} /> {t('dashboard.factors')} <span className="assessment-show">{t('dashboard.showFactors')}</span><span className="assessment-hide">{t('dashboard.hideFactors')}</span></summary>
    <div className="assessment-content">
      <p className="muted">{t('dashboard.assessmentDescription', { score: number(data.readiness) })}</p>
      <div className="assessment-factors">{factors.map(({ key, label, description }) => <div className="assessment-factor" key={key}>
        <div><strong>{label}</strong><span>{t('dashboard.points', { value: number(data.readiness_contributions[key], { maximumFractionDigits: 2 }) })}</span></div>
        <div className="progress-track" aria-hidden="true"><span style={{ width: `${data.readiness_components[key] * 100}%` }} /></div>
        <p>{description}</p>
        <small>{t('dashboard.weight', { value: number(totalWeight ? Math.round(data.readiness_weights[key] / totalWeight * 100) : 0) })}</small>
      </div>)}</div>
      <p className="data-note">{t('dashboard.sampleNote', { count: data.market_sample_size })}</p>
      <Link className="inline-link" to="/recommendations">{t('dashboard.detailedAssessment')} <ArrowRight size={16} /></Link>
    </div>
  </details>;
}

function VacancyRow({ job }: { job: RecommendedJob }) {
  const { t, enumLabel } = useI18n();
  const skills = job.skills?.filter(skill => skill.required).slice(0, 4).map(skill => skill.name) || [];
  return <article className="dashboard-job">
    <div className="company-icon" aria-hidden="true">{job.company.slice(0, 1)}</div>
    <div className="dashboard-job-main">
      <h3><Link to={`/jobs/${job.id}`}>{job.title}</Link></h3>
      <p className="dashboard-job-meta"><strong>{job.company}</strong>{job.location && <span><MapPin size={13} />{job.location}</span>}{job.employment_type && <span>{enumLabel(job.employment_type)}</span>}</p>
      {skills.length > 0 && <Tags items={skills} />}
      {job.is_demo && <span className="demo-label">{t('common.demoJob')}</span>}
    </div>
    <div className="dashboard-job-match"><Score value={job.score} /><span>{t('dashboard.skillsMatch')}</span></div>
    <div className="dashboard-job-actions">
      <Link className="button outline small" to={`/jobs/${job.id}`} aria-label={t('dashboard.detailsLabel', { title: job.title })}>{t('dashboard.details')} <ArrowUpRight size={16} /></Link>
      <SaveButton id={job.id} saved={job.saved} />
    </div>
  </article>;
}

export default function Dashboard() {
  const { t, sourceLabel } = useI18n();
  const { user } = useAuth();
  const { data, loading, error, reload } = useData<DashboardData>('/dashboard');
  if (loading) return <Loading />;
  if (error) return <ErrorBox message={error} retry={reload} />;
  if (!data) return <Empty title={t('dashboard.unavailable')} action={<button className="button outline" onClick={reload}>{t('common.retry')}</button>} />;

  const jobs = data.recommended_jobs.filter(job => typeof job.score === 'number' && Number.isFinite(job.score) && job.score > 0 && job.score <= 100)
    .sort((a, b) => b.score! - a.score!);
  const hasSkills = data.competency_count > 0;
  const hasMarket = data.market_sample_size > 0;
  const gaps = data.skill_gaps;
  const recommendations = [
    ...data.profile_improvements.slice(0, 2).map(text => ({ title: t(profileAction(text).key), description: t('dashboard.missingSection'), path: profileAction(text).path, action: t('dashboard.complete') })),
    ...gaps.slice(0, 2).map(gap => ({ title: t('dashboard.practice', { skill: gap.skill }), description: t('career.gapAction', { skill: gap.skill }), path: '/projects', action: t('portfolio.add.projects') })),
  ].slice(0, 3);

  return <div className="dashboard">
    <PageTitle eyebrow={t('dashboard.eyebrow')} title={t('dashboard.greeting', { name: user?.name.trim().split(/\s+/)[0] || t('common.student') })}
      description={data.desired_role ? t('dashboard.direction', { role: data.desired_role }) : t('dashboard.description')}
      action={<Link className="button outline" to="/profile">{t('dashboard.editProfile')} <ArrowUpRight size={17} /></Link>} />

    <section className="dashboard-stats" aria-label={t('dashboard.metrics')}>
      <article className="dashboard-readiness">
        <Ring value={data.readiness} />
        <div><h2>{t('common.readiness')}</h2><p>{t('dashboard.readinessDescription')}</p><a className="inline-link" href="#readiness-details" onClick={() => {
          const details = document.querySelector<HTMLDetailsElement>('#readiness-details details');
          if (details) details.open = true;
        }}>{t('common.howScore')} <ArrowRight size={16} /></a></div>
      </article>
      <article className="dashboard-stat">
        <span className="dashboard-stat-icon"><BriefcaseBusiness size={20} /></span>
        <h2>{t('dashboard.suitableJobs')}</h2><strong>{data.recommended_job_count ?? jobs.length}</strong>
        <p>{t('dashboard.matchNote')}</p><Link className="inline-link" to="/jobs">{t('common.allJobs')} <ArrowRight size={15} /></Link>
      </article>
      <article className="dashboard-stat">
        <span className="dashboard-stat-icon"><Layers size={20} /></span>
        <h2>{t('dashboard.skillsToImprove')}</h2><strong>{hasMarket ? (data.skill_gap_count ?? gaps.length) : '—'}</strong>
        <p>{hasMarket ? t('dashboard.gapsDescription') : t('dashboard.needRequirements')}</p><a className="inline-link" href="#skill-gaps">{t('dashboard.viewGaps')} <ArrowRight size={15} /></a>
      </article>
    </section>
    <div id="readiness-details"><ReadinessDetails data={data} /></div>

    <section className="panel dashboard-vacancies" aria-labelledby="recommended-vacancies-title">
      <div className="panel-heading"><div><h2 id="recommended-vacancies-title">{t('dashboard.recommendedJobs')}</h2><p className="muted">{t('dashboard.bestMatches')}</p></div><Link to="/jobs">{t('common.allJobs')} <ArrowRight size={17} /></Link></div>
      {jobs.length ? <div className="dashboard-job-list">{jobs.slice(0, 3).map(job => <VacancyRow key={job.id} job={job} />)}</div>
        : <Empty title={hasSkills ? t('dashboard.noMatches') : t('dashboard.startSkills')}
          description={hasSkills ? t('dashboard.noMatchesHint') : t('dashboard.startSkillsHint')}
          action={<Link className="button outline" to="/jobs">{t('dashboard.goJobs')} <ArrowRight size={16} /></Link>} />}
      <p className="data-note">{t('dashboard.demoNote')}</p>
    </section>

    <div className="dashboard-competencies">
      <section className="panel dashboard-skills" aria-labelledby="skills-overview-title">
        <div className="panel-heading"><h2 id="skills-overview-title">{t('dashboard.strengths')}</h2><Link to="/skills">{t('common.allSkills')} <ArrowUpRight size={16} /></Link></div>
        <p className="muted">{t('dashboard.proficiencyNote', { count: data.competency_count })}</p>
        {data.top_skills.length ? <div className="skill-bars">{data.top_skills.slice(0, 5).map(skill => <div key={skill.skill_id}>
          <div className="skill-bar-label"><strong>{skill.name}</strong><span>{t(levelNames[skill.level])} · {skill.level}/3</span></div>
          <div className="progress-track" aria-hidden="true"><span style={{ width: `${skill.level / 3 * 100}%` }} /></div>
          <small className="skill-evidence" title={skill.sources.map(sourceLabel).join(' · ')}>{skill.inferred ? t('dashboard.inferred') : t('dashboard.sources', { label: skill.sources.includes('\u0417\u0430\u044f\u0432\u043b\u0435\u043d\u043d\u044b\u0439 \u043d\u0430\u0432\u044b\u043a') ? t('dashboard.declared') : t('dashboard.fromProject'), count: skill.sources.length })}</small>
        </div>)}</div> : <Empty title={t('dashboard.showSkills')} description={t('dashboard.addSkillsHint')}
          action={<Link className="button outline" to="/skills">{t('dashboard.addSkills')}</Link>} />}
      </section>

      <section className="panel dashboard-gaps" id="skill-gaps" aria-labelledby="skill-gaps-title">
        <div className="panel-heading"><h2 id="skill-gaps-title">{t('dashboard.gaps')}</h2><Link to="/recommendations">{t('dashboard.plan')} <ArrowUpRight size={16} /></Link></div>
        <p className="muted">{t('dashboard.gapsSample', { count: data.market_sample_size })}</p>
        {gaps.length ? <ol className="dashboard-gap-list">{gaps.slice(0, 4).map((gap, index) => <li key={gap.skill}>
          <span className="gap-rank">{index + 1}</span><div><strong>{gap.skill}</strong><p>{t('dashboard.learn')}</p></div>
          <Link className="icon-button" to="/skills" aria-label={t('dashboard.updateSkill', { skill: gap.skill })}><ArrowUpRight size={18} /></Link>
        </li>)}</ol> : <Empty title={hasMarket ? t('dashboard.noGaps') : t('dashboard.insufficient')}
          description={hasMarket ? t('dashboard.noGapsNote') : t('dashboard.insufficientHint')}
          action={<Link className="inline-link" to="/jobs">{t('dashboard.viewJobs')} <ArrowRight size={16} /></Link>} />}
      </section>
    </div>

    <section className="panel dashboard-next" aria-labelledby="career-actions-title">
      <div className="panel-heading"><div><span className="card-kicker"><Sparkles size={15} /> {t('dashboard.next')}</span><h2 id="career-actions-title">{t('dashboard.recommendations')}</h2></div><Link to="/recommendations">{t('common.careerPlan')} <ArrowRight size={17} /></Link></div>
      {recommendations.length ? <div className="dashboard-actions">{recommendations.map((item, index) => <article key={item.title}>
        <span className="action-number">0{index + 1}</span><h3>{item.title}</h3><p>{item.description}</p><Link className="inline-link" to={item.path}>{item.action} <ArrowRight size={16} /></Link>
      </article>)}</div> : <Empty title={t('dashboard.completeTitle')} description={t('dashboard.completeHint')}
        action={<Link className="button outline" to="/jobs">{t('dashboard.explore')}</Link>} />}
    </section>
  </div>;
}
