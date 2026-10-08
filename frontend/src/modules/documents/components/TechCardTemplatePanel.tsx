import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState, type CSSProperties } from 'react';
import { useTranslation } from 'react-i18next';
import { brandbookApi } from '@/api/brandbook';

export function TechCardTemplatePanel() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [error, setError] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['brandbook', 'tech_card'],
    queryFn: async () => {
      const { data } = await brandbookApi.list('tech_card');
      return data;
    },
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => brandbookApi.uploadTechCardTemplate(file),
    onSuccess: () => {
      setError('');
      queryClient.invalidateQueries({ queryKey: ['brandbook', 'tech_card'] });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ? `${t('documents.techCardTemplateError')}: ${detail}` : t('documents.techCardTemplateError'));
    },
  });

  const active = data?.find((item) => item.is_active);

  return (
    <section style={panelStyle}>
      <h3 style={{ margin: '0 0 0.35rem' }}>{t('documents.techCardTemplateTitle')}</h3>
      <p style={hintStyle}>{t('documents.techCardTemplateHint')}</p>
      {isLoading ? (
        <p style={hintStyle}>{t('common.loading')}</p>
      ) : (
        <p style={{ margin: '0.5rem 0' }}>
          {active
            ? t('documents.techCardTemplateCurrent', { name: active.file_name, version: active.version })
            : t('documents.techCardTemplateMissing')}
        </p>
      )}
      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <a href={brandbookApi.techCardSampleUrl()} style={linkBtn}>
          {t('documents.techCardTemplateSample')}
        </a>
        <label style={{ ...linkBtn, cursor: 'pointer' }}>
          {uploadMutation.isPending ? t('common.loading') : t('documents.techCardTemplateUpload')}
          <input
            type="file"
            accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            style={{ display: 'none' }}
            disabled={uploadMutation.isPending}
            onChange={(event) => {
              const file = event.target.files?.[0];
              event.target.value = '';
              if (file) uploadMutation.mutate(file);
            }}
          />
        </label>
      </div>
      {error && <p style={{ color: 'var(--color-danger)', margin: '0.5rem 0 0' }}>{error}</p>}
    </section>
  );
}

const panelStyle: CSSProperties = {
  marginBottom: '1rem',
  padding: '1rem 1.25rem',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius)',
  background: 'var(--color-surface)',
};

const hintStyle: CSSProperties = {
  margin: 0,
  color: 'var(--color-text-muted)',
  fontSize: '0.92rem',
};

const linkBtn: CSSProperties = {
  display: 'inline-block',
  padding: '0.45rem 0.8rem',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius)',
  background: 'var(--color-surface)',
  color: 'var(--color-primary)',
  textDecoration: 'none',
};
