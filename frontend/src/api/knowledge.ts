import { apiClient } from './client';

export const knowledgeApi = {
  search: (query: string, equipmentId?: string) =>
    apiClient.post('/knowledge/search', {
      query,
      equipment_id: equipmentId,
    }),
};
