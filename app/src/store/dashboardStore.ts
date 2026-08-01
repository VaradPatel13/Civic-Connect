
import { create } from 'zustand';
import type { Report, DashboardStats, TrendingCategory } from '@src/types';
import { api, ApiError } from '@src/lib/api';

interface DashboardResponse {
  stats?: DashboardStats;
  recentReports?: any[];
  trending?: TrendingCategory[];
}

/** Normalize a raw API report (snake_case or camelCase) to frontend Report shape */
function normalizeReport(r: any): Report {
  const photosList = r.photos ?? r.images ?? [];
  const normalizedImages = photosList.map((p: any, idx: number) => {
    if (typeof p === 'string') return { id: `photo-${idx}`, url: p };
    return {
      id: p.id ? String(p.id) : `photo-${idx}`,
      url: p.url || p.cloudinary_url || p.secure_url || '',
      display_order: p.display_order ?? idx,
      forensic_score: p.forensic_score ?? null,
      is_authentic: p.is_authentic ?? null,
    };
  });

  return {
    id: String(r.id),
    title: r.title || 'Untitled Report',
    description: r.description || '',
    category: String(r.category || r.issue_category || 'other').toLowerCase() as any,
    status: String(r.status || 'open').toLowerCase() as any,
    location: {
      lat: r.location?.lat ?? r.latitude ?? 0,
      lng: r.location?.lng ?? r.longitude ?? 0,
      address: r.location?.address ?? r.address ?? '',
    },
    images: normalizedImages,
    authorId: String(r.authorId ?? r.citizen_id ?? ''),
    authorName: r.authorName ?? '',
    upvotes: r.upvotes ?? 0,
    commentCount: r.commentCount ?? 0,
    isUpvoted: Boolean(r.isUpvoted),
    createdAt: r.createdAt ?? r.created_at ?? new Date().toISOString(),
    updatedAt: r.updatedAt ?? r.updated_at ?? new Date().toISOString(),
  };
}

interface DashboardState {
  stats:        DashboardStats | null;
  reports:      Report[];         // ALL community reports (for dashboard feed)
  trending:     TrendingCategory[];
  isLoading:    boolean;
  isRefreshing: boolean;
  error:        string | null;
  lastFetched:  number | null;

  /** Load dashboard stats + ALL community reports from backend */
  fetchDashboard: () => Promise<void>;

  /** Pull-to-refresh — keeps existing data visible while refreshing */
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
      // Step 1: fetch dashboard stats + recent reports
      const data = await api.get<DashboardResponse>('/api/v1/reports/dashboard');

      // Step 2: also fetch full report list (all community reports, not mine_only)
      let allReports: Report[] = (data.recentReports ?? []).map(normalizeReport);
      try {
        const listRes = await api.get<any>('/api/v1/reports/');
        if (Array.isArray(listRes) && listRes.length > 0) {
          allReports = listRes.map(normalizeReport);
        }
      } catch {
        // Keep dashboard recentReports as fallback
      }

      set({
        stats:       data.stats ?? null,
        reports:     allReports,
        trending:    data.trending ?? [],
        isLoading:   false,
        lastFetched: Date.now(),
        error:       null,
      });
    } catch (err) {
      const isAuthError = err instanceof ApiError && err.status === 401;
      const message = isAuthError
        ? 'Session expired. Please log in again.'
        : err instanceof Error ? err.message : 'Failed to load dashboard';
      set((state) => ({
        isLoading: false,
        error: message,
        stats: state.stats,
        reports: state.reports,
        trending: state.trending,
      }));
    }
  },

  refresh: async () => {
    set({ isRefreshing: true, error: null });

    try {
      const data = await api.get<DashboardResponse>('/api/v1/reports/dashboard');

      let allReports: Report[] = (data.recentReports ?? []).map(normalizeReport);
      try {
        const listRes = await api.get<any>('/api/v1/reports/');
        if (Array.isArray(listRes) && listRes.length > 0) {
          allReports = listRes.map(normalizeReport);
        }
      } catch {
        // Keep dashboard data
      }

      set({
        stats:        data.stats ?? get().stats ?? null,
        reports:      allReports.length > 0 ? allReports : get().reports,
        trending:     data.trending ?? get().trending ?? [],
        isRefreshing: false,
        lastFetched:  Date.now(),
        error:        null,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Refresh failed';
      set({ isRefreshing: false, error: message });
    }
  },
}));