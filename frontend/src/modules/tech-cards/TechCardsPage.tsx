import { useTranslation } from 'react-i18next';
import { PageHeader } from '@/components/ui/PageHeader';

export function TechCardsPage() {
  const { t } = useTranslation();

  return (
    <div>
      <PageHeader title={t('nav.techCards')} />
      <p style={{ color: 'var(--color-text-muted)' }}>
        Технологические карты по видам ТО: годовое, полугодовое, квартальное, месячное, недельное, ежедневное.
      </p>
    </div>
  );
}
