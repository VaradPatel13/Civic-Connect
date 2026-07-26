// ─── Domain types — mirrors what the backend API returns. ───────────────────
// These are NOT hardcoded in UI components. Components consume these from
// the store or API layer. Only the type definitions live here.

export type ReportStatus = 'open' | 'pending' | 'processing' | 'verified' | 'assigned' | 'in_progress' | 'resolved' | 'closed' | 'rejected';
export type ReportCategory =
  | 'pothole'   | 'streetlight' | 'drainage'     | 'water'
  | 'sanitation'| 'traffic'     | 'noise'        | 'other';

export interface GeoLocation {
  lat: number;
  lng: number;
  address?: string;
}

export interface ReportImage {
  id: string;
  url: string;
  thumbnailUrl?: string;
  display_order?: number;
  forensic_score?: number;
  is_authentic?: boolean;
}

export interface Report {
  id: string;
  title: string;
  description: string;
  category: ReportCategory;
  status: ReportStatus;
  location: GeoLocation;
  images: ReportImage[];
  authorId: string;
  authorName: string;
  upvotes: number;
  commentCount: number;
  isUpvoted: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface DashboardStats {
  totalReports: number;
  openReports: number;
  resolvedThisMonth: number;
  avgResolutionDays: number;
  myReports: number;
}

export interface TrendingCategory {
  label: string;
  icon:  keyof typeof import('@expo/vector-icons').Ionicons.glyphMap;
  count: number;
}

export interface DashboardData {
  stats: DashboardStats;
  recentReports: Report[];
  trending: TrendingCategory[];
}