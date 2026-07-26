/**
 * Dashboard — CivicConnect
 *
 * Reads exclusively from useDashboardStore → Real Backend API.
 * Zero hardcoded data. All display tokens come from @src/constants/tokens.ts.
 */
import { useEffect } from 'react';
import { View, ScrollView, RefreshControl } from 'react-native';
import { useRouter } from 'expo-router';
import { tokens }             from '@src/constants';
import {
  Masthead,
  TrendingStrip,
  SectionDivider,
  FeaturedCard,
  ReportRow,
  LoadingState,
  ErrorState,
  EmptyState,
  FAB,
} from '@src/components/ui';
import { useDashboardStore }  from '@src/store';
import type { Report }        from '@src/types';

// ─── Screen ──────────────────────────────────────────────────────────────────

export default function DashboardScreen() {
  const router = useRouter();
  const { stats, reports, trending, isLoading, isRefreshing, error, fetchDashboard, refresh } =
    useDashboardStore();

  useEffect(() => { fetchDashboard(); }, []);

  const handleRefresh      = () => refresh();
  const handleCreateReport = () => { router.push('/camera'); };
  const handleViewReport   = (id: string) => { router.push({ pathname: '/report-details', params: { id } }); };

  if (isLoading && !stats) return <LoadingState />;
  if (error && !stats)     return <ErrorState message={error} onRetry={fetchDashboard} />;

  // Featured report = first item, rest go to compact list
  const [featured, ...rest] = reports;
  const reportCount = reports.length;

  return (
    <View style={{ flex: 1, backgroundColor: tokens.surface.bg }}>
      <ScrollView
        style={{ flex: 1 }}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor={tokens.primary.DEFAULT}
            colors={['#065f46']}
          />
        }
      >
        {/* Masthead */}
        <Masthead stats={stats} />

        {/* Trending categories */}
        <TrendingStrip trending={trending} />

        {/* Report feed */}
        <SectionDivider
          label={reportCount > 0 ? `Recent Reports · ${reportCount}` : 'Recent Reports'}
        />

        {reportCount === 0 ? (
          <EmptyState onReport={handleCreateReport} />
        ) : (
          <>
            {/* Large featured card — first report */}
            {featured && <FeaturedCard report={featured} onPress={() => handleViewReport(featured.id)} />}

            {/* Compact list — remaining reports */}
            {rest.map((r: Report) => (
              <ReportRow key={r.id} report={r} onPress={() => handleViewReport(r.id)} />
            ))}

            <View style={{ height: 90 }} />
          </>
        )}
      </ScrollView>

      <FAB onPress={handleCreateReport} />
    </View>
  );
}