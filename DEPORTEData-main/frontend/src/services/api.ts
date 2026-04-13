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

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function apiRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers ?? {}),
    },
    ...options,
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
  sendMessage: (message: string) => apiRequest<{ answer: string; message: string }>('/chat', {
    method: 'POST',
    body: JSON.stringify({ message }),
  }),
};
