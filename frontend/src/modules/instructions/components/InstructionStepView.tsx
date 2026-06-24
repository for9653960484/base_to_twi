import { useTranslation } from 'react-i18next';
import type { InstructionStep } from '@/types';

interface Props {
  step: InstructionStep;
}

export function InstructionStepView({ step }: Props) {
  const { t } = useTranslation();

  return (
    <article
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius)',
        padding: '1.25rem',
        boxShadow: 'var(--shadow)',
      }}
    >
      <header style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', marginBottom: '0.75rem' }}>
        <span
          style={{
            width: '2rem',
            height: '2rem',
            borderRadius: '50%',
            background: 'var(--color-primary)',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 700,
            flexShrink: 0,
          }}
        >
          {step.step_number}
        </span>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>{step.title}</h3>
      </header>

      {step.description && <p style={{ marginBottom: '0.75rem' }}>{step.description}</p>}

      {step.key_points.length > 0 && (
        <section style={{ marginBottom: '0.75rem' }}>
          <h4 style={{ fontSize: '0.85rem', color: 'var(--color-warning)', marginBottom: '0.25rem' }}>
            {t('instructions.keyPoints')}
          </h4>
          <ul style={{ paddingLeft: '1.25rem' }}>
            {step.key_points.map((kp, i) => (
              <li key={i}>{kp.content}</li>
            ))}
          </ul>
        </section>
      )}

      {step.reasons.length > 0 && (
        <section style={{ marginBottom: '0.75rem' }}>
          <h4 style={{ fontSize: '0.85rem', color: 'var(--color-info)', marginBottom: '0.25rem' }}>
            {t('instructions.reasons')}
          </h4>
          <ul style={{ paddingLeft: '1.25rem' }}>
            {step.reasons.map((r, i) => (
              <li key={i}>{r.content}</li>
            ))}
          </ul>
        </section>
      )}

      {step.safety_notes && (
        <p
          style={{
            padding: '0.5rem 0.75rem',
            background: '#fef2f2',
            borderRadius: 'var(--radius)',
            fontSize: '0.9rem',
            color: 'var(--color-danger)',
          }}
        >
          ⚠ {step.safety_notes}
        </p>
      )}
    </article>
  );
}
