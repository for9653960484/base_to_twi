import { FormEvent, useEffect, useState, type CSSProperties } from 'react';
import { useTranslation } from 'react-i18next';
import type { Equipment } from '@/types';

interface FormData {
  name: string;
  serial_name?: string | null;
  description?: string | null;
}

interface Props {
  initial: Equipment | null;
  loading?: boolean;
  onClose: () => void;
  onSubmit: (data: FormData) => void;
}

export function EquipmentForm({ initial, loading, onClose, onSubmit }: Props) {
  const { t } = useTranslation();
  const [name, setName] = useState(initial?.name ?? '');
  const [serialName, setSerialName] = useState(initial?.serial_name ?? '');
  const [description, setDescription] = useState(initial?.description ?? '');

  useEffect(() => {
    setName(initial?.name ?? '');
    setSerialName(initial?.serial_name ?? '');
    setDescription(initial?.description ?? '');
  }, [initial]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    const trimmedSerial = serialName.trim();
    const trimmedDescription = description.trim();
    onSubmit({
      name: name.trim(),
      serial_name: trimmedSerial || (initial ? null : undefined),
      description: trimmedDescription || (initial ? null : undefined),
    });
  };

  return (
    <div style={overlayStyle} onClick={onClose}>
      <form
        style={modalStyle}
        onClick={(e) => e.stopPropagation()}
        onSubmit={handleSubmit}
      >
        <h3 style={{ marginBottom: '1.25rem', fontWeight: 700 }}>
          {initial ? t('equipment.editTitle') : t('equipment.createTitle')}
        </h3>

        <label style={labelStyle}>
          {t('equipment.name')} *
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            style={inputStyle}
          />
        </label>

        <label style={labelStyle}>
          {t('equipment.serialName')}
          <input
            value={serialName}
            onChange={(e) => setSerialName(e.target.value)}
            style={inputStyle}
          />
        </label>

        <label style={labelStyle}>
          {t('equipment.description')}
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            style={{ ...inputStyle, resize: 'vertical' }}
          />
        </label>

        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
          <button type="button" onClick={onClose} style={cancelBtn} disabled={loading}>
            {t('common.cancel')}
          </button>
          <button type="submit" style={submitBtn} disabled={loading}>
            {loading ? t('common.loading') : t('common.save')}
          </button>
        </div>
      </form>
    </div>
  );
}

const overlayStyle: CSSProperties = {
  position: 'fixed',
  inset: 0,
  background: 'rgba(0,0,0,0.4)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000,
  padding: '1rem',
};

const modalStyle: CSSProperties = {
  background: 'var(--color-surface)',
  borderRadius: 'var(--radius)',
  padding: '1.5rem',
  width: '100%',
  maxWidth: '480px',
  boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
};

const labelStyle: CSSProperties = {
  display: 'block',
  marginBottom: '1rem',
  fontSize: '0.9rem',
  fontWeight: 500,
};

const inputStyle: CSSProperties = {
  display: 'block',
  width: '100%',
  marginTop: '0.35rem',
  padding: '0.6rem 0.75rem',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius)',
};

const cancelBtn: CSSProperties = {
  padding: '0.5rem 1rem',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius)',
  background: 'transparent',
};

const submitBtn: CSSProperties = {
  padding: '0.5rem 1rem',
  border: 'none',
  borderRadius: 'var(--radius)',
  background: 'var(--color-primary)',
  color: '#fff',
};
