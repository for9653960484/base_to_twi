import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { equipmentApi } from '@/api/equipment';
import type { Equipment } from '@/types';
import { EquipmentForm } from './components/EquipmentForm';
import { EquipmentTable } from './components/EquipmentTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { useState, type CSSProperties } from 'react';

export function EquipmentPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [showActiveOnly, setShowActiveOnly] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Equipment | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['equipment', search, showActiveOnly],
    queryFn: async () => {
      const { data } = await equipmentApi.list({
        search: search || undefined,
        is_active: showActiveOnly ? true : undefined,
      });
      return data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (formData: { name: string; serial_name?: string; description?: string }) => {
      const { data } = await equipmentApi.create(formData);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipment'] });
      setShowForm(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Equipment> }) => {
      const { data: result } = await equipmentApi.update(id, data);
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipment'] });
      setEditing(null);
    },
  });

  return (
    <div>
      <PageHeader
        title={t('equipment.title')}
        actions={
          <button
            onClick={() => {
              setEditing(null);
              setShowForm(true);
            }}
            style={btnPrimary}
          >
            {t('common.create')}
          </button>
        }
      />

      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={t('common.search')}
          style={inputStyle}
        />
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.9rem' }}>
          <input
            type="checkbox"
            checked={showActiveOnly}
            onChange={(e) => setShowActiveOnly(e.target.checked)}
          />
          {t('equipment.activeOnly')}
        </label>
      </div>

      {error && (
        <div style={{ color: 'var(--color-danger)', marginBottom: '1rem' }}>
          {t('equipment.loadError')}
        </div>
      )}

      {isLoading ? (
        <p style={{ color: 'var(--color-text-muted)' }}>{t('common.loading')}</p>
      ) : (
        <EquipmentTable
          items={data?.items ?? []}
          onEdit={(item) => {
            setEditing(item);
            setShowForm(true);
          }}
        />
      )}

      {showForm && (
        <EquipmentForm
          initial={editing}
          loading={createMutation.isPending || updateMutation.isPending}
          onClose={() => {
            setShowForm(false);
            setEditing(null);
          }}
          onSubmit={(formData) => {
            if (editing) {
              updateMutation.mutate({ id: editing.id, data: formData });
            } else {
              createMutation.mutate(formData);
            }
          }}
        />
      )}
    </div>
  );
}

const btnPrimary: CSSProperties = {
  padding: '0.5rem 1rem',
  background: 'var(--color-primary)',
  color: '#fff',
  border: 'none',
  borderRadius: 'var(--radius)',
};

const inputStyle: CSSProperties = {
  padding: '0.5rem 0.75rem',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius)',
  minWidth: '240px',
};
