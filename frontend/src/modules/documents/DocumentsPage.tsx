import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState, type CSSProperties } from 'react';
import { useTranslation } from 'react-i18next';
import { documentsApi } from '@/api/documents';
import { equipmentApi } from '@/api/equipment';
import { PageHeader } from '@/components/ui/PageHeader';
import { DocumentTable } from './components/DocumentTable';
import { DocumentUploadForm } from './components/DocumentUploadForm';

type AiNotice = {
  type: 'info' | 'success' | 'error';
  message: string;
};

export function DocumentsPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [equipmentFilter, setEquipmentFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [aiNotice, setAiNotice] = useState<AiNotice | null>(null);
  const [trackingAi, setTrackingAi] = useState<Record<string, true>>({});

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

  useEffect(() => {
    if (!data?.items || Object.keys(trackingAi).length === 0) return;

    for (const docId of Object.keys(trackingAi)) {
      const doc = data.items.find((d) => d.id === docId);
      if (!doc) continue;

      if (doc.ai_processing_status === 'completed') {
        setAiNotice({
          type: 'success',
          message: t('documents.aiCompleted', { title: doc.title }),
        });
        setTrackingAi((prev) => {
          const next = { ...prev };
          delete next[docId];
          return next;
        });
      } else if (doc.ai_processing_status === 'failed') {
        setAiNotice({
          type: 'error',
          message: t('documents.aiFailed', { title: doc.title }),
        });
        setTrackingAi((prev) => {
          const next = { ...prev };
          delete next[docId];
          return next;
        });
      }
    }
  }, [data, trackingAi, t]);

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
    onError: (err: unknown) => {
      const detail =
        (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data
          ?.detail ||
        (err as { message?: string })?.message;
      setUploadError(
        detail ? `${t('documents.uploadError')}: ${detail}` : t('documents.uploadError'),
      );
    },
  });

  const actionMutation = useMutation({
    mutationFn: async ({ action, id, force }: { action: string; id: string; force?: boolean }) => {
      if (action === 'submit') return documentsApi.submit(id);
      if (action === 'approve') return documentsApi.approve(id);
      if (action === 'archive') return documentsApi.archive(id);
      if (action === 'ai') return documentsApi.startAiProcess(id, force);
    },
    onSuccess: (_result, variables) => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      if (variables.action === 'ai') {
        const doc = data?.items.find((d) => d.id === variables.id);
        setAiNotice({
          type: 'info',
          message: t('documents.aiStarted', { title: doc?.title ?? '' }),
        });
        setTrackingAi((prev) => ({ ...prev, [variables.id]: true }));
      }
    },
    onError: (_error, variables) => {
      if (variables.action === 'ai') {
        setAiNotice({ type: 'error', message: t('documents.aiStartError') });
        setTrackingAi((prev) => {
          const next = { ...prev };
          delete next[variables.id];
          return next;
        });
      }
    },
  });

  const [trackingTechCards, setTrackingTechCards] = useState<Record<string, true>>({});
  const trackedTechCardIds = Object.keys(trackingTechCards);

  useEffect(() => {
    if (trackedTechCardIds.length === 0) return;

    const timer = window.setInterval(async () => {
      const ids = [...trackedTechCardIds];
      for (const id of ids) {
        try {
          const { data: status } = await documentsApi.getTechCardsGenerationStatus(id);
          const doc = data?.items.find((d) => d.id === id);
          if (status.ai_processing_status === 'completed') {
            setAiNotice({
              type: 'success',
              message: t('documents.techCardsCompleted', {
                title: doc?.title ?? '',
                count: status.maintenance_works_count ?? 0,
              }),
            });
            setTrackingTechCards((prev) => {
              const next = { ...prev };
              delete next[id];
              return next;
            });
            queryClient.invalidateQueries({ queryKey: ['tech-cards'] });
          } else if (status.ai_processing_status === 'failed') {
            setAiNotice({
              type: 'error',
              message: status.error_message
                ? `${t('documents.techCardsFailed')}: ${status.error_message}`
                : t('documents.techCardsFailed'),
            });
            setTrackingTechCards((prev) => {
              const next = { ...prev };
              delete next[id];
              return next;
            });
          }
        } catch {
          // keep polling; transient API errors should not stop tracking
        }
      }
    }, 3000);

    return () => window.clearInterval(timer);
  }, [data?.items, queryClient, t, trackedTechCardIds]);

  const generateTechCardsMutation = useMutation({
    mutationFn: async (id: string) => {
      const { data: result } = await documentsApi.generateTechCards(id);
      return result;
    },
    onSuccess: (_result, id) => {
      const doc = data?.items.find((d) => d.id === id);
      setAiNotice({
        type: 'info',
        message: t('documents.techCardsStarted', { title: doc?.title ?? '' }),
      });
      setTrackingTechCards((prev) => ({ ...prev, [id]: true }));
    },
    onError: (err: unknown) => {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setAiNotice({
        type: 'error',
        message: detail
          ? `${t('documents.techCardsError')}: ${detail}`
          : t('documents.techCardsError'),
      });
    },
  });

  const handleAction = (action: string, id: string, force?: boolean) => {
    actionMutation.mutate({ action, id, force });
  };

  const handleGenerateTechCards = (id: string) => {
    generateTechCardsMutation.mutate(id);
  };

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

      {aiNotice && (
        <div style={noticeStyle(aiNotice.type)}>
          <span>{aiNotice.message}</span>
          <button type="button" onClick={() => setAiNotice(null)} style={noticeDismissBtn}>
            {t('common.close')}
          </button>
        </div>
      )}

      {isLoading ? (
        <p style={{ color: 'var(--color-text-muted)' }}>{t('common.loading')}</p>
      ) : (
        <DocumentTable
          items={data?.items ?? []}
          onAction={handleAction}
          actionLoading={actionMutation.isPending}
          onGenerateTechCards={handleGenerateTechCards}
          techCardsLoading={generateTechCardsMutation.isPending}
          techCardsLoadingId={generateTechCardsMutation.variables ?? null}
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

function noticeStyle(type: AiNotice['type']): CSSProperties {
  const palette = {
    info: { bg: '#dbeafe', border: '#93c5fd', text: '#1e40af' },
    success: { bg: '#d1fae5', border: '#6ee7b7', text: '#065f46' },
    error: { bg: '#fee2e2', border: '#fca5a5', text: '#991b1b' },
  }[type];

  return {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '1rem',
    marginBottom: '1rem',
    padding: '0.75rem 1rem',
    borderRadius: 'var(--radius)',
    border: `1px solid ${palette.border}`,
    background: palette.bg,
    color: palette.text,
    fontSize: '0.95rem',
  };
}

const noticeDismissBtn: CSSProperties = {
  padding: '0.25rem 0.6rem',
  border: '1px solid currentColor',
  borderRadius: 'var(--radius)',
  background: 'transparent',
  color: 'inherit',
  fontSize: '0.85rem',
  flexShrink: 0,
};
