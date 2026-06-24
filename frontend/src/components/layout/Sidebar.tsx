import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import '@/styles/layout.css';

const navItems = [
  { to: '/equipment', key: 'equipment' },
  { to: '/documents', key: 'documents' },
  { to: '/tech-cards', key: 'techCards' },
  { to: '/instructions', key: 'instructions' },
  { to: '/courses', key: 'courses' },
  { to: '/competencies', key: 'competencies' },
  { to: '/knowledge', key: 'knowledge' },
  { to: '/admin', key: 'admin' },
] as const;

export function Sidebar() {
  const { t } = useTranslation();

  return (
    <aside
      style={{
        width: 'var(--sidebar-width)',
        background: 'var(--color-surface)',
        borderRight: '1px solid var(--color-border)',
        padding: '1rem 0',
        flexShrink: 0,
      }}
    >
      <div style={{ padding: '0 1.25rem 1.5rem' }}>
        <h1 style={{ fontSize: '1.25rem', fontWeight: 700 }}>{t('app.title')}</h1>
        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{t('app.subtitle')}</p>
      </div>
      <nav>
        {navItems.map(({ to, key }) => (
          <NavLink
            key={to}
            to={to}
            style={({ isActive }) => ({
              display: 'block',
              padding: '0.6rem 1.25rem',
              fontSize: '0.9rem',
              color: isActive ? 'var(--color-primary)' : 'var(--color-text)',
              background: isActive ? '#eff6ff' : 'transparent',
              borderRight: isActive ? '3px solid var(--color-primary)' : '3px solid transparent',
              fontWeight: isActive ? 600 : 400,
            })}
          >
            {t(`nav.${key}`)}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
