import { FormEvent, useState, type CSSProperties } from 'react';
import { useTranslation } from 'react-i18next';
import type { Equipment } from '@/types';

interface Props {
  equipmentList: Equipment[];
  loading?: boolean;
  onClose: () => void;
  onSubmit: (formData: FormData) => void;
}

const ACCEPT = '.pdf,.docx,.doc,.txt,.md';

export function DocumentUploadForm({ equipmentList, loading, onClose, onSubmit }: Props) {
  const { t } = useTranslation();
  const [equipmentId, setEquipmentId] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState<File | null>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!equipmentId || !title.trim() || !file) return;

    const formData = new FormData();
    formData.append('equipment_id', equipmentId);
    formData.append('title', title.trim());
    if (description.trim()) formData.append('description', description.trim());
    formData.append('file', file);
    onSubmit(formData);
  };

  const handleFileChange = (f: File | null) => {
    setFile(f);
    if (f && !title) {
      const name = f.name.replace(/\.[^.]+$/, '');
      setTitle(name);
    }
  };

  return (
    <div style={overlayStyle} onClick={onClose}>
      <form style={modalStyle} onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h3 style={{ marginBottom: '1.25rem', fontWeight: 700 }}>{t('documents.uploadTitle')}</h3>

        <label style={labelStyle}>
          {t('documents.equipment')} *
          <select
            value={equipmentId}
            onChange={(e) => setEquipmentId(e.target.value)}
            required
            style={inputStyle}
          >
            <option value="">{t('documents.selectEquipment')}</option>
            {equipmentList.map((eq) => (
              <option key={eq.id} value={eq.id}>
                {eq.name}
              </option>
            ))}
          </select>
        </label>

        <label style={labelStyle}>
          {t('documents.colTitle')} *
          <input value={title} onChange={(e) => setTitle(e.target.value)} required style={inputStyle} />
        </label>

        <label style={labelStyle}>
          {t('equipment.description')}
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            style={{ ...inputStyle, resize: 'vertical' }}
          />
        </label>

        <label style={labelStyle}>
          {t('documents.file')} * ({t('documents.fileHint')})
          <input
            type="file"
            accept={ACCEPT}
            required
            onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
            style={{ ...inputStyle, padding: '0.4rem' }}
          />
        </label>

        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
          <button type="button" onClick={onClose} style={cancelBtn} disabled={loading}>
            {t('common.cancel')}
          </button>
          <button type="submit" style={submitBtn} disabled={loading || !file}>
            {loading ? t('common.loading') : t('common.upload')}
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
  maxWidth: '520px',
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
