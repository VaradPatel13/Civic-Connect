/**
 * Mock API — ONLY for development / demo.
 *
 * Components do NOT import from here. The store does.
 * To go to production: swap the import inside dashboardStore.ts fetchDashboard.
 *
 * Delete this file when your backend is available.
 */
import type { DashboardData } from '@src/types';

export async function fetchDashboard(): Promise<DashboardData> {
  await new Promise((resolve) => setTimeout(resolve, 600));

  return {
    stats: {
      totalReports: 47,
      openReports: 12,
      resolvedThisMonth: 28,
      avgResolutionDays: 4.2,
      myReports: 5,
    },
    recentReports: [
      {
        id: '1',
        title: 'Large pothole near FC Road junction',
        description: 'Dangerous pothole causing traffic slowdowns after rain.',
        category: 'pothole',
        status: 'open',
        location: { lat: 18.5167, lng: 73.8563, address: 'FC Road, Shivajinagar, Pune' },
        images: [],
        authorId: 'u1',
        authorName: 'Rahul M.',
        upvotes: 14,
        commentCount: 3,
        isUpvoted: false,
        createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        updatedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      },
    ],
    trending: [{ label: 'Water Supply', icon: 'water', count: 12 }],
  };
}