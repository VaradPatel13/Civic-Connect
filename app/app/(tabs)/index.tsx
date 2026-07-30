/**
 * Home / Dashboard Screen — CivicConnect Mobile
 * Clean, production-grade interface built with modular dashboard components.
 */
import { useCallback, useEffect, useState } from 'react';
import {
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';

import {
  EmptyState,
  ErrorState,
  FAB,
  FeaturedCard,
  ReportRow,
} from '@src/components/ui';
import {
  AnnouncementCarousel,
  CategoryChips,
  DashboardHeader,
  LocationCard,
  StatsOverview,
} from '@src/components/dashboard';
import { useDashboardStore } from '@src/store';
import type { Report } from '@src/types';
import { getCurrentLocation, DeviceLocation } from '@src/lib/location';

export default function DashboardScreen() {
  const router = useRouter();

  const { reports, isLoading, error, fetchDashboard } = useDashboardStore();
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [deviceLoc, setDeviceLoc] = useState<DeviceLocation | null>(null);
  const [loadingLoc, setLoadingLoc] = useState(false);

  const loadLocation = useCallback(async () => {
    setLoadingLoc(true);
    const loc = await getCurrentLocation();
    setDeviceLoc(loc);
    setLoadingLoc(false);
  }, []);

  useEffect(() => {
    fetchDashboard();
    loadLocation();
  }, [fetchDashboard, loadLocation]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await Promise.all([fetchDashboard(), loadLocation()]);
    setRefreshing(false);
  }, [fetchDashboard, loadLocation]);

  const filteredReports = reports.filter((r) => {
    if (!selectedCategory) return true;
    return (r.category || '').toLowerCase().includes(selectedCategory.toLowerCase());
  });

  const featured = filteredReports[0];
  const rest = filteredReports.slice(1);

  const handleViewReport = (id: string) => {
    router.push({ pathname: '/report-details', params: { id } });
  };

  return (
    <View style={styles.screen}>
      {/* 1. Header */}
      <DashboardHeader
        onNotificationPress={() => router.push('/notifications')}
      />

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor="#059669"
          />
        }
      >
        {/* 2. Announcement Carousel */}
        <AnnouncementCarousel />

        {/* 3. Real-Time Location Card */}
        <LocationCard
          location={deviceLoc}
          loading={loadingLoc}
          onRefresh={loadLocation}
        />

        {/* 4. District Overview */}
        <StatsOverview />

        {/* 5. Trending Categories */}
        <CategoryChips
          selectedCategory={selectedCategory}
          onSelectCategory={setSelectedCategory}
        />

        {/* 6. Recent Nearby Reports */}
        <View style={styles.feedSection}>
          <View style={styles.feedHeaderRow}>
            <Text style={styles.sectionTitle}>Recent Nearby Reports</Text>
            <Text style={styles.feedCountText}>{filteredReports.length} Reports</Text>
          </View>

          {isLoading && reports.length === 0 ? (
            <View style={styles.skelStack}>
              <View style={styles.skelCard} />
              <View style={styles.skelCard} />
            </View>
          ) : error && reports.length === 0 ? (
            <ErrorState message={error} onRetry={fetchDashboard} />
          ) : filteredReports.length === 0 ? (
            <EmptyState onReport={() => router.push('/camera')} />
          ) : (
            <View style={styles.reportsList}>
              {featured && (
                <FeaturedCard
                  report={featured}
                  onPress={() => handleViewReport(featured.id)}
                />
              )}
              {rest.map((r: Report) => (
                <ReportRow
                  key={r.id}
                  report={r}
                  onPress={() => handleViewReport(r.id)}
                />
              ))}
            </View>
          )}
        </View>
      </ScrollView>

      {/* Floating Action Button (Cleanly positioned above tab bar) */}
      <FAB onPress={() => router.push('/camera')} />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingTop: 16,
    paddingHorizontal: 20,
    paddingBottom: 110,
    gap: 20,
  },
  feedSection: {
    gap: 12,
  },
  feedHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
    letterSpacing: -0.3,
  },
  feedCountText: {
    fontSize: 12,
    color: '#64748B',
    fontWeight: '500',
  },
  reportsList: {
    gap: 12,
  },
  skelStack: {
    gap: 12,
  },
  skelCard: {
    height: 96,
    backgroundColor: '#E2E8F0',
    borderRadius: 12,
  },
});