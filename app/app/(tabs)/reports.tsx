import { useEffect, useState, useCallback, useRef } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Image,
  StyleSheet,
  useColorScheme,
  Animated,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { TOKENS } from '@src/theme/tokens';
import type { Report } from '@src/types';
import { api } from '@src/lib/api';
import { FAB } from '@src/components/ui';

const CATEGORY_ICON: Record<string, string> = {
  roads: 'alert-circle',
  pothole: 'alert-circle',
  street_lighting: 'flash',
  streetlight: 'flash',
  drainage: 'water',
  water_supply: 'water-outline',
  waste_management: 'trash',
  traffic: 'trail-sign',
  noise: 'volume-high',
  other: 'location',
};

const FILTER_TABS = ['All', 'Open', 'In Progress', 'Resolved'] as const;
type FilterTab = (typeof FILTER_TABS)[number];

function timeAgo(iso?: string): string {
  if (!iso) return 'Recently';
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function useItemEntrance(index: number) {
  const opacity = useRef(new Animated.Value(0)).current;
  const translateY = useRef(new Animated.Value(10)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(opacity, {
        toValue: 1,
        duration: 300,
        delay: Math.min(index * 50, 300),
        useNativeDriver: true,
      }),
      Animated.spring(translateY, {
        toValue: 0,
        friction: 8,
        tension: 40,
        delay: Math.min(index * 50, 300),
        useNativeDriver: true,
      }),
    ]).start();
  }, [index, opacity, translateY]);

  return { opacity, translateY };
}

function ExecutiveReportCard({
  report,
  index,
  onPress,
  isDark,
}: {
  report: Report;
  index: number;
  onPress: () => void;
  isDark: boolean;
}) {
  const p = isDark ? TOKENS.colors.dark : TOKENS.colors.light;
  const { opacity, translateY } = useItemEntrance(index);
  const [imgError, setImgError] = useState(false);

  const catKey = (report.category || 'other').toLowerCase();
  const iconName = CATEGORY_ICON[catKey] ?? 'location';

  const isResolved = report.status === 'resolved';
  const isInProgress = report.status === 'in_progress' || report.status === 'assigned';
  const statusBg = isResolved ? `${p.accentLime}20` : isInProgress ? `${p.accentCyan}20` : `${p.accentRose}20`;
  const statusColor = isResolved ? p.accentLime : isInProgress ? p.accentCyan : p.accentRose;
  const statusLabel = isResolved ? 'RESOLVED' : isInProgress ? 'IN PROGRESS' : 'OPEN';

  const firstImg = report.images?.[0];
  const imageUrl = typeof firstImg === 'string' ? firstImg : firstImg?.url;

  return (
    <Animated.View style={{ opacity, transform: [{ translateY }] }}>
      <TouchableOpacity
        activeOpacity={0.82}
        style={[styles.cardContainer, { backgroundColor: p.surface, borderColor: p.border }]}
        onPress={onPress}>
        {/* Card Banner Image or Category Pattern */}
        <View style={[styles.cardMediaArea, { backgroundColor: p.pillBg }]}>
          {Boolean(imageUrl) && !imgError ? (
            <Image
              source={{ uri: imageUrl }}
              style={styles.cardImage}
              onError={() => setImgError(true)}
              resizeMode="cover"
            />
          ) : (
            <View style={styles.cardPlaceholderIcon}>
              <Ionicons name={iconName as any} size={32} color={p.accentPrimary} />
            </View>
          )}

          <View style={[styles.statusBadge, { backgroundColor: statusBg }]}>
            <Text style={[styles.statusBadgeText, { color: statusColor }]}>{statusLabel}</Text>
          </View>
        </View>

        {/* Content Details */}
        <View style={styles.cardContent}>
          <Text style={[styles.reportTitle, { color: p.textPrimary }]} numberOfLines={2}>
            {report.title}
          </Text>

          <View style={styles.metaRow}>
            <Ionicons name="location-outline" size={13} color={p.textMuted} />
            <Text style={[styles.locationText, { color: p.textSecondary }]} numberOfLines={1}>
              {report.location?.address ?? 'Shivajinagar, Ward 12'}
            </Text>
            <Text style={[styles.dotSep, { color: p.textMuted }]}>•</Text>
            <Text style={[styles.timeText, { color: p.textMuted }]}>{timeAgo(report.createdAt)}</Text>
          </View>

          <View style={[styles.divider, { backgroundColor: p.border }]} />

          <View style={styles.cardFooter}>
            <View style={styles.counterWrap}>
              <View style={styles.counterItem}>
                <Ionicons name="caret-up-circle-outline" size={16} color={p.accentPrimary} />
                <Text style={[styles.counterText, { color: p.textPrimary }]}>{report.upvotes ?? 0}</Text>
              </View>
              <View style={styles.counterItem}>
                <Ionicons name="chatbubble-ellipses-outline" size={15} color={p.textMuted} />
                <Text style={[styles.counterText, { color: p.textSecondary }]}>{report.commentCount ?? 0}</Text>
              </View>
            </View>

            <Ionicons name="chevron-forward" size={16} color={p.textMuted} />
          </View>
        </View>
      </TouchableOpacity>
    </Animated.View>
  );
}

