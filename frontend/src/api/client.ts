import axios from 'axios';

/**
 * Если в сборке/env остался http://localhost:..., а страница открыта
 * с IP/домена сервера — браузер получит Network Error. В этом случае
 * используем same-origin /api/v1 (Vite proxy → backend).
 */
function resolveApiBase(): string {
  const configured = (import.meta.env.VITE_API_BASE_URL as string | undefined) || '/api/v1';
  if (typeof window === 'undefined') {
    return configured;
  }
  const pointsToLoopback = /^(https?:\/\/)?(localhost|127\.0\.0\.1)(:|\/|$)/i.test(configured);
  const pageIsRemote = !/^(localhost|127\.0\.0\.1)$/i.test(window.location.hostname);
  if (pointsToLoopback && pageIsRemote) {
    return '/api/v1';
  }
  return configured;
}

export const apiClient = axios.create({
  baseURL: resolveApiBase(),
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  const lang = localStorage.getItem('locale') || 'ru';
  config.headers['Accept-Language'] = lang;
  // FormData: браузер сам выставит multipart boundary
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type'];
  }
  return config;
});
