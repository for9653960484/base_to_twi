import { useTranslation } from 'react-i18next';
import i18n from '@/i18n';

export function Header() {
  const { t } = useTranslation();

  return (
    <header
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.75rem 1.5rem',
        background: 'var(--color-surface)',
        borderBottom: '1px solid var(--color-border)',
      }}
    >
      <input
        type="search"
        placeholder={t('common.search')}
        style={{
          padding: '0.5rem 1rem',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius)',
          width: '320px',
          maxWidth: '50vw',
        }}
      />
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <select
          value={i18n.language}
          onChange={(e) => i18n.changeLanguage(e.target.value)}
          style={{
            padding: '0.4rem 0.6rem',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius)',
          }}
        >
          <option value="ru">RU</option>
          <option value="en">EN</option>
        </select>
      </div>
    </header>
  );
}
