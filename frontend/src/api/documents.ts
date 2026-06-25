import { apiClient } from './client';
import type { Document, PaginatedResponse } from '@/types';

export const documentsApi = {
  list: (params?: {
    page?: number;
    equipment_id?: string;
    status?: string;
    search?: string;
  }) => apiClient.get<PaginatedResponse<Document>>('/documents', { params }),

  get: (id: string) => apiClient.get<Document>(`/documents/${id}`),

  upload: (formData: FormData) => apiClient.post<Document>('/documents/upload', formData),

  uploadVersion: (id: string, formData: FormData) =>
    apiClient.post<Document>(`/documents/${id}/versions`, formData),

  downloadUrl: (id: string) => {
    const base = apiClient.defaults.baseURL || '/api/v1';
    return `${base}/documents/${id}/download`;
  },

  submit: (id: string) => apiClient.post(`/documents/${id}/submit`),

  approve: (id: string) => apiClient.post(`/documents/${id}/approve`),

  archive: (id: string) => apiClient.post(`/documents/${id}/archive`),

  startAiProcess: (id: string, force = false) =>
    apiClient.post(`/documents/${id}/ai-process`, { force_reprocess: force }),

  getAiStatus: (id: string) => apiClient.get(`/documents/${id}/ai-status`),
};
