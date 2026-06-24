import { useTranslation } from 'react-i18next';
import { PageHeader } from '@/components/ui/PageHeader';

export function CompetenciesPage() {
  const { t } = useTranslation();

  return (
    <div>
      <PageHeader title={t('nav.competencies')} />
      <p style={{ color: 'var(--color-text-muted)' }}>
        Матрица компетенций: фильтры по оборудованию и подразделениям, отчёты о дефиците навыков.
      </p>
    </div>
  );
}
