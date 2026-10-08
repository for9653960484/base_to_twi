import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState, type CSSProperties } from 'react';
import { useTranslation } from 'react-i18next';
import { documentsApi } from '@/api/documents';
import { equipmentApi } from '@/api/equipment';
import { safetyApi, type SafetySheetUpdate } from '@/api/safety';
import { PageHeader } from '@/components/ui/PageHeader';
import type { SafetySheet } from '@/types';
import { SafetyForm } from './components/SafetyForm';

type Notice = {
  type: 'info' | 'success' | 'error';
  message: string;
};

export function SafetyPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [equipmentId, setEquipmentId] = useState('');
  const [documentId, setDocumentId] = useState('');
  const [notice, setNotice] = useState<Notice | null>(null);
  const [trackingId, setTrackingId] = useState<string | null>(null);
  const [trackedTaskId, setTrackedTaskId] = useState<string | null>(null);
  const [editing, setEditing] = useState<SafetySheet | null>(null);

  const { data: equipmentList } = useQuery({
    queryKey: ['equipment', 'all'],
    queryFn: async () => {
      const { data } = await equipmentApi.list({ page_size: 100 });
      return data.items;
    },
  });

  const { data: documents } = useQuery({
    queryKey: ['documents', 'safety', equipmentId],
    queryFn: async () => {
      const { data } = await documentsApi.list({
        equipment_id: equipmentId,
        page_size: 100,
      });
      return data.items.filter((doc) => doc.ai_processing_status === 'completed');
    },
    enabled: Boolean(equipmentId),
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ['safety', equipmentId],
    queryFn: async () => {
      const { data } = await safetyApi.list({
        equipment_id: equipmentId || undefined,
        page_size: 100,
      });
      return data;
    },
  });

  useEffect(() => {
    setDocumentId('');
    setTrackingId(null);
    setTrackedTaskId(null);
    setNotice(null);
  }, [equipmentId]);

  useEffect(() => {
    if (!documents || trackingId) return;
    if (documents.length === 1) setDocumentId(documents[0].id);
  }, [documents, trackingId]);

  useEffect(() => {
    if (!trackingId) return;

    const poll = async () => {
      try {
        const { data: status } = await safetyApi.generationStatus(trackingId);
        if (trackedTaskId && status.task_id && status.task_id !== trackedTaskId) return;
        const doc = documents?.find((item) => item.id === trackingId);
        if (status.ai_processing_status === 'pending' || status.ai_processing_status === 'processing') {
          return;
        }
        if (status.ai_processing_status === 'completed') {
          setNotice({
            type: 'success',
            message: t('safety.generateCompleted', {
              title: doc?.title ?? '',
              count: status.sheets_count ?? 0,
            }),
          });
          setTrackingId(null);
          setTrackedTaskId(null);
          queryClient.invalidateQueries({ queryKey: ['safety', equipmentId] });
        } else if (status.ai_processing_status === 'failed') {
          setNotice({
            type: 'error',
            message: status.error_message
              ? `${t('safety.generateFailed')}: ${status.error_message}`
              : t('safety.generateFailed'),
          });
          setTrackingId(null);
          setTrackedTaskId(null);
        }
      } catch {
        // keep polling
      }
    };

    void poll();
    const timer = window.setInterval(() => {
      void poll();
    }, 3000);
    return () => window.clearInterval(timer);
  }, [documents, equipmentId, queryClient, t, trackedTaskId, trackingId]);

  const generateMutation = useMutation({
    mutationFn: async (id: string) => {
      const { data: result } = await safetyApi.generate(id);
      return result;
    },
    onSuccess: (result, id) => {
      const doc = documents?.find((item) => item.id === id);
      setNotice({
        type: 'info',
        message: t('safety.generateStarted', { title: doc?.title ?? '' }),
      });
      setTrackingId(id);
      setTrackedTaskId(result.task_id ?? null);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setNotice({
        type: 'error',
        message: detail ? `${t('safety.generateError')}: ${detail}` : t('safety.generateError'),
      });
      setTrackingId(null);
      setTrackedTaskId(null);
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: SafetySheetUpdate }) => {
      const { data: result } = await safetyApi.update(id, data);
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['safety'] });
      setEditing(null);
    },
  });

  const readyDocuments = documents ?? [];
  const busy = generateMutation.isPending || Boolean(trackingId);

  return (
    <div>
      <PageHeader title={t('nav.safety')} />

      <select value={equipmentId} onChange={(e) => setEquipmentId(e.target.value)} style={selectStyle}>
        <option value="">{t('safety.selectEquipment')}</option>
        {equipmentList?.map((eq) => (
          <option key={eq.id} value={eq.id}>
            {eq.name}
          </option>
        ))}
      </select>

      {equipmentId && (
        <div style={generateRow}>
          <select
            value={documentId}
            onChange={(e) => setDocumentId(e.target.value)}
            style={selectStyle}
            disabled={readyDocuments.length === 0 || busy}
          >
            <option value="">
              {readyDocuments.length === 0 ? t('safety.noIndexedDocuments') : t('safety.selectDocument')}
            </option>
            {readyDocuments.map((doc) => (
              <option key={doc.id} value={doc.id}>
                {doc.title}
              </option>
            ))}
          </select>
          <button
            type="button"
            style={{ ...generateBtn, ...(busy || readyDocuments.length === 0 ? disabledBtn : {}) }}
            disabled={busy || readyDocuments.length === 0}
            onClick={() => {
              if (!documentId) {
                setNotice({ type: 'error', message: t('safety.pickDocument') });
                return;
              }
              const doc = readyDocuments.find((item) => item.id === documentId);
              setNotice({
                type: 'info',
                message: t('safety.generateStarted', { title: doc?.title ?? '' }),
              });
              generateMutation.mutate(documentId);
            }}
          >
            {busy ? t('safety.generating') : t('safety.generate')}
          </button>
        </div>
      )}

      {trackingId && (
        <div style={progressStyle} role="status">
          {t('safety.generating')}
        </div>
      )}

      {notice && (
        <div style={noticeStyle(notice.type)}>
          <span>{notice.message}</span>
          <button type="button" onClick={() => setNotice(null)} style={noticeDismissBtn}>
            {t('common.close')}
          </button>
        </div>
      )}

      {isLoading && (
        <p style={{ color: 'var(--color-text-muted)', marginTop: '1rem' }}>{t('common.loading')}</p>
      )}
      {error && (
        <p style={{ color: 'var(--color-danger)', marginTop: '1rem' }}>{t('safety.loadError')}</p>
      )}
      {updateMutation.isError && (
        <p style={{ color: 'var(--color-danger)', marginTop: '1rem' }}>{t('safety.saveError')}</p>
      )}
      {data && !isLoading && (
        <div style={{ marginTop: '1rem', overflowX: 'auto' }}>
          {data.items.length === 0 ? (
            <div style={placeholderStyle}>{t('safety.noSheets')}</div>
          ) : (
            <table style={tableStyle}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--color-border)', textAlign: 'left' }}>
                  <th style={thStyle}>{t('safety.colTitle')}</th>
                  <th style={thStyle}>{t('safety.equipment')}</th>
                  <th style={thStyle}></th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((sheet) => (
                  <SafetyRow key={sheet.id} sheet={sheet} onEdit={setEditing} />
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {editing && (
        <SafetyForm
          key={editing.id}
          initial={editing}
          equipment={equipmentList ?? []}
          loading={updateMutation.isPending}
          onClose={() => {
            setEditing(null);
            updateMutation.reset();
          }}
          onSubmit={(formData) => updateMutation.mutate({ id: editing.id, data: formData })}
        />
      )}
    </div>
  );
}

function SafetyRow({ sheet, onEdit }: { sheet: SafetySheet; onEdit: (sheet: SafetySheet) => void }) {
  const { t } = useTranslation();
  return (
    <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
      <td style={tdStyle}>
        <strong>{sheet.title}</strong>
      </td>
      <td style={tdStyle}>{sheet.equipment_name || '—'}</td>
      <td style={tdStyle}>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button type="button" onClick={() => onEdit(sheet)} style={editBtn}>
            {t('common.edit')}
          </button>
          <a href={safetyApi.exportPdfUrl(sheet.id)} style={pdfLink} target="_blank" rel="noreferrer">
            {t('safety.downloadPdf')}
          </a>
        </div>
      </td>
    </tr>
  );
}

const selectStyle: CSSProperties = {
  padding: '0.5rem 0.75rem',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius)',
  minWidth: '280px',
};

const placeholderStyle: CSSProperties = {
  marginTop: '1rem',
  padding: '2rem',
  textAlign: 'center',
  color: 'var(--color-text-muted)',
  border: '1px dashed var(--color-border)',
  borderRadius: 'var(--radius)',
};

const generateRow: CSSProperties = {
  display: 'flex',
  gap: '0.75rem',
  alignItems: 'center',
  flexWrap: 'wrap',
  marginTop: '1rem',
};

const generateBtn: CSSProperties = {
  padding: '0.5rem 1rem',
  background: 'var(--color-primary)',
  color: '#fff',
  border: 'none',
  borderRadius: 'var(--radius)',
  cursor: 'pointer',
};

const disabledBtn: CSSProperties = { opacity: 0.55, cursor: 'not-allowed' };

const progressStyle: CSSProperties = {
  marginTop: '1rem',
  padding: '0.85rem 1rem',
  borderRadius: 'var(--radius)',
  border: '1px solid #93c5fd',
  background: '#dbeafe',
  color: '#1e40af',
  fontWeight: 600,
};

function noticeStyle(type: Notice['type']): CSSProperties {
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
    marginTop: '1rem',
    padding: '0.75rem 1rem',
    borderRadius: 'var(--radius)',
    border: `1px solid ${palette.border}`,
    background: palette.bg,
    color: palette.text,
  };
}

const noticeDismissBtn: CSSProperties = {
  padding: '0.25rem 0.6rem',
  border: '1px solid currentColor',
  borderRadius: 'var(--radius)',
  background: 'transparent',
  color: 'inherit',
};

const tableStyle: CSSProperties = {
  width: '100%',
  borderCollapse: 'collapse',
  background: 'var(--color-surface)',
};

const thStyle: CSSProperties = {
  padding: '0.75rem',
  fontSize: '0.875rem',
  color: 'var(--color-text-muted)',
};

const tdStyle: CSSProperties = { padding: '0.75rem', verticalAlign: 'middle' };

const editBtn: CSSProperties = {
  padding: '0.35rem 0.75rem',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius)',
  background: 'transparent',
  fontSize: '0.85rem',
};

const pdfLink: CSSProperties = {
  fontSize: '0.875rem',
  color: 'var(--color-primary)',
  textDecoration: 'none',
};
