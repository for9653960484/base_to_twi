import { apiClient } from './client';

export interface BrandbookTemplate {
  id: string;
  title: string;
  template_type: string;
  file_path: string;
  file_name: string;
  version: number;
  is_active: boolean;
}

export const brandbookApi = {
  list: (templateType?: string) =>
    apiClient.get<BrandbookTemplate[]>('/brandbook/templates', {
      params: templateType ? { template_type: templateType } : undefined,
    }),

  uploadSafetyTemplate: (file: File) => {
    const form = new FormData();
    form.append('title', 'Шаблон листа техники безопасности');
    form.append('template_type', 'safety_sheet');
    form.append('file', file);
    return apiClient.postForm<BrandbookTemplate>('/brandbook/templates', form);
  },

  sampleUrl: () => {
    const base = apiClient.defaults.baseURL || '/api/v1';
    return `${base}/brandbook/templates/safety-sheet/sample`;
  },

  uploadTechCardTemplate: (file: File) => {
    const form = new FormData();
    form.append('title', 'Шаблон технологической карты');
    form.append('template_type', 'tech_card');
    form.append('file', file);
    return apiClient.postForm<BrandbookTemplate>('/brandbook/templates', form);
  },

  techCardSampleUrl: () => {
    const base = apiClient.defaults.baseURL || '/api/v1';
    return `${base}/brandbook/templates/tech-card/sample`;
  },
};
