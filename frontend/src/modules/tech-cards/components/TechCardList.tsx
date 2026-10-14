import { techCardsApi } from '@/api/tech-cards';
import type { TechCard } from '@/types';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useQueryClient } from '@tanstack/react-query';
import { useRef, useState, type CSSProperties } from 'react';
import { useTranslation } from 'react-i18next';

interface Props {
  items: TechCard[];
  equipmentId?: string;
}

export function TechCardList({ items, equipmentId }: Props) {
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
                <CardActions card={card} equipmentId={equipmentId} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CardActions({ card, equipmentId }: { card: TechCard; equipmentId?: string }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  function refresh() {
    queryClient.invalidateQueries({ queryKey: ['tech-cards', equipmentId] });
  }

  async function upload(file: File) {
    setBusy(true);
    setError('');
    try {
      await techCardsApi.uploadEdited(card.id, file);
      refresh();
    } catch {
      setError(t('techCards.uploadError'));
    } finally {
      setBusy(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  }

  async function formPdf() {
    setBusy(true);
    setError('');
    try {
      const response = await techCardsApi.formPdf(card.id);
      const url = URL.createObjectURL(response.data);
      window.open(url, '_blank');
      refresh();
    } catch {
      setError(t('techCards.formPdfError'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={actionsStyle}>
      <a href={techCardsApi.exportDocxUrl(card.id)} style={linkBtn}>
        {t('techCards.exportDoc')}
      </a>
      <button type="button" style={textBtn} disabled={busy} onClick={() => fileRef.current?.click()}>
        {t('techCards.uploadEdited')}
      </button>
      <input
        ref={fileRef}
        type="file"
        accept=".doc,.docx,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        hidden
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) void upload(file);
        }}
      />
      {card.status === 'approved' ? (
        <a
          href={techCardsApi.exportPdfUrl(card.id)}
          style={linkBtn}
          target="_blank"
          rel="noreferrer"
        >
          {t('techCards.exportPdf')}
        </a>
      ) : (
        <button type="button" style={textBtn} disabled={busy} onClick={() => void formPdf()}>
          {t('techCards.formPdf')}
        </button>
      )}
      {error && <span style={errorStyle}>{error}</span>}
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

const actionsStyle: CSSProperties = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: '0.75rem',
  alignItems: 'center',
};

const linkBtn: CSSProperties = {
  fontSize: '0.875rem',
  color: 'var(--color-primary)',
  textDecoration: 'none',
};

const textBtn: CSSProperties = {
  fontSize: '0.875rem',
  color: 'var(--color-primary)',
  background: 'none',
  border: 'none',
  padding: 0,
  cursor: 'pointer',
};

const errorStyle: CSSProperties = { color: 'var(--color-danger)', fontSize: '0.75rem' };

const emptyStyle: CSSProperties = {
  padding: '2rem',
  textAlign: 'center',
  color: 'var(--color-text-muted)',
};
