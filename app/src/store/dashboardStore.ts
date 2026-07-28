/**
 * Dashboard store.
 *
 * Data source: Real backend API at EXPO_PUBLIC_API_URL/api/v1/reports/dashboard
 * Zero hardcoded data. Zero mock placeholders.
 *
 * To swap in real API: this file is the only place to change.
 */
import { create } from 'zustand';
import type { Report, DashboardStats, TrendingCategory } from '@src/types';
import { api } from '@src/lib/api';

interface DashboardResponse {
  stats?: DashboardStats;
  recentReports?: Report[];
  trending?: TrendingCategory[];
}

interface DashboardState {
  stats:        DashboardStats | null;
  reports:      Report[];
  trending:     TrendingCategory[];
  isLoading:    boolean;
  isRefreshing: boolean;
  error:        string | null;
  lastFetched:  number | null;

  /** Load dashboard stats + recent reports from the backend. */
  fetchDashboard: () => Promise<void>;

  /** Pull-to-refresh — keeps existing data visible while refreshing. */
  refresh: () => Promise<void>;
}

export const useDashboardStore = create<DashboardState>((set, get) => ({
  stats:        null,
  reports:      [],
  trending:     [],
  isLoading:    false,
  isRefreshing: false,
  error:        null,
  lastFetched:  null,

  fetchDashboard: async () => {
    if (get().isLoading) return;
    set({ isLoading: true, error: null });

    try {
      const data = await api.get<DashboardResponse>('/api/v1/reports/dashboard');

      set({
        stats:       data.stats ?? null,
        reports:     data.recentReports ?? [],
        trending:    data.trending ?? [],
        isLoading:   false,
        lastFetched: Date.now(),
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load dashboard';
      set({ isLoading: false, error: message });
    }
  },

  refresh: async () => {
    set({ isRefreshing: true, error: null });

    try {
      const data = await api.get<DashboardResponse>('/api/v1/reports/dashboard');

      set({
        stats:        data.stats ?? get().stats ?? null,
        reports:      data.recentReports ?? get().reports ?? [],
        trending:     data.trending ?? get().trending ?? [],
        isRefreshing: false,
        lastFetched:  Date.now(),
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Refresh failed';
      set({ isRefreshing: false, error: message });
    }
  },
}));