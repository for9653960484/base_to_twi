import { apiClient } from './client';
import type { Document, PaginatedResponse } from '@/types';

export const documentsApi = {
  list: (params?: {
    page?: number;
    equipment_id?: string;
    status?: string;
    search?: string;
  }) => apiClient.get<PaginatedResponse<Document>>('/documents/', { params }),

  get: (id: string) => apiClient.get<Document>(`/documents/${id}`),

  upload: (formData: FormData) =>
    apiClient.postForm<Document>('/documents/upload', formData, { timeout: 600_000 }),

  uploadVersion: (id: string, formData: FormData) =>
    apiClient.postForm<Document>(`/documents/${id}/versions`, formData, { timeout: 600_000 }),

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

  generateTechCards: (id: string) =>
    apiClient.post(`/documents/${id}/generate-tech-cards`),

  getTechCardsGenerationStatus: (id: string) =>
    apiClient.get(`/documents/${id}/generate-tech-cards/status`),
};
