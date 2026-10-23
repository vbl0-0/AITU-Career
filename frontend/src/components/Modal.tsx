import { useI18n } from '../i18n';
import { useEffect, useId, useRef, type ReactNode } from 'react';
import { X } from 'lucide-react';
import LanguageSwitcher from './LanguageSwitcher';

export default function Modal({ title, children, close }: { title: string; children: ReactNode; close: () => void }) {
  const { t } = useI18n();
  const headingId = useId();
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => { ref.current?.showModal(); }, []);
  return <dialog aria-labelledby={headingId} className="modal" ref={ref} onCancel={event => { event.preventDefault(); close(); }}><div className="modal-heading"><h2 id={headingId}>{title}</h2><div className="modal-controls"><LanguageSwitcher /><button type="button" className="icon-button" onClick={close} aria-label={t('common.close')}><X size={20} /></button></div></div>{children}</dialog>;
}
