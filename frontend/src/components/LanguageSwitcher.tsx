import { Globe2 } from 'lucide-react';
import { languages, useI18n } from '../i18n';

export default function LanguageSwitcher() {
  const { t, i18n } = useI18n();
  return <label className="language-switcher"><Globe2 size={17} aria-hidden="true" /><span className="sr-only">{t('language.select')}</span>
    <select value={i18n.resolvedLanguage || 'en'} onChange={event => void i18n.changeLanguage(event.target.value)}>
      {languages.map(language => <option value={language.code} lang={language.code} key={language.code}>{language.name}</option>)}
    </select>
  </label>;
}
