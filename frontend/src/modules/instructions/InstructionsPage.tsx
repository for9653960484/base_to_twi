import { useTranslation } from 'react-i18next';
import { PageHeader } from '@/components/ui/PageHeader';
import { InstructionStepView } from './components/InstructionStepView';
import type { InstructionStep } from '@/types';

const demoSteps: InstructionStep[] = [
  {
    step_number: 1,
    title: 'Подготовка к обслуживанию',
    description: 'Отключить питание аттракциона и установить блокировку.',
    safety_notes: 'Убедиться в отсутствии напряжения.',
    tools: ['Мультиметр', 'Замок блокировки'],
    key_points: [{ content: 'Проверить блокировку главного выключателя' }],
    reasons: [{ content: 'Предотвращение поражения электрическим током' }],
    media: [],
  },
];

export function InstructionsPage() {
  const { t } = useTranslation();

  return (
    <div>
      <PageHeader title={t('instructions.title')} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {demoSteps.map((step) => (
          <InstructionStepView key={step.step_number} step={step} />
        ))}
      </div>
    </div>
  );
}
