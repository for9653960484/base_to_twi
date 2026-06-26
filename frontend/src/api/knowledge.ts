import { apiClient } from './client';
import type { KnowledgeSearchResponse } from '@/types';

export const knowledgeApi = {
  search: (query: string, equipmentId?: string) =>
    apiClient.post<KnowledgeSearchResponse>('/knowledge/search', {
      query,
      equipment_id: equipmentId,
    }),
};
