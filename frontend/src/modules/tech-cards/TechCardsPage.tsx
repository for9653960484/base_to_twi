import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { equipmentApi } from '@/api/equipment';
import { techCardsApi } from '@/api/tech-cards';
import { PageHeader } from '@/components/ui/PageHeader';
import { TechCardList } from './components/TechCardList';

export function TechCardsPage() {
  const { t } = useTranslation();
  const [equipmentId, setEquipmentId] = useState('');

  const { data: equipmentList } = useQuery({
    queryKey: ['equipment', 'all'],
    queryFn: async () => {
      const { data } = await equipmentApi.list({ page_size: 100 });
      return data.items;
    },
  });

  const { data, isLoading, error, isFetching } = useQuery({
    queryKey: ['tech-cards', equipmentId],
    queryFn: async () => {
      const { data } = await techCardsApi.list({
        equipment_id: equipmentId,
        page_size: 100,
      });
      return data;
    },
    enabled: Boolean(equipmentId),
  });

  return (
    <div>
      <PageHeader title={t('nav.techCards')} />

      <p style={{ color: 'var(--color-text-muted)', marginBottom: '1rem' }}>
        {t('techCards.hint')}
      </p>

      <select
        value={equipmentId}
        onChange={(e) => setEquipmentId(e.target.value)}
        style={selectStyle}
      >
        <option value="">{t('techCards.selectEquipment')}</option>
        {equipmentList?.map((eq) => (
          <option key={eq.id} value={eq.id}>
            {eq.name}
          </option>
        ))}
      </select>

      {!equipmentId && (
        <div style={placeholderStyle}>{t('techCards.pickEquipment')}</div>
      )}

      {equipmentId && isLoading && (
        <p style={{ color: 'var(--color-text-muted)', marginTop: '1rem' }}>{t('common.loading')}</p>
      )}

      {equipmentId && error && (
        <p style={{ color: 'var(--color-danger)', marginTop: '1rem' }}>{t('techCards.loadError')}</p>
      )}

      {equipmentId && data && !isLoading && (
        <>
          {isFetching && (
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', marginTop: '1rem' }}>
              {t('common.loading')}
            </p>
          )}
          <div style={{ marginTop: '1rem' }}>
            <TechCardList items={data.items} />
          </div>
        </>
      )}
    </div>
  );
}

const selectStyle: React.CSSProperties = {
  padding: '0.5rem 0.75rem',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius)',
  minWidth: '280px',
};

const placeholderStyle: React.CSSProperties = {
  marginTop: '1rem',
  padding: '2rem',
  textAlign: 'center',
  color: 'var(--color-text-muted)',
  border: '1px dashed var(--color-border)',
  borderRadius: 'var(--radius)',
};
