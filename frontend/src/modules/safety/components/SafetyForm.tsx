import { FormEvent, useState, type CSSProperties } from 'react';
import { useTranslation } from 'react-i18next';
import type { SafetySheetUpdate } from '@/api/safety';
import type { Equipment, PpeItem, SafetySheet } from '@/types';

interface Props {
  initial: SafetySheet;
  equipment: Equipment[];
  loading?: boolean;
  onClose: () => void;
  onSubmit: (data: SafetySheetUpdate) => void;
}

export function SafetyForm({ initial, equipment, loading, onClose, onSubmit }: Props) {
  const { t } = useTranslation();
  const [title, setTitle] = useState(initial.title);
  const [equipmentId, setEquipmentId] = useState(initial.equipment_id);
  const [ppe, setPpe] = useState<PpeItem[]>(
    initial.ppe.length > 0 ? initial.ppe : [{ name: '', purpose: '', mandatory: true }],
  );
  const [temperature, setTemperature] = useState(initial.work_conditions.temperature ?? '');
  const [humidity, setHumidity] = useState(initial.work_conditions.humidity ?? '');
  const [voltage, setVoltage] = useState(initial.work_conditions.voltage ?? '');
  const [other, setOther] = useState(initial.work_conditions.other ?? []);
  const [notes, setNotes] = useState(initial.notes ?? '');

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!title.trim() || !equipmentId) return;
    onSubmit({
      title: title.trim(),
      equipment_id: equipmentId,
      ppe: ppe
        .map((item) => ({
          name: item.name.trim(),
          purpose: item.purpose.trim(),
          mandatory: item.mandatory,
        }))
        .filter((item) => item.name),
      work_conditions: {
        temperature: temperature.trim(),
        humidity: humidity.trim(),
        voltage: voltage.trim(),
        other: other
          .map((item) => ({ name: item.name.trim(), value: item.value.trim() }))
          .filter((item) => item.name && item.value),
      },
      notes: notes.trim() || null,
    });
  };

  return (
    <div style={overlayStyle} onClick={onClose}>
      <form style={modalStyle} onClick={(event) => event.stopPropagation()} onSubmit={handleSubmit}>
        <h3 style={{ marginBottom: '1.25rem', fontWeight: 700 }}>{t('safety.editTitle')}</h3>

        <label style={labelStyle}>
          {t('safety.colTitle')} *
          <input value={title} onChange={(e) => setTitle(e.target.value)} required style={inputStyle} disabled={loading} />
        </label>

        <label style={labelStyle}>
          {t('safety.equipment')} *
          <select
            value={equipmentId}
            onChange={(e) => setEquipmentId(e.target.value)}
            required
            style={inputStyle}
            disabled={loading}
          >
            {equipment.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </label>

        <div style={labelStyle}>
          {t('safety.ppe')}
          {ppe.map((item, index) => (
            <div key={index} style={rowStyle}>
              <input
                value={item.name}
                placeholder={t('safety.ppeName')}
                onChange={(e) => updatePpe(index, { name: e.target.value })}
                style={inputStyle}
                disabled={loading}
              />
              <input
                value={item.purpose}
                placeholder={t('safety.ppePurpose')}
                onChange={(e) => updatePpe(index, { purpose: e.target.value })}
                style={inputStyle}
                disabled={loading}
              />
              <label style={checkStyle}>
                <input
                  type="checkbox"
                  checked={item.mandatory}
                  onChange={(e) => updatePpe(index, { mandatory: e.target.checked })}
                  disabled={loading}
                />
                {t('safety.mandatory')}
              </label>
              <button type="button" onClick={() => setPpe(ppe.filter((_, i) => i !== index))} style={removeBtn} disabled={loading}>
                {t('common.delete')}
              </button>
            </div>
          ))}
          <button
            type="button"
            style={addBtn}
            disabled={loading}
            onClick={() => setPpe([...ppe, { name: '', purpose: '', mandatory: true }])}
          >
            {t('safety.addPpe')}
          </button>
        </div>

        <label style={labelStyle}>
          {t('safety.temperature')}
          <input value={temperature} onChange={(e) => setTemperature(e.target.value)} style={inputStyle} disabled={loading} />
        </label>
        <label style={labelStyle}>
          {t('safety.humidity')}
          <input value={humidity} onChange={(e) => setHumidity(e.target.value)} style={inputStyle} disabled={loading} />
        </label>
        <label style={labelStyle}>
          {t('safety.voltage')}
          <input value={voltage} onChange={(e) => setVoltage(e.target.value)} style={inputStyle} disabled={loading} />
        </label>

        <div style={labelStyle}>
          {t('safety.otherConditions')}
          {other.map((item, index) => (
            <div key={index} style={rowStyle}>
              <input
                value={item.name}
                placeholder={t('safety.conditionName')}
                onChange={(e) => updateOther(index, { name: e.target.value })}
                style={inputStyle}
                disabled={loading}
              />
              <input
                value={item.value}
                placeholder={t('safety.conditionValue')}
                onChange={(e) => updateOther(index, { value: e.target.value })}
                style={inputStyle}
                disabled={loading}
              />
              <button type="button" onClick={() => setOther(other.filter((_, i) => i !== index))} style={removeBtn} disabled={loading}>
                {t('common.delete')}
              </button>
            </div>
          ))}
          <button
            type="button"
            style={addBtn}
            disabled={loading}
            onClick={() => setOther([...other, { name: '', value: '' }])}
          >
            {t('safety.addCondition')}
          </button>
        </div>

        <label style={labelStyle}>
          {t('safety.rules')}
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={4}
            style={{ ...inputStyle, resize: 'vertical' }}
            disabled={loading}
          />
        </label>

        <div style={footerStyle}>
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

  function updatePpe(index: number, patch: Partial<PpeItem>) {
    setPpe(ppe.map((item, i) => (i === index ? { ...item, ...patch } : item)));
  }

  function updateOther(index: number, patch: Partial<{ name: string; value: string }>) {
    setOther(other.map((item, i) => (i === index ? { ...item, ...patch } : item)));
  }
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
  maxWidth: '720px',
  maxHeight: '90vh',
  overflowY: 'auto',
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

const rowStyle: CSSProperties = {
  display: 'grid',
  gridTemplateColumns: '1fr 1fr auto auto',
  gap: '0.5rem',
  alignItems: 'end',
  marginTop: '0.5rem',
};

const checkStyle: CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '0.35rem',
  fontWeight: 400,
  whiteSpace: 'nowrap',
  marginBottom: '0.45rem',
};

const footerStyle: CSSProperties = {
  display: 'flex',
  justifyContent: 'flex-end',
  gap: '0.5rem',
  marginTop: '1rem',
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

const addBtn: CSSProperties = {
  marginTop: '0.5rem',
  padding: '0.35rem 0.75rem',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius)',
  background: 'transparent',
};

const removeBtn: CSSProperties = {
  padding: '0.45rem 0.7rem',
  marginBottom: '0.05rem',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius)',
  background: 'transparent',
};