export default function ReportsScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';
  const p = isDark ? TOKENS.colors.dark : TOKENS.colors.light;

  const [filter, setFilter] = useState<FilterTab>('All');
  const [refreshing, setRefreshing] = useState(false);
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchReports = useCallback(async () => {
    try {
      const data = await api.get<Report[]>('/api/v1/reports/');
      setReports(Array.isArray(data) ? data : []);
    } catch {
      setReports([]);
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
    if (filter === 'All') return true;
    if (filter === 'Open' && (r.status === 'open' || r.status === 'pending')) return true;
    if (filter === 'In Progress' && (r.status === 'in_progress' || r.status === 'assigned')) return true;
    if (filter === 'Resolved' && r.status === 'resolved') return true;
    return false;
  });

  const activeCount = reports.filter((r) => r.status !== 'resolved').length;
  const resolvedCount = reports.filter((r) => r.status === 'resolved').length;

  return (
    <View style={[styles.screen, { backgroundColor: p.bg }]}>
      {/* Asymmetric Header */}
      <View style={styles.headerContainer}>
        <View>
          <Text style={[styles.kickerText, { color: p.accentPrimary }]}>CITIZEN DISPATCH FEED</Text>
          <Text style={[styles.headerTitle, { color: p.textPrimary }]}>District Reports</Text>
        </View>

        <View style={styles.statsCapsules}>
          <View style={[styles.statCapsule, { backgroundColor: `${p.accentRose}15`, borderColor: `${p.accentRose}30` }]}>
            <Text style={[styles.statVal, { color: p.accentRose }]}>{activeCount}</Text>
            <Text style={[styles.statLbl, { color: p.textSecondary }]}>Active</Text>
          </View>
          <View style={[styles.statCapsule, { backgroundColor: `${p.accentLime}15`, borderColor: `${p.accentLime}30` }]}>
            <Text style={[styles.statVal, { color: p.accentLime }]}>{resolvedCount}</Text>
            <Text style={[styles.statLbl, { color: p.textSecondary }]}>Fixed</Text>
          </View>
        </View>
      </View>

      {/* Segmented Filter Bar */}
      <View style={styles.filterBarContainer}>
        <View style={[styles.filterSegment, { backgroundColor: p.pillBg, borderColor: p.border }]}>
          {FILTER_TABS.map((tab) => {
            const active = tab === filter;
            return (
              <TouchableOpacity
                key={tab}
                activeOpacity={0.8}
                style={[
                  styles.filterTabButton,
                  { backgroundColor: active ? p.surface : 'transparent' },
                ]}
                onPress={() => setFilter(tab)}>
                <Text style={[styles.filterTabText, { color: active ? p.accentPrimary : p.textSecondary, fontWeight: active ? '800' : '600' }]}>
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
          <ActivityIndicator size="large" color={p.accentPrimary} />
        </View>
      ) : (
        <FlatList
          data={filteredReports}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listPadding}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} tintColor={p.accentPrimary} />
          }
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <View style={[styles.emptyIconCircle, { backgroundColor: p.pillBg }]}>
                <Ionicons name="documents-outline" size={32} color={p.textMuted} />
              </View>
              <Text style={[styles.emptyTitle, { color: p.textPrimary }]}>No {filter.toLowerCase()} reports</Text>
              <Text style={[styles.emptySub, { color: p.textSecondary }]}>
                File a report using the camera button to notify ward engineers.
              </Text>
            </View>
          }
          renderItem={({ item, index }) => (
            <ExecutiveReportCard
              report={item}
              index={index}
              onPress={() => router.push({ pathname: '/report-details', params: { id: item.id } })}
              isDark={isDark}
            />
          )}
        />
      )}

      {/* Floating Create FAB */}
      <FAB onPress={() => router.push('/camera')} />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
  },
  headerContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    paddingTop: Platform.select({ ios: 56, android: 44 }) ?? 44,
    paddingHorizontal: 20,
    paddingBottom: 16,
  },
  kickerText: {
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 0.8,
    marginBottom: 2,
  },
  headerTitle: {
    fontSize: 26,
    fontWeight: '800',
    letterSpacing: -0.5,
  },
  statsCapsules: {
    flexDirection: 'row',
    gap: 8,
  },
  statCapsule: {
    borderRadius: 12,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 4,
    alignItems: 'center',
  },
  statVal: {
    fontSize: 14,
    fontWeight: '900',
  },
  statLbl: {
    fontSize: 9,
    fontWeight: '700',
  },

  filterBarContainer: {
    paddingHorizontal: 20,
    marginBottom: 16,
  },
  filterSegment: {
    flexDirection: 'row',
    borderRadius: 14,
    borderWidth: 1,
    padding: 3,
  },
  filterTabButton: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  filterTabText: {
    fontSize: 12,
  },

  loadingArea: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  listPadding: {
    paddingHorizontal: 20,
    paddingBottom: 100,
    gap: 14,
  },

  /* Card Styles */
  cardContainer: {
    borderRadius: 18,
    borderWidth: 1,
    overflow: 'hidden',
  },
  cardMediaArea: {
    height: 120,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardImage: {
    width: '100%',
    height: '100%',
  },
  cardPlaceholderIcon: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  statusBadge: {
    position: 'absolute',
    top: 10,
    right: 10,
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  statusBadgeText: {
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 0.5,
  },

  cardContent: {
    padding: 16,
    gap: 8,
  },
  reportTitle: {
    fontSize: 15,
    fontWeight: '800',
    lineHeight: 20,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  locationText: {
    fontSize: 12,
    fontWeight: '500',
    maxWidth: '65%',
  },
  dotSep: {
    fontSize: 10,
  },
  timeText: {
    fontSize: 11,
    fontWeight: '500',
  },

  divider: {
    height: 1,
    marginVertical: 4,
  },

  cardFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  counterWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  counterItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  counterText: {
    fontSize: 12,
    fontWeight: '700',
  },

  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
    gap: 10,
  },
  emptyIconCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '800',
  },
  emptySub: {
    fontSize: 12,
    textAlign: 'center',
    maxWidth: 240,
    lineHeight: 18,
  },
});