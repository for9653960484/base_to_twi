import { apiClient } from './client';
import type { PaginatedResponse, TechCard } from '@/types';

export const techCardsApi = {
  list: (params?: {
    page?: number;
    page_size?: number;
    equipment_id?: string;
    maintenance_type?: string;
    status?: string;
  }) => apiClient.get<PaginatedResponse<TechCard>>('/tech-cards/', { params }),

  get: (id: string) => apiClient.get<TechCard>(`/tech-cards/${id}`),

  exportPdfUrl: (id: string) => {
    const base = apiClient.defaults.baseURL || '/api/v1';
    return `${base}/tech-cards/export/${id}?format=pdf`;
  },

  exportDocxUrl: (id: string) => {
    const base = apiClient.defaults.baseURL || '/api/v1';
    return `${base}/tech-cards/export/${id}?format=docx`;
  },

  uploadEdited: (id: string, file: File) => {
    const form = new FormData();
    form.append('file', file);
    return apiClient.postForm<TechCard>(`/tech-cards/${id}/edited-file`, form);
  },

  formPdf: (id: string) =>
    apiClient.post<Blob>(`/tech-cards/${id}/form-pdf`, null, { responseType: 'blob' }),
};
