import { useEffect } from 'react';
import { useI18n } from '../i18n';

type Control = HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;
export default function LocalizedForms() {
  const { t, i18n } = useI18n();
  useEffect(() => {
    function localize(control: Control) {
      control.setCustomValidity('');
      const validity = control.validity;
      let message = '';
      if (validity.valueMissing) message = t('validation.required');
      else if (validity.typeMismatch) message = t(control instanceof HTMLInputElement && control.type === 'email' ? 'validation.email' : 'validation.url');
      else if (validity.tooShort) message = t('validation.minLength', { count: (control as HTMLInputElement).minLength });
      else if (validity.tooLong) message = t('validation.maxLength', { count: (control as HTMLInputElement).maxLength });
      else if (validity.rangeUnderflow) message = t('validation.min', { value: (control as HTMLInputElement).min });
      else if (validity.rangeOverflow) message = t('validation.max', { value: (control as HTMLInputElement).max });
      else if (!validity.valid) message = t('validation.pattern');
      control.setCustomValidity(message);
    }
    function isControl(target: EventTarget | null): target is Control { return target instanceof HTMLInputElement || target instanceof HTMLSelectElement || target instanceof HTMLTextAreaElement; }
    const invalid = (event: Event) => { if (isControl(event.target)) localize(event.target); };
    const input = (event: Event) => { if (isControl(event.target)) event.target.setCustomValidity(''); };
    document.querySelectorAll<Control>('input, select, textarea').forEach(control => { if (control.validity.customError) localize(control); });
    document.addEventListener('invalid', invalid, true);
    document.addEventListener('input', input, true);
    document.addEventListener('change', input, true);
    return () => { document.removeEventListener('invalid', invalid, true); document.removeEventListener('input', input, true); document.removeEventListener('change', input, true); };
  }, [t, i18n.resolvedLanguage]);
  return null;
}
