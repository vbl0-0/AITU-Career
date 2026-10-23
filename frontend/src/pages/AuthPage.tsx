import { useI18n } from '../i18n';
import { useState, type FormEvent } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { ArrowRight, Check, Sparkles } from 'lucide-react';
import { Brand } from '../components/Layout';
import { ErrorBox, Field } from '../components/UI';
import { useAuth } from '../hooks/Auth';
import { api } from '../services/api';
import LanguageSwitcher from '../components/LanguageSwitcher';

export default function AuthPage({ register = false }: { register?: boolean }) {
  const { t } = useI18n();
  const { user, authenticate } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  if (user) return <Navigate to="/dashboard" replace />;
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setBusy(true);
    const values = Object.fromEntries(new FormData(event.currentTarget));
    try { const data = await api(register ? '/auth/register' : '/auth/login', { method: 'POST', body: values }); authenticate(data); navigate(location.state?.from || '/dashboard', { replace: true }); }
    catch (err: any) { setError(err.message); } finally { setBusy(false); }
  }
  return <div className="auth-page"><aside className="auth-story"><Brand light /><div><span className="pill dark"><Sparkles size={14} /> AITU CAREER</span><h1>{t('auth.chapter')}<br />{t('auth.starts')}<br /><em>{t('auth.withYou')}</em></h1><p>{t('auth.promise')}</p><ul>{[t('auth.competencies'), t('auth.explainable'), t('auth.plan')].map(text => <li key={text}><Check size={17} />{text}</li>)}</ul></div><span className="auth-story-footer">{t('auth.support')}</span></aside><main className="auth-main"><div className="auth-toolbar"><Link to="/" className="back-link">{t('auth.home')}</Link><LanguageSwitcher /></div><div className="auth-form"><p className="eyebrow">{t('auth.eyebrow')}</p><h1>{register ? t('auth.createTitle') : t('auth.welcome')}</h1><p className="muted">{register ? t('auth.createDescription') : t('auth.loginDescription')}</p>{error && <ErrorBox message={error} />}<form onSubmit={submit}>{register && <Field label={t('common.fullName')}><input name="name" autoComplete="name" placeholder={t('auth.namePlaceholder')} required minLength={2} maxLength={150} /></Field>}<Field label={t('common.email')}><input type="email" name="email" placeholder="you@aitu.edu.kz" autoComplete="email" required maxLength={254} /></Field><Field label={t('auth.password')}><input type="password" name="password" autoComplete={register ? 'new-password' : 'current-password'} required minLength={register ? 10 : 1} maxLength={128} placeholder={register ? t('auth.passwordHint') : t('auth.passwordPlaceholder')} /></Field><button disabled={busy} className="button primary full" type="submit">{busy ? t('auth.wait') : register ? t('auth.register') : t('auth.login')}<ArrowRight size={18} /></button></form><p className="auth-switch">{register ? t('auth.haveAccount') : t('auth.noAccount')} <Link to={register ? '/login' : '/register'}>{register ? t('auth.login') : t('auth.signUp')}</Link></p>{!register && <div className="demo-hint"><strong>{t('auth.demo')}</strong><p>student.demo@aitu.edu.kz</p><small>{t('auth.demoHint')}</small></div>}</div></main></div>;
}
