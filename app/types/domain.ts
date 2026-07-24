export type IssueCategory = 'roads' | 'water' | 'garbage' | 'electricity' | 'sewage' | 'parks' | 'traffic' | 'other';

export type UrgencyLevel = 'low' | 'medium' | 'high' | 'critical';

export type ReportStatus = 'pending' | 'triaged' | 'assigned' | 'in_progress' | 'resolved' | 'rejected';

export interface CitizenUser {
  id: string;
  display_name: string;
  phone: string;
  email?: string | null;
  preferred_language: 'en' | 'hi' | 'mr';
  points: number;
  is_active: boolean;
  is_verified: boolean;
  role: string;
  created_at: string;
}

export interface PhotoItem {
  id: string;
  cloudinary_url: string;
  caption?: string;
  created_at: string;
}

export interface StatusLogItem {
  id: string;
  from_status?: ReportStatus | null;
  to_status: ReportStatus;
  changed_by: string;
  reason?: string;
  created_at: string;
}

export interface ReportItem {
  id: string;
  citizen_id: string;
  title: string;
  description: string;
  issue_category: IssueCategory;
  urgency: UrgencyLevel;
  status: ReportStatus;
  latitude?: number | null;
  longitude?: number | null;
  address?: string | null;
  language: string;
  ai_priority_score?: number;
  ai_summary?: string;
  ai_duplicate_of_id?: string;
  photos: PhotoItem[];
  status_logs: StatusLogItem[];
  created_at: string;
  updated_at: string;
}

export interface DepartmentItem {
  id: string;
  name: string;
  code: string;
  description?: string;
  head_name?: string;
  contact_email?: string;
  contact_phone?: string;
  is_active: boolean;
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
}

export interface RewardsSummary {
  total_points: number;
  tier: string;
}
