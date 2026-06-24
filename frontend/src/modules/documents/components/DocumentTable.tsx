import type { CSSProperties } from 'react';
import { useTranslation } from 'react-i18next';
import { documentsApi } from '@/api/documents';
import type { Document } from '@/types';
import { StatusBadge } from '@/components/ui/StatusBadge';

interface Props {
  items: Document[];
  onAction: (action: string, id: string, force?: boolean) => void;
  actionLoading?: boolean;
}

function formatSize(bytes?: number): string {
  if (!bytes) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function DocumentTable({ items, onAction, actionLoading }: Props) {
  const { t } = useTranslation();

  if (items.length === 0) {
    return <div style={emptyStyle}>{t('common.noData')}</div>;
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', background: 'var(--color-surface)' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid var(--color-border)', textAlign: 'left' }}>
            <th style={thStyle}>{t('documents.colTitle')}</th>
            <th style={thStyle}>{t('documents.colEquipment')}</th>
            <th style={thStyle}>{t('documents.colSize')}</th>
            <th style={thStyle}>{t('documents.colStatus')}</th>
            <th style={thStyle}>{t('documents.colAi')}</th>
            <th style={thStyle}>{t('documents.colVersion')}</th>
            <th style={thStyle}></th>
          </tr>
        </thead>
        <tbody>
          {items.map((doc) => (
            <tr key={doc.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
              <td style={tdStyle}>
                <strong>{doc.title}</strong>
                {doc.description && (
                  <div style={muted}>{doc.description}</div>
                )}
              </td>
              <td style={tdStyle}>{doc.equipment_name || doc.equipment_id.slice(0, 8)}</td>
              <td style={tdStyle}>{formatSize(doc.file_size)}</td>
              <td style={tdStyle}>
                <StatusBadge status={doc.status} />
              </td>
              <td style={tdStyle}>
                <StatusBadge status={doc.ai_processing_status} />
              </td>
              <td style={tdStyle}>v{doc.current_version_number ?? 1}</td>
              <td style={tdStyle}>
                <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                  <a href={documentsApi.downloadUrl(doc.id)} style={linkBtn} target="_blank" rel="noreferrer">
                    {t('documents.download')}
                  </a>
                  {doc.status === 'draft' && (
                    <button
                      style={actionBtn}
                      disabled={actionLoading}
                      onClick={() => onAction('submit', doc.id)}
                    >
                      {t('common.submit')}
                    </button>
                  )}
                  {doc.status === 'pending_approval' && (
                    <button
                      style={actionBtn}
                      disabled={actionLoading}
                      onClick={() => onAction('approve', doc.id)}
                    >
                      {t('common.approve')}
                    </button>
                  )}
                  {(doc.ai_processing_status === 'pending' ||
                    doc.ai_processing_status === 'failed') && (
                    <button
                      style={actionBtn}
                      disabled={actionLoading}
                      onClick={() => onAction('ai', doc.id, doc.ai_processing_status === 'failed')}
                    >
                      {doc.ai_processing_status === 'failed'
                        ? t('documents.aiRetry')
                        : t('documents.aiProcess')}
                    </button>
                  )}
                  {doc.ai_processing_status === 'processing' && (
                    <span style={processingLabel}>{t('documents.aiProcessing')}</span>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const thStyle: CSSProperties = {
  padding: '0.75rem 1rem',
  fontSize: '0.85rem',
  color: 'var(--color-text-muted)',
  fontWeight: 600,
};

const tdStyle: CSSProperties = { padding: '0.75rem 1rem', verticalAlign: 'top' };

const muted: CSSProperties = {
  fontSize: '0.85rem',
  color: 'var(--color-text-muted)',
  marginTop: '0.2rem',
};

const emptyStyle: CSSProperties = {
  background: 'var(--color-surface)',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius)',
  padding: '2rem',
  textAlign: 'center',
  color: 'var(--color-text-muted)',
};

const actionBtn: CSSProperties = {
  padding: '0.3rem 0.6rem',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius)',
  background: 'transparent',
  fontSize: '0.8rem',
};

const linkBtn: CSSProperties = {
  ...actionBtn,
  display: 'inline-block',
  textDecoration: 'none',
  color: 'var(--color-primary)',
};

const processingLabel: CSSProperties = {
  fontSize: '0.8rem',
  color: 'var(--color-info)',
  fontStyle: 'italic',
};
