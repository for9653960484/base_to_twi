import { techCardsApi } from '@/api/tech-cards';
import type { TechCard } from '@/types';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useTranslation } from 'react-i18next';
import type { CSSProperties } from 'react';

interface Props {
  items: TechCard[];
}

export function TechCardList({ items }: Props) {
  const { t } = useTranslation();

  if (items.length === 0) {
    return <div style={emptyStyle}>{t('techCards.noCards')}</div>;
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={tableStyle}>
        <thead>
          <tr style={{ borderBottom: '2px solid var(--color-border)', textAlign: 'left' }}>
            <th style={thStyle}>{t('techCards.colTitle')}</th>
            <th style={thStyle}>{t('techCards.colStatus')}</th>
            <th style={thStyle}></th>
          </tr>
        </thead>
        <tbody>
          {items.map((card) => (
            <tr key={card.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
              <td style={tdStyle}>
                <strong>{card.title}</strong>
              </td>
              <td style={tdStyle}>
                <StatusBadge status={card.status} />
              </td>
              <td style={tdStyle}>
                {card.status === 'published' ? (
                  <a
                    href={techCardsApi.exportPdfUrl(card.id)}
                    style={linkBtn}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {t('techCards.exportPdf')}
                  </a>
                ) : (
                  <span style={mutedBtn}>{t('techCards.exportPdf')}</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const tableStyle: CSSProperties = {
  width: '100%',
  borderCollapse: 'collapse',
  background: 'var(--color-surface)',
};

const thStyle: CSSProperties = {
  padding: '0.75rem',
  fontSize: '0.875rem',
  color: 'var(--color-text-muted)',
};

const tdStyle: CSSProperties = { padding: '0.75rem', verticalAlign: 'middle' };

const linkBtn: CSSProperties = {
  fontSize: '0.875rem',
  color: 'var(--color-primary)',
  textDecoration: 'none',
};

const mutedBtn: CSSProperties = {
  fontSize: '0.875rem',
  color: 'var(--color-text-muted)',
};

const emptyStyle: CSSProperties = {
  padding: '2rem',
  textAlign: 'center',
  color: 'var(--color-text-muted)',
};
