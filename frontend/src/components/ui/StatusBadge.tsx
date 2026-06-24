import clsx from 'clsx';
import { useTranslation } from 'react-i18next';
import '@/styles/components.css';

type ContentStatus =
  | 'draft'
  | 'pending_approval'
  | 'published'
  | 'archived'
  | 'assigned'
  | 'in_progress'
  | 'completed'
  | 'failed'
  | 'pending'
  | 'processing';

interface StatusBadgeProps {
  status: ContentStatus | string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const { t } = useTranslation();

  return (
    <span className={clsx('status-badge', `status-badge--${status}`)}>
      {t(`status.${status}`, status)}
    </span>
  );
}
