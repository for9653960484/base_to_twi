import { useTranslation } from 'react-i18next';

export function LoginPage() {
  const { t } = useTranslation();

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--color-bg)',
      }}
    >
      <form
        style={{
          background: 'var(--color-surface)',
          padding: '2rem',
          borderRadius: 'var(--radius)',
          boxShadow: 'var(--shadow)',
          width: '100%',
          maxWidth: '400px',
        }}
      >
        <h1 style={{ marginBottom: '0.5rem', fontSize: '1.5rem' }}>{t('app.title')}</h1>
        <p style={{ color: 'var(--color-text-muted)', marginBottom: '1.5rem' }}>{t('app.subtitle')}</p>
        <input
          type="email"
          placeholder="Email"
          style={{
            width: '100%',
            padding: '0.75rem',
            marginBottom: '1rem',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius)',
          }}
        />
        <input
          type="password"
          placeholder="Password"
          style={{
            width: '100%',
            padding: '0.75rem',
            marginBottom: '1.5rem',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius)',
          }}
        />
        <button
          type="submit"
          style={{
            width: '100%',
            padding: '0.75rem',
            background: 'var(--color-primary)',
            color: '#fff',
            border: 'none',
            borderRadius: 'var(--radius)',
            fontWeight: 600,
          }}
        >
          {t('common.save')}
        </button>
      </form>
    </div>
  );
}
