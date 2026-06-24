import type { CSSProperties } from 'react';
import { useTranslation } from 'react-i18next';
import type { Equipment } from '@/types';

interface Props {
  items: Equipment[];
  onEdit: (item: Equipment) => void;
}

export function EquipmentTable({ items, onEdit }: Props) {
  const { t } = useTranslation();

  if (items.length === 0) {
    return (
      <div style={emptyStyle}>
        {t('common.noData')}
      </div>
    );
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', background: 'var(--color-surface)' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid var(--color-border)', textAlign: 'left' }}>
            <th style={thStyle}>{t('equipment.name')}</th>
            <th style={thStyle}>{t('equipment.serialName')}</th>
            <th style={thStyle}>{t('equipment.status')}</th>
            <th style={thStyle}></th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
              <td style={tdStyle}>
                <strong>{item.name}</strong>
                {item.description && (
                  <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginTop: '0.2rem' }}>
                    {item.description}
                  </div>
                )}
              </td>
              <td style={tdStyle}>{item.serial_name || '—'}</td>
              <td style={tdStyle}>
                <span style={item.is_active ? activeStyle : inactiveStyle}>
                  {item.is_active ? t('equipment.active') : t('equipment.inactive')}
                </span>
              </td>
              <td style={tdStyle}>
                <button onClick={() => onEdit(item)} style={editBtn}>
                  {t('common.edit')}
                </button>
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

const tdStyle: CSSProperties = {
  padding: '0.75rem 1rem',
  verticalAlign: 'top',
};

const editBtn: CSSProperties = {
  padding: '0.35rem 0.75rem',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius)',
  background: 'transparent',
  fontSize: '0.85rem',
};

const emptyStyle: CSSProperties = {
  background: 'var(--color-surface)',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius)',
  padding: '2rem',
  textAlign: 'center',
  color: 'var(--color-text-muted)',
};

const activeStyle: CSSProperties = {
  display: 'inline-block',
  padding: '0.2rem 0.6rem',
  borderRadius: '999px',
  fontSize: '0.75rem',
  fontWeight: 600,
  background: '#d1fae5',
  color: '#065f46',
};

const inactiveStyle: CSSProperties = {
  ...activeStyle,
  background: '#e2e8f0',
  color: '#64748b',
};
