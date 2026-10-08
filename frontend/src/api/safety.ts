import { apiClient } from './client';
import type { PaginatedResponse, PpeItem, SafetyGenerateStatus, SafetySheet, WorkConditions } from '@/types';

export interface SafetySheetUpdate {
  title: string;
  equipment_id: string;
  ppe: PpeItem[];
  work_conditions: WorkConditions;
  notes: string | null;
}

export const safetyApi = {
  list: (params?: { page?: number; page_size?: number; equipment_id?: string }) =>
    apiClient.get<PaginatedResponse<SafetySheet>>('/safety/', { params }),

  generate: (documentId: string) =>
    apiClient.post<SafetyGenerateStatus>('/safety/generate', { document_id: documentId }),

  generationStatus: (documentId: string) =>
    apiClient.get<SafetyGenerateStatus>(`/safety/generate/${documentId}/status`),

  update: (id: string, data: SafetySheetUpdate) =>
    apiClient.patch<SafetySheet>(`/safety/${id}`, data),

  exportPdfUrl: (id: string) => {
    const base = apiClient.defaults.baseURL || '/api/v1';
    return `${base}/safety/export/${id}`;
  },
};
