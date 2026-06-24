import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { PageHeader } from '@/components/ui/PageHeader';
import { knowledgeApi } from '@/api/knowledge';

export function KnowledgeSearchPage() {
  const { t } = useTranslation();
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const { data } = await knowledgeApi.search(query);
      setAnswer(data.answer || t('common.noData'));
    } catch {
      setAnswer('Сервис справки временно недоступен.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <PageHeader title={t('knowledge.title')} />
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder={t('knowledge.placeholder')}
          style={{
            flex: 1,
            padding: '0.75rem 1rem',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius)',
          }}
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          style={{
            padding: '0.75rem 1.5rem',
            background: 'var(--color-primary)',
            color: '#fff',
            border: 'none',
            borderRadius: 'var(--radius)',
          }}
        >
          {loading ? t('common.loading') : t('knowledge.ask')}
        </button>
      </div>
      {answer && (
        <div
          style={{
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius)',
            padding: '1.25rem',
          }}
        >
          {answer}
        </div>
      )}
    </div>
  );
}
