/**
 * Reports Tab Screen — CivicConnect Mobile
 * Single direct fetch from /api/v1/reports/dashboard — no store dependency.
 */
import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';

import type { Report } from '@src/types';
import { api } from '@src/lib/api';
import { ExecutiveReportCard, getStatusDetails } from '@src/components/ui';

const FILTER_TABS = ['All', 'Open', 'In Progress', 'Resolved'] as const;
type FilterTab = (typeof FILTER_TABS)[number];

function normalizeReport(r: any): Report {
  const photosList = r.photos ?? r.images ?? [];
  const normalizedImages = photosList.map((p: any, idx: number) => {
    if (typeof p === 'string') {
      return { id: `photo-${idx}`, url: p };
    }
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

export default function ReportsScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();

  const [filter, setFilter] = useState<FilterTab>('All');
  const [refreshing, setRefreshing] = useState(false);
  const [reports, setReports] = useState<Report[]>([]);
  const [activeCount, setActiveCount] = useState(0);
  const [resolvedCount, setResolvedCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchReports = useCallback(async () => {
    setError(null);
    try {
      // Fetch only this user's own reports
      const res = await api.get<any>('/api/v1/reports/?mine_only=true');
      const rawList: any[] = Array.isArray(res) ? res : [];

      const normalized = rawList.map(normalizeReport);
      setReports(normalized);

      setActiveCount(
        normalized.filter((r) => {
          const g = getStatusDetails(r.status).group;
          return g === 'Open' || g === 'In Progress';
        }).length,
      );
      setResolvedCount(
        normalized.filter((r) => getStatusDetails(r.status).group === 'Resolved').length,
      );
    } catch (err: any) {
      setError(err?.message ?? 'Failed to load reports');

    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  const handleRefresh = useCallback(() => {
    setRefreshing(true);
    fetchReports();
  }, [fetchReports]);

  const filteredReports = reports.filter((r) => {
    const info = getStatusDetails(r.status);
    if (filter === 'All') return true;
    if (filter === 'Open') return info.group === 'Open';
    if (filter === 'In Progress') return info.group === 'In Progress';
    if (filter === 'Resolved') return info.group === 'Resolved';
    return true;
  });

  return (
    <View style={styles.screen}>
      {/* Header */}
      <View style={[styles.headerContainer, { paddingTop: Math.max(insets.top + 6, 40) }]}>
        <View>
          <Text style={styles.kickerText}>MY REPORTS</Text>
          <Text style={styles.headerTitle}>Your Reports</Text>
        </View>

        <View style={styles.statsCapsules}>
          <View style={[styles.statCapsule, { backgroundColor: '#FEF2F2', borderColor: '#FCA5A5' }]}>
            <Text style={[styles.statVal, { color: '#DC2626' }]}>{activeCount}</Text>
            <Text style={styles.statLbl}>Active</Text>
          </View>
          <View style={[styles.statCapsule, { backgroundColor: '#ECFDF5', borderColor: '#A7F3D0' }]}>
            <Text style={[styles.statVal, { color: '#059669' }]}>{resolvedCount}</Text>
            <Text style={styles.statLbl}>Fixed</Text>
          </View>
        </View>
      </View>

      {/* Segmented Filter Bar */}
      <View style={styles.filterBarContainer}>
        <View style={styles.filterSegment}>
          {FILTER_TABS.map((tab) => {
            const active = tab === filter;
            return (
              <TouchableOpacity
                key={tab}
                activeOpacity={0.8}
                style={[styles.filterTabButton, active && styles.filterTabActive]}
                onPress={() => {
                  Haptics.selectionAsync();
                  setFilter(tab);
                }}
              >
                <Text style={[styles.filterTabText, active && styles.filterTextActive]}>
                  {tab}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {/* Reports List */}
      {loading ? (
        <View style={styles.loadingArea}>
          <ActivityIndicator size="large" color="#059669" />
          <Text style={styles.loadingText}>Loading reports...</Text>
        </View>
      ) : error ? (
        <View style={styles.errorContainer}>
          <Ionicons name="cloud-offline-outline" size={36} color="#DC2626" />
          <Text style={styles.errorTitle}>Could not load reports</Text>
          <Text style={styles.errorSub}>{error}</Text>
          <TouchableOpacity style={styles.retryBtn} onPress={fetchReports}>
            <Text style={styles.retryBtnText}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={filteredReports}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listPadding}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={handleRefresh}
              tintColor="#059669"
            />
          }
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <View style={styles.emptyIconCircle}>
                <Ionicons name="documents-outline" size={28} color="#059669" />
              </View>
              <Text style={styles.emptyTitle}>{filter === 'All' ? "You haven't filed any reports yet" : `No ${filter.toLowerCase()} reports`}</Text>
              <Text style={styles.emptySub}>
                Tap the camera button to report a civic issue in your area.
              </Text>
            </View>
          }
          renderItem={({ item, index }) => (
            <ExecutiveReportCard
              report={item}
              index={index}
              onPress={() => router.push({ pathname: '/report-details', params: { id: item.id } })}
            />
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  headerContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingBottom: 14,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  kickerText: {
    fontSize: 9,
    fontWeight: '700',
    color: '#059669',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#0F172A',
    letterSpacing: -0.4,
  },
  statsCapsules: {
    flexDirection: 'row',
    gap: 8,
  },
  statCapsule: {
    borderRadius: 8,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 4,
    alignItems: 'center',
  },
  statVal: {
    fontSize: 14,
    fontWeight: '700',
  },
  statLbl: {
    fontSize: 9,
    fontWeight: '600',
    color: '#64748B',
  },
  filterBarContainer: {
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  filterSegment: {
    flexDirection: 'row',
    backgroundColor: '#F1F5F9',
    borderRadius: 8,
    padding: 3,
  },
  filterTabButton: {
    flex: 1,
    paddingVertical: 7,
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
  },
  filterTabActive: {
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  filterTabText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#64748B',
  },
  filterTextActive: {
    fontWeight: '700',
    color: '#059669',
  },
  loadingArea: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 13,
    color: '#64748B',
    fontWeight: '500',
  },
  listPadding: {
    paddingHorizontal: 20,
    paddingBottom: 110,
    gap: 12,
    paddingTop: 4,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
    gap: 8,
  },
  emptyIconCircle: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#ECFDF5',
    borderWidth: 1,
    borderColor: '#A7F3D0',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  emptyTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
  },
  emptySub: {
    fontSize: 12,
    color: '#64748B',
    textAlign: 'center',
    maxWidth: 240,
    lineHeight: 17,
  },
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    paddingHorizontal: 32,
  },
  errorTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
  },
  errorSub: {
    fontSize: 12,
    color: '#64748B',
    textAlign: 'center',
    lineHeight: 17,
  },
  retryBtn: {
    marginTop: 8,
    backgroundColor: '#059669',
    borderRadius: 8,
    paddingHorizontal: 24,
    paddingVertical: 10,
  },
  retryBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});