import { useTranslation } from 'react-i18next';
import { PageHeader } from '@/components/ui/PageHeader';

export function AdminPage() {
  const { t } = useTranslation();

  const sections = [
    'Пользователи и роли',
    'Специализации',
    'Настраиваемые поля',
    'HR-интеграция',
    'Брендбук',
    'Словари',
  ];

  return (
    <div>
      <PageHeader title={t('nav.admin')} />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
        {sections.map((section) => (
          <div
            key={section}
            style={{
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius)',
              padding: '1.25rem',
              cursor: 'pointer',
            }}
          >
            <h3 style={{ fontWeight: 600 }}>{section}</h3>
          </div>
        ))}
      </div>
    </div>
  );
}
