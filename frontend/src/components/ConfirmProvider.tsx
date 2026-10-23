import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { useI18n } from '../i18n';
import Modal from './Modal';

type Request = { name: string; resolve: (confirmed: boolean) => void };
const ConfirmContext = createContext<((name: string) => Promise<boolean>) | null>(null);
export function ConfirmProvider({ children }: { children: ReactNode }) {
  const { t } = useI18n();
  const [request, setRequest] = useState<Request | null>(null);
  const pending = useRef<Request | null>(null);
  const confirm = useCallback((name: string) => new Promise<boolean>(resolve => {
    pending.current?.resolve(false);
    const next = { name, resolve };
    pending.current = next; setRequest(next);
  }), []);
  useEffect(() => () => { pending.current?.resolve(false); }, []);
  function finish(value: boolean) { pending.current?.resolve(value); pending.current = null; setRequest(null); }
  return <ConfirmContext.Provider value={confirm}>{children}{request && <Modal title={t('common.confirmTitle')} close={() => finish(false)}>
    <p>{t('common.confirmDelete', { name: request.name })}</p><div className="form-actions">
      <button className="button outline" onClick={() => finish(false)} autoFocus>{t('common.cancel')}</button>
      <button className="button primary" onClick={() => finish(true)}>{t('common.delete')}</button>
    </div>
  </Modal>}</ConfirmContext.Provider>;
}
export function useConfirm() {
  const context = useContext(ConfirmContext);
  if (!context) throw new Error('ConfirmProvider is required');
  return context;
}
