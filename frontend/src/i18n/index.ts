import i18n from 'i18next';
import { initReactI18next, useTranslation } from 'react-i18next';
import kk from './locales/kk/translation.json';
import ru from './locales/ru/translation.json';
import en from './locales/en/translation.json';

export const languageStorageKey = 'aitu-career.language';
export const languages = [{ code: 'kk', name: 'Қазақша' }, { code: 'ru', name: 'Русский' }, { code: 'en', name: 'English' }] as const;
export type Language = typeof languages[number]['code'];
function supported(value: string | null): Language | undefined {
  const code = value?.toLowerCase().split('-')[0];
  return languages.find(language => language.code === code)?.code;
}
function initialLanguage(): Language {
  try { const saved = supported(localStorage.getItem(languageStorageKey)); if (saved) return saved; } catch { /* Storage may be unavailable in private browsers. */ }
  for (const value of navigator.languages || [navigator.language]) { const language = supported(value); if (language) return language; }
  return 'en';
}
void i18n.use(initReactI18next).init({
  resources: { kk: { translation: kk }, ru: { translation: ru }, en: { translation: en } },
  lng: initialLanguage(), fallbackLng: 'en', supportedLngs: ['kk', 'ru', 'en'],
  interpolation: { escapeValue: false }, keySeparator: false, returnNull: false, initAsync: false,
});
function applyLanguage(language: string) {
  document.documentElement.lang = supported(language) || 'en';
  document.title = i18n.t('meta.title');
  document.querySelector('meta[name="description"]')?.setAttribute('content', i18n.t('meta.description'));
}
i18n.on('languageChanged', language => {
  applyLanguage(language);
  try { localStorage.setItem(languageStorageKey, language); } catch { /* Language switching still works without persistence. */ }
});
applyLanguage(i18n.language);
window.addEventListener('storage', event => {
  if (event.key === languageStorageKey) { const language = supported(event.newValue); if (language) void i18n.changeLanguage(language); }
});

const backendMessages: Record<string, string> = {
  'Invalid email or password': 'errors.credentials', 'Email is already registered': 'errors.emailRegistered',
  'No refresh session': 'errors.sessionExpired', 'Session expired': 'errors.sessionExpired',
  'Account unavailable': 'errors.unavailable', 'Authentication required': 'errors.signIn',
  'Administrator access required': 'errors.adminRequired', 'Origin not allowed': 'errors.origin',
  'Match not found': 'errors.itemNotFound', 'Item not found': 'errors.itemNotFound',
  'Duplicate skills': 'errors.duplicateSkills', 'Unknown skill': 'errors.unknownSkill',
  'Duplicate value or item is in use': 'errors.duplicateInUse',
  'Aliases must be distinct from the skill name and each other': 'errors.aliasDistinct',
  'Skill name or alias conflicts with another skill': 'errors.aliasConflict', 'Name is already in use': 'errors.nameInUse',
  'You cannot disable or demote your own admin account': 'errors.selfDemote', 'You cannot delete your own admin account': 'errors.selfDelete',
  'Certificate issue date cannot be in the future': 'validation.certificateFuture', 'Start date cannot be in the future': 'validation.startFuture',
  'End date must be between start date and today': 'validation.endDate', 'Provide an http(s) URL': 'validation.url',
  'Maximum salary cannot be below minimum': 'validation.salary', 'Requirements must be unique': 'validation.uniqueRequirements',
};
const enumKeys: Record<string, string> = {
  'Full-time': 'enum.fullTime', 'Part-time': 'enum.partTime', Internship: 'enum.internship', Freelance: 'enum.freelance',
  Academic: 'enum.academic', Personal: 'enum.personal', Commercial: 'enum.commercial', 'Open source': 'enum.openSource', Remote: 'enum.remote',
};
const improvements: Record<string, { key: string; path: string }> = {
  'Выбери карьерное направление.': { key: 'career.selectDirection', path: '/profile' },
  'Добавь образование AITU.': { key: 'career.addEducation', path: '/profile' },
  'Добавь навыки с текущими уровнями.': { key: 'career.addSkills', path: '/skills' },
  'Добавь проект и его технологии.': { key: 'career.addProject', path: '/projects' },
  'Select your target career direction.': { key: 'career.selectDirection', path: '/profile' },
  'Add your AITU education.': { key: 'career.addEducation', path: '/profile' },
  'Add skills with honest proficiency levels.': { key: 'career.addSkills', path: '/skills' },
  'Add a project with its technologies.': { key: 'career.addProject', path: '/projects' },
};
export function profileAction(text: string) { return improvements[text] || { key: text, path: '/profile' }; }
export function validationError(details: unknown) { return '@validation:' + JSON.stringify(details); }

