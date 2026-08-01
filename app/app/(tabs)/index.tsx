/**
 * Home / Dashboard Screen — CivicConnect Mobile
 */
import { useCallback, useEffect, useState } from 'react';
import {
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useRouter } from 'expo-router';

import {
  EmptyState,
  ErrorState,
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

const ITEMS_PER_PAGE = 10;

export default function DashboardScreen() {
  const router = useRouter();

  const { reports, isLoading, error, fetchDashboard } = useDashboardStore();
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
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

  const handleCategorySelect = (category: string | null) => {
    setSelectedCategory(category);
    setCurrentPage(1);
  };

  const filteredReports = reports.filter((r) => {
    if (!selectedCategory) return true;
    return (r.category || '').toLowerCase().includes(selectedCategory.toLowerCase());
  });

  const totalPages = Math.max(1, Math.ceil(filteredReports.length / ITEMS_PER_PAGE));
  const validCurrentPage = Math.min(currentPage, totalPages);

  const startIndex = (validCurrentPage - 1) * ITEMS_PER_PAGE;
  const paginatedReports = filteredReports.slice(startIndex, startIndex + ITEMS_PER_PAGE);

  const isFirstPage = validCurrentPage === 1;
  const featured = isFirstPage ? paginatedReports[0] : null;
  const rest = isFirstPage ? paginatedReports.slice(1) : paginatedReports;

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
          onSelectCategory={handleCategorySelect}
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

              {totalPages > 1 && (
                <View style={styles.paginationRow}>
                  <TouchableOpacity
                    disabled={validCurrentPage === 1}
                    style={[
                      styles.pageBtn,
                      validCurrentPage === 1 && styles.pageBtnDisabled,
                    ]}
                    onPress={() => {
                      Haptics.selectionAsync();
                      setCurrentPage((prev) => Math.max(1, prev - 1));
                    }}
                  >
                    <Ionicons
                      name="chevron-back"
                      size={16}
                      color={validCurrentPage === 1 ? '#94A3B8' : '#0F172A'}
                    />
                    <Text
                      style={[
                        styles.pageBtnText,
                        validCurrentPage === 1 && styles.pageBtnTextDisabled,
                      ]}
                    >
                      Previous
                    </Text>
                  </TouchableOpacity>

                  <Text style={styles.pageInfoText}>
                    Page {validCurrentPage} of {totalPages}
                  </Text>

                  <TouchableOpacity
                    disabled={validCurrentPage === totalPages}
                    style={[
                      styles.pageBtn,
                      validCurrentPage === totalPages && styles.pageBtnDisabled,
                    ]}
                    onPress={() => {
                      Haptics.selectionAsync();
                      setCurrentPage((prev) => Math.min(totalPages, prev + 1));
                    }}
                  >
                    <Text
                      style={[
                        styles.pageBtnText,
                        validCurrentPage === totalPages && styles.pageBtnTextDisabled,
                      ]}
                    >
                      Next
                    </Text>
                    <Ionicons
                      name="chevron-forward"
                      size={16}
                      color={validCurrentPage === totalPages ? '#94A3B8' : '#0F172A'}
                    />
                  </TouchableOpacity>
                </View>
              )}
            </View>
          )}
        </View>
      </ScrollView>
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
  paginationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 8,
    paddingHorizontal: 4,
  },
  pageBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  pageBtnDisabled: {
    backgroundColor: '#F1F5F9',
    borderColor: '#E2E8F0',
  },
  pageBtnText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#0F172A',
  },
  pageBtnTextDisabled: {
    color: '#94A3B8',
  },
  pageInfoText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#475569',
  },
});