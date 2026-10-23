import { useI18n } from '../i18n';
import { useEffect, useRef, useState } from 'react';
import { NavLink, Outlet, Link, useLocation } from 'react-router-dom';
import { ArrowUpRight, LayoutDashboard, UserRound, Layers, FolderGit2, Award, BriefcaseBusiness, Search, Sparkles, Bookmark, ShieldCheck, LogOut, Menu, X, GraduationCap } from 'lucide-react';
import { useAuth } from '../hooks/Auth';
import LanguageSwitcher from './LanguageSwitcher';



export function Brand({ light = false }: { light?: boolean }) { return <Link to="/" className={`brand ${light ? 'light' : ''}`}><span className="brand-symbol"><GraduationCap size={23} /></span><span>AITU<span className="brand-thin"> Career</span><small>ASTANA IT UNIVERSITY</small></span></Link>; }

export default function Layout() {
  const { t, message: translateMessage } = useI18n();
  const navigation = [
  { label: t('nav.workspace'), items: [['/dashboard', t('nav.overview'), LayoutDashboard]] },
  { label: t('nav.portfolio'), items: [
    ['/profile', t('common.profile'), UserRound], ['/skills', t('common.skills'), Layers], ['/projects', t('common.projects'), FolderGit2],
    ['/certificates', t('common.certificates'), Award], ['/experience', t('common.experience'), BriefcaseBusiness],
  ] },
  { label: t('nav.career'), items: [
    ['/jobs', t('common.jobs'), Search], ['/saved', t('nav.saved'), Bookmark], ['/recommendations', t('common.careerPlan'), Sparkles],
  ] },
] as const;

  const { user, logout } = useAuth();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [mobile, setMobile] = useState(() => window.matchMedia('(max-width: 760px)').matches);
  const [error, setError] = useState('');
  const sidebar = useRef<HTMLElement>(null);
  const menuButton = useRef<HTMLButtonElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  const drawerOpen = mobile && open;

  useEffect(() => {
    const media = window.matchMedia('(max-width: 760px)');
    const change = () => { setMobile(media.matches); if (!media.matches) setOpen(false); };
    media.addEventListener('change', change);
    return () => media.removeEventListener('change', change);
  }, []);
  useEffect(() => { setOpen(false); }, [location.pathname]);
  useEffect(() => {
    if (!drawerOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    closeButton.current?.focus();
    function keydown(event: KeyboardEvent) {
      if (event.key === 'Escape') { event.preventDefault(); setOpen(false); }
      if (event.key !== 'Tab') return;
      const items = sidebar.current?.querySelectorAll<HTMLElement>('a[href], button:not([disabled])');
      if (!items?.length) return;
      const first = items[0], last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
    document.addEventListener('keydown', keydown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener('keydown', keydown);
      menuButton.current?.focus();
    };
  }, [drawerOpen]);

  async function signout() { try { await logout(); } catch (err: any) { setError(err.message); } }
  const navClass = ({ isActive }: { isActive: boolean }) => isActive ? 'nav-link active' : 'nav-link';
  return <div className="app-shell">
    <a className="skip-link" href="#main-content">{t('nav.skip')}</a>
    {drawerOpen && <button className="sidebar-overlay" tabIndex={-1} aria-label={t('nav.closeMenu')} onClick={() => setOpen(false)} />}
    <aside id="career-navigation" ref={sidebar} className={`sidebar ${drawerOpen ? 'open' : ''}`}
      role={drawerOpen ? 'dialog' : undefined} aria-modal={drawerOpen || undefined} aria-label={t('nav.navigation')} inert={mobile && !drawerOpen}>
      <div className="sidebar-brand"><Brand light /><button ref={closeButton} className="mobile-close icon-button" onClick={() => setOpen(false)} aria-label={t('nav.closeMenu')}><X size={21} /></button></div>
      <nav aria-label={t('nav.mainNavigation')}>
        {navigation.map(group => <div className="nav-group" key={group.label}><p className="workspace-label">{group.label}</p>
          {group.items.map(([path, label, Icon]) => <NavLink key={path} to={path} onClick={() => setOpen(false)} className={navClass}><Icon size={18} />{label}</NavLink>)}
        </div>)}
        {user?.role === 'admin' && <div className="nav-group"><p className="workspace-label">{t('nav.management')}</p><NavLink to="/admin" onClick={() => setOpen(false)} className={navClass}><ShieldCheck size={18} />{t('common.admin')}</NavLink></div>}
      </nav>
      <div className="sidebar-shortcut"><Sparkles size={18} /><Link to="/recommendations" onClick={() => setOpen(false)}>{t('nav.nextStep')} <ArrowUpRight size={15} /></Link></div>
      <div className="sidebar-footer"><span className="status-dot" /> {t('nav.support')}</div>
    </aside>
    <div className="main-shell" inert={drawerOpen}>
      <header className="topbar"><div className="topbar-left"><button ref={menuButton} className="mobile-menu icon-button" aria-label={t('nav.openMenu')} aria-expanded={drawerOpen} aria-controls="career-navigation" onClick={() => setOpen(true)}><Menu size={21} /></button><span className="breadcrumb">{t('nav.path')} <span>/</span> AITU Career</span></div>
        <div className="user-menu"><LanguageSwitcher /><span className="avatar">{user?.name?.slice(0, 1).toUpperCase()}</span><div><strong>{user?.name}</strong><small>{user?.role === 'admin' ? t('common.administrator') : t('nav.graduate')}</small></div><button className="icon-button" aria-label={t('nav.logout')} onClick={signout}><LogOut size={18} /></button></div>
      </header>
      {error && <div role="alert" className="error">{translateMessage(error)}</div>}
      <main id="main-content" className="page-content" tabIndex={-1}><Outlet /></main>
      <footer className="main-footer"><span>{t('nav.footer')}</span><span>{t('nav.madeFor')}</span></footer>
    </div>
  </div>;
}