export function useI18n() {
  const { t, i18n: instance } = useTranslation();
  const locale = ({ kk: 'kk-KZ', ru: 'ru-RU', en: 'en-GB' } as Record<string, string>)[instance.resolvedLanguage || 'en'] || 'en-GB';
  const number = (value: number, options?: Intl.NumberFormatOptions) => new Intl.NumberFormat(locale, options).format(value);
  const date = (value: string | number | Date, time = false) => {
    const parsed = typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value) ? new Date(value + 'T00:00:00') : new Date(value);
    // Numeric Kazakh dates avoid incomplete month names in browsers with reduced ICU data.
    const options: Intl.DateTimeFormatOptions = locale === 'kk-KZ'
      ? { year: 'numeric', month: '2-digit', day: '2-digit', ...(time ? { hour: '2-digit', minute: '2-digit' } : {}) }
      : { dateStyle: 'medium', ...(time ? { timeStyle: 'short' as const } : {}) };
    return Number.isNaN(parsed.getTime()) ? String(value) : new Intl.DateTimeFormat(locale, options).format(parsed);
  };
  const enumLabel = (value: string) => enumKeys[value] ? t(enumKeys[value]) : value;
  const sourceLabel = (value: string) => {
    if (value === 'Заявленный навык' || value === 'Declared skill') return t('source.declared');
    for (const [prefix, key] of [['Описание проекта: ', 'source.projectDescription'], ['Проект: ', 'source.project'], ['Опыт: ', 'source.experience'], ['Сертификат: ', 'source.certificate']]) {
      if (value.startsWith(prefix)) return t(key, { name: value.slice(prefix.length) });
    }
    return value;
  };
  const message = (raw: string): string => {
    if (raw.startsWith('@validation:')) {
      try {
        const details = JSON.parse(raw.slice(12)) as { type: string; msg: string; ctx?: Record<string, unknown> }[];
        return details.map(detail => {
          const text = detail.msg.replace(/^Value error, /, '');
          if (backendMessages[text]) return t(backendMessages[text]);
          const values = detail.ctx || {};
          if (detail.type === 'missing') return t('validation.required');
          if (detail.type === 'string_too_short') return t('validation.minLength', { count: Number(values.min_length) });
          if (detail.type === 'string_too_long') return t('validation.maxLength', { count: Number(values.max_length) });
          if (/email/i.test(text)) return t('validation.email');
          if (detail.type.startsWith('greater_than')) return t('validation.min', { value: values.ge ?? values.gt });
          if (detail.type.startsWith('less_than')) return t('validation.max', { value: values.le ?? values.lt });
          return t('validation.invalid');
        }).join(' ');
      } catch { return t('validation.invalid'); }
    }
    if (backendMessages[raw]) return t(backendMessages[raw]);
    if (/^\w+ not found$/.test(raw)) return t('errors.itemNotFound');
    return instance.exists(raw) ? t(raw) : raw;
  };
  const list = (items: string[]) => new Intl.ListFormat(locale, { style: 'long', type: 'conjunction' }).format(items);
  const matchExplanation = (match: any) => {
    if (match.score === null) return t('match.noRequirements');
    const gaps = [...match.missing, ...match.partial];
    if (!gaps.length) return t('match.fullCoverage');
    return t('match.gapsExplanation', { matched: number(match.matched.length), total: number(match.matched.length + gaps.length), skills: list(gaps.sort((a, b) => b.weight - a.weight).slice(0, 3).map(skill => skill.name)) });
  };
  return { t, i18n: instance, locale, number, date, enumLabel, sourceLabel, message, list, matchExplanation };
}

export default i18n;
