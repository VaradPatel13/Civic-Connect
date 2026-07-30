/**
 * Report domain types aligned with backend API schemas.
 * Consumed by camera → create-report → submit-success flow.
 */
import type { ReportCategory } from '@src/types/dashboard';

export { type ReportCategory } from '@src/types/dashboard';

// ── Backend IssueCategory ← mobile slug mapping ──────────────────────────────
export const ISSUE_CATEGORY_SLUGS = [
  { slug: 'roads',                   label: 'Roads & Potholes',    icon: 'alert-circle'    } as const,
  { slug: 'street_lighting',          label: 'Streetlight',          icon: 'flash'          } as const,
  { slug: 'drainage',                 label: 'Drainage',             icon: 'water'          } as const,
  { slug: 'water_supply',             label: 'Water Supply',         icon: 'water-outline'  } as const,
  { slug: 'waste_management',         label: 'Sanitation',           icon: 'trash'          } as const,
  { slug: 'traffic_infrastructure',  label: 'Traffic Infra',        icon: 'trail-sign'     } as const,
  { slug: 'public_health',           label: 'Public Health',         icon: 'medkit'         } as const,
  { slug: 'parks',                   label: 'Parks & Green',         icon: 'leaf'           } as const,
  { slug: 'encroachment',            label: 'Encroachment',         icon: 'resize'         } as const,
  { slug: 'other',                   label: 'Other',                 icon: 'location'       } as const,
] as const;

export type IssueCategorySlug = typeof ISSUE_CATEGORY_SLUGS[number]['slug'];

export const ISSUE_CATEGORY_MAP = Object.fromEntries(
  ISSUE_CATEGORY_SLUGS.map(c => [c.slug, c]),
) as Record<IssueCategorySlug, typeof ISSUE_CATEGORY_SLUGS[number]>;

// ── Uploaded asset returned by POST /api/v1/uploads ─────────────────────────
export interface UploadAsset {
  url:        string;
  secure_url: string;
  public_id:  string;
  format:     string;
  width:      number | null;
  height:     number | null;
}

// ── PhotoMetadata payload (sent to backend) ────────────────────────────────────
export interface PhotoMetadata {
  url:             string;
  capture_source:  'camera' | 'gallery';
  latitude?:       number;
  longitude?:      number;
  gps_accuracy_m?: number;
  captured_at?:    string;
  sha256_hash?:    string;
  hmac_signature?: string;
  device_model?:   string;
  os_version?:     string;
  app_version?:    string;
}

// ── CreateReport payload (sent to backend) ───────────────────────────────────
export interface CreateReportPayload {
  title:          string;
  description:    string;
  issue_category: IssueCategorySlug;
  latitude:       number;
  longitude:      number;
  address:        string;
  photos:         string[];   // Cloudinary secure URLs
  photo_metadata?: PhotoMetadata[];
  language:       string;
}

// ── Backend response after successful submission ───────────────────────────────
export interface SubmittedReport {
  id:             string;
  title:          string;
  description:    string;
  issue_category: IssueCategorySlug;
  status:         string;
  latitude:       number;
  longitude:      number;
  address:        string;
  created_at:     string;
  ward:           string | null;
  zone:           string | null;
  photos:         { url: string; secure_url: string }[];
}