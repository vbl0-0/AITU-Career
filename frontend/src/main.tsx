import { useI18n } from './i18n';
import { Component, useEffect, type ReactNode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Link, Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/Auth';
import Layout from './components/Layout';
import { Empty, Loading } from './components/UI';
import Landing from './pages/Landing';
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';
import Profile from './pages/Profile';
import Portfolio from './pages/Portfolio';
import Jobs from './pages/Jobs';
import JobDetail from './pages/JobDetail';
import Analysis from './pages/Analysis';
import Career from './pages/Career';
import Admin from './pages/Admin';
import LanguageSwitcher from './components/LanguageSwitcher';
import LocalizedForms from './components/LocalizedForms';
import { ConfirmProvider } from './components/ConfirmProvider';
import './styles.css';

class ErrorBoundary extends Component<{ children: ReactNode }, { error: boolean }> {
  state = { error: false };
  static getDerivedStateFromError() { return { error: true }; }
  render() { return this.state.error ? <ErrorFallback /> : this.props.children; }
}

function ErrorFallback() {
  const { t } = useI18n();
  return <div className="standalone-state"><LanguageSwitcher /><Empty title={t('errors.page')} description={t('errors.reloadHint')} action={<button className="button primary" onClick={() => window.location.reload()}>{t('errors.reload')}</button>} /></div>;
}

function NotFound() {
  const { t } = useI18n();
  return <div className="standalone-state"><LanguageSwitcher /><Empty title={t('errors.notFound')} action={<Link className="button primary" to="/dashboard">{t('errors.goDashboard')}</Link>} /></div>;
}

function Protected({ admin = false }: { admin?: boolean }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <Loading />;
  if (!user) return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  if (admin && user.role !== 'admin') return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}

function App() {
  const { loading } = useAuth();
  const location = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [location.pathname]);
  if (loading) return <Loading />;
  return <Routes><Route path="/" element={<Landing />} /><Route path="/login" element={<AuthPage />} /><Route path="/register" element={<AuthPage register />} /><Route element={<Protected />}><Route element={<Layout />}><Route path="/dashboard" element={<Dashboard />} /><Route path="/profile" element={<Profile />} />{(['skills', 'projects', 'certificates', 'experience'] as const).map(kind => <Route path={'/' + kind} key={kind} element={<Portfolio key={kind} kind={kind} />} />)}<Route path="/jobs" element={<Jobs />} /><Route path="/jobs/:id" element={<JobDetail />} /><Route path="/saved" element={<Jobs saved />} /><Route path="/matches/:id" element={<Analysis />} /><Route path="/recommendations" element={<Career />} /><Route element={<Protected admin />}><Route path="/admin" element={<Admin />} /></Route></Route></Route><Route path="*" element={<NotFound />} /></Routes>;
}

createRoot(document.getElementById('root')!).render(<ErrorBoundary><BrowserRouter><AuthProvider><ConfirmProvider><LocalizedForms /><App /></ConfirmProvider></AuthProvider></BrowserRouter></ErrorBoundary>);
