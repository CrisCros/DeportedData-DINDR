export type DashboardKpis = {
  empleo_total: number;
  growth_pct: number;
  latest_year: number;
  latest_values: Array<{ year: number; empleo: number }>;
};

export type DashboardSeries = {
  years: number[];
  values: number[];
};

function resolveApiBaseUrl() {
  const configuredUrl = import.meta.env.VITE_API_BASE_URL;

  if (configuredUrl && configuredUrl.trim().length > 0) {
    return configuredUrl.replace(/\/$/, '');
  }

  // En Vercel frontend usamos /api con rewrite a backend para evitar CORS.
  return '/api';
}

const API_BASE_URL = resolveApiBaseUrl();

async function apiRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const needsJsonHeader = options?.body !== undefined;

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(needsJsonHeader ? { 'Content-Type': 'application/json' } : {}),
      ...(options?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Error ${response.status}: ${errorBody}`);
  }

  return response.json() as Promise<T>;
}

export const dashboardApi = {
  getKpis: () => apiRequest<DashboardKpis>('/dashboard/kpis'),
  getSeries: () => apiRequest<DashboardSeries>('/dashboard/series'),
};

export const chatApi = {
  sendMessage: (message: string) =>
    apiRequest<{ answer: string; message: string }>('/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    }),
};
