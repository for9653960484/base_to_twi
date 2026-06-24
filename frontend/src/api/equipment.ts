import { apiClient } from './client';
import type { Equipment, PaginatedResponse } from '@/types';

export const equipmentApi = {
  list: (params?: { page?: number; page_size?: number; search?: string; is_active?: boolean }) =>
    apiClient.get<PaginatedResponse<Equipment>>('/equipment', { params }),

  get: (id: string) => apiClient.get<Equipment>(`/equipment/${id}`),

  getRelations: (id: string) => apiClient.get(`/equipment/${id}/relations`),

  create: (data: { name: string; serial_name?: string; description?: string }) =>
    apiClient.post<Equipment>('/equipment', data),

  update: (id: string, data: Partial<Equipment>) =>
    apiClient.patch<Equipment>(`/equipment/${id}`, data),
};
