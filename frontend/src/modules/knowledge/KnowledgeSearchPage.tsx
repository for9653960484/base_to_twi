import { useState, type CSSProperties } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { equipmentApi } from '@/api/equipment';
import { knowledgeApi } from '@/api/knowledge';
import { PageHeader } from '@/components/ui/PageHeader';
import type { KnowledgeSource } from '@/types';

export function KnowledgeSearchPage() {
  const { t } = useTranslation();
  const [query, setQuery] = useState('');
  const [equipmentId, setEquipmentId] = useState('');
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState<KnowledgeSource[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { data: equipmentList } = useQuery({
    queryKey: ['equipment', 'all'],
    queryFn: async () => {
      const { data } = await equipmentApi.list({ page_size: 100 });
      return data.items;
    },
  });

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError('');
    setAnswer('');
    setSources([]);
    try {
      const { data } = await knowledgeApi.search(
        query.trim(),
        equipmentId || undefined,
      );
      setAnswer(data.answer || t('common.noData'));
      setSources(data.sources ?? []);
    } catch {
      setError(t('knowledge.error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <PageHeader title={t('knowledge.title')} />

      <div style={{ marginBottom: '1rem' }}>
        <label style={labelStyle} htmlFor="knowledge-equipment">
          {t('knowledge.equipment')}
        </label>
        <select
          id="knowledge-equipment"
          value={equipmentId}
          onChange={(e) => setEquipmentId(e.target.value)}
          style={selectStyle}
        >
          <option value="">{t('knowledge.allEquipment')}</option>
          {equipmentList?.map((eq) => (
            <option key={eq.id} value={eq.id}>
              {eq.name}
            </option>
          ))}
        </select>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder={t('knowledge.placeholder')}
          style={inputStyle}
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          style={btnStyle}
        >
          {loading ? t('common.loading') : t('knowledge.ask')}
        </button>
      </div>

      {error && <div style={errorStyle}>{error}</div>}

      {answer && (
        <div style={cardStyle}>
          <h3 style={answerTitleStyle}>{t('knowledge.answer')}</h3>
          <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{answer}</p>
        </div>
      )}

      {sources.length > 0 && (
        <div style={{ marginTop: '1.5rem' }}>
          <h3 style={answerTitleStyle}>{t('knowledge.sources')}</h3>
          <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
            {sources.map((src) => (
              <li key={`${src.source_id}-${src.excerpt.slice(0, 20)}`} style={{ marginBottom: '0.75rem' }}>
                <strong>{src.title}</strong>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
                  {' '}
                  ({Math.round(src.relevance_score * 100)}%)
                </span>
                <div style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
                  {src.excerpt}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

const labelStyle: CSSProperties = {
  display: 'block',
  marginBottom: '0.35rem',
  fontSize: '0.875rem',
  color: 'var(--color-text-muted)',
};

const selectStyle: CSSProperties = {
  width: '100%',
  maxWidth: '420px',
  padding: '0.5rem 0.75rem',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius)',
};

const inputStyle: CSSProperties = {
  flex: 1,
  padding: '0.75rem 1rem',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius)',
};

const btnStyle: CSSProperties = {
  padding: '0.75rem 1.5rem',
  background: 'var(--color-primary)',
  color: '#fff',
  border: 'none',
  borderRadius: 'var(--radius)',
};

const cardStyle: CSSProperties = {
  background: 'var(--color-surface)',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius)',
  padding: '1.25rem',
};

const answerTitleStyle: CSSProperties = {
  margin: '0 0 0.75rem',
  fontSize: '1rem',
};

const errorStyle: CSSProperties = {
  color: 'var(--color-danger)',
  marginBottom: '1rem',
};
