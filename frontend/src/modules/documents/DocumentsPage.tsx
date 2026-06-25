import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState, type CSSProperties } from 'react';
import { useTranslation } from 'react-i18next';
import { documentsApi } from '@/api/documents';
import { equipmentApi } from '@/api/equipment';
import { PageHeader } from '@/components/ui/PageHeader';
import { DocumentTable } from './components/DocumentTable';
import { DocumentUploadForm } from './components/DocumentUploadForm';

export function DocumentsPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [equipmentFilter, setEquipmentFilter] = useState('');
  const [showForm, setShowForm] = useState(false);

  const { data: equipmentData } = useQuery({
    queryKey: ['equipment', 'all'],
    queryFn: async () => {
      const { data } = await equipmentApi.list({ page_size: 100 });
      return data.items;
    },
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ['documents', search, equipmentFilter],
    queryFn: async () => {
      const { data } = await documentsApi.list({
        search: search || undefined,
        equipment_id: equipmentFilter || undefined,
      });
      return data;
    },
    refetchInterval: (query) => {
      const items = query.state.data?.items ?? [];
      return items.some((d) => d.ai_processing_status === 'processing') ? 3000 : false;
    },
  });

  const [uploadError, setUploadError] = useState('');

  const uploadMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      const { data } = await documentsApi.upload(formData);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      setShowForm(false);
      setUploadError('');
    },
    onError: () => setUploadError(t('documents.uploadError')),
  });

  const actionMutation = useMutation({
    mutationFn: async ({ action, id, force }: { action: string; id: string; force?: boolean }) => {
      if (action === 'submit') return documentsApi.submit(id);
      if (action === 'approve') return documentsApi.approve(id);
      if (action === 'archive') return documentsApi.archive(id);
      if (action === 'ai') return documentsApi.startAiProcess(id, force);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['documents'] }),
  });

  return (
    <div>
      <PageHeader
        title={t('documents.title')}
        actions={
          <button onClick={() => setShowForm(true)} style={btnPrimary}>
            {t('common.upload')}
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
        <select
          value={equipmentFilter}
          onChange={(e) => setEquipmentFilter(e.target.value)}
          style={inputStyle}
        >
          <option value="">{t('documents.allEquipment')}</option>
          {equipmentData?.map((eq) => (
            <option key={eq.id} value={eq.id}>
              {eq.name}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div style={{ color: 'var(--color-danger)', marginBottom: '1rem' }}>
          {t('documents.loadError')}
        </div>
      )}

      {isLoading ? (
        <p style={{ color: 'var(--color-text-muted)' }}>{t('common.loading')}</p>
      ) : (
        <DocumentTable
          items={data?.items ?? []}
          onAction={(action, id, force) => actionMutation.mutate({ action, id, force })}
          actionLoading={actionMutation.isPending}
        />
      )}

      {showForm && (
        <DocumentUploadForm
          equipmentList={equipmentData ?? []}
          loading={uploadMutation.isPending}
          error={uploadError}
          onClose={() => {
            setShowForm(false);
            setUploadError('');
          }}
          onSubmit={(formData) => uploadMutation.mutate(formData)}
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
  minWidth: '200px',
};
