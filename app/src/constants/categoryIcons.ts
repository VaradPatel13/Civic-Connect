import type { ReportCategory } from '@src/types';

/**
 * Maps ReportCategory slugs → Ionicons icon name.
 * Shared across FeaturedCard, ReportRow, and any other category-dot components.
 */
export const CATEGORY_ICON: Record<ReportCategory, string> = {
  pothole:     'alert-circle',
  streetlight: 'flash',
  drainage:    'water',
  water:       'water-outline',
  sanitation:  'trash',
  traffic:     'trail-sign',
  noise:       'volume-high',
  other:       'location',
};