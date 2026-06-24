import { useTranslation } from 'react-i18next';
import { PageHeader } from '@/components/ui/PageHeader';

export function CoursesPage() {
  const { t } = useTranslation();

  return (
    <div>
      <PageHeader title={t('nav.courses')} />
      <p style={{ color: 'var(--color-text-muted)' }}>
        Конструктор и просмотр TWI-курсов, назначение сотрудникам, статусы прохождения.
      </p>
    </div>
  );
}
