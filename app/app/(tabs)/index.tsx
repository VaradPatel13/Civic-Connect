import { useCallback, useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  RefreshControl,
  StyleSheet,
  Animated,
  Platform,
  TouchableOpacity,
  useColorScheme,
  Dimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import {
  FeaturedCard,
  ReportRow,
  EmptyState,
  ErrorState,
  FAB,
} from '@src/components/ui';
import { useDashboardStore, useAuthStore } from '@src/store';
import type { Report } from '@src/types';

const { width: SCREEN_W } = Dimensions.get('window');
const H_PAD = 20;

/* ─── Modern Curator Design System Tokens ────────────── */
const PALETTE = {
  dark: {
    bg: '#090A0F',
    surface: '#12141F',
    surfaceHover: '#1B1E2E',
    border: 'rgba(255, 255, 255, 0.08)',
    borderStrong: 'rgba(255, 255, 255, 0.16)',
    textPrimary: '#F8FAFC',
    textSecondary: '#94A3B8',
    textMuted: '#64748B',
    accentPrimary: '#A855F7', // Electric Violet
    accentCyan: '#06B6D4',    // Bright Cyan
    accentLime: '#84CC16',    // Fresh Lime
    accentRose: '#F43F5E',    // Vivid Rose
    accentAmber: '#F59E0B',   // Warm Amber
    pillBg: '#1A1D2D',
    heroGradientBg: '#1A132B',
  },
  light: {
    bg: '#F8FAFC',
    surface: '#FFFFFF',
    surfaceHover: '#F1F5F9',
    border: 'rgba(0, 0, 0, 0.08)',
    borderStrong: 'rgba(0, 0, 0, 0.16)',
    textPrimary: '#0F172A',
    textSecondary: '#475569',
    textMuted: '#94A3B8',
    accentPrimary: '#7C3AED',
    accentCyan: '#0891B2',
    accentLime: '#65A30D',
    accentRose: '#E11D48',
    accentAmber: '#D97706',
    pillBg: '#F1F5F9',
    heroGradientBg: '#F3E8FF',
  },
};

/* ─── Smooth Micro Entrance Hook ─────────────────────── */
function useEntrance(delay = 0) {
  const scale = useRef(new Animated.Value(0.95)).current;
  const opacity = useRef(new Animated.Value(0)).current;
  const translateY = useRef(new Animated.Value(12)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.spring(scale, {
        toValue: 1,
        friction: 9,
        tension: 45,
        delay,
        useNativeDriver: true,
      }),
      Animated.timing(opacity, {
        toValue: 1,
        duration: 350,
        delay,
        useNativeDriver: true,
      }),
      Animated.spring(translateY, {
        toValue: 0,
        friction: 8,
        tension: 35,
        delay,
        useNativeDriver: true,
      }),
    ]).start();
  }, [delay, scale, opacity, translateY]);

  return { scale, opacity, translateY };
}

/* ─── Hero Masthead & Citizen Guardian Card ──────────── */
function HeroMasthead({
  userName,
  points,
  onPressProfile,
  onPressNotif,
  unreadCount,
  isDark,
}: {
  userName: string;
  points: number;
  onPressProfile: () => void;
  onPressNotif: () => void;
  unreadCount: number;
  isDark: boolean;
}) {
  const p = isDark ? PALETTE.dark : PALETTE.light;
  const { scale, opacity, translateY } = useEntrance(0);
  const pulse = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 0.3, duration: 900, useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 1, duration: 900, useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [pulse]);

  const levelName = points >= 500 ? 'Civic Guardian III' : points >= 200 ? 'Neighborhood Scout' : 'Active Resident';

  return (
    <Animated.View style={[styles.mastheadWrapper, { opacity, transform: [{ scale }, { translateY }] }]}>
      {/* Location Badge Bar */}
      <View style={styles.topLocationRow}>
        <View style={[styles.locationChip, { backgroundColor: p.pillBg, borderColor: p.border }]}>
          <Animated.View style={[styles.liveDot, { opacity: pulse, backgroundColor: p.accentLime }]} />
          <Text style={[styles.locationText, { color: p.textSecondary }]}>
            LOCATION • <Text style={{ color: p.textPrimary, fontWeight: '800' }}>Ward 12, Shivajinagar</Text>
          </Text>
        </View>

        <TouchableOpacity
          activeOpacity={0.8}
          style={[styles.bellButton, { backgroundColor: p.surface, borderColor: p.border }]}
          onPress={onPressNotif}>
          <Ionicons name="notifications-outline" size={20} color={p.textPrimary} />
          {unreadCount > 0 && (
            <View style={[styles.notifBadge, { backgroundColor: p.accentRose }]}>
              <Text style={styles.notifBadgeText}>{unreadCount > 9 ? '9+' : unreadCount}</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      {/* Greeting & Avatar */}
      <View style={styles.userGreetingRow}>
        <TouchableOpacity activeOpacity={0.85} style={styles.userProfileTouch} onPress={onPressProfile}>
          <View style={[styles.avatarBox, { backgroundColor: p.accentPrimary }]}>
            <Text style={styles.avatarLetter}>{userName.charAt(0).toUpperCase() || 'C'}</Text>
          </View>
          <View>
            <Text style={[styles.salutationText, { color: p.textSecondary }]}>Welcome back 👋</Text>
            <Text style={[styles.displayNameText, { color: p.textPrimary }]}>{userName}</Text>
          </View>
        </TouchableOpacity>

        {/* Guardian Level Capsule */}
        <View style={[styles.levelCapsule, { backgroundColor: `${p.accentAmber}15`, borderColor: `${p.accentAmber}40` }]}>
          <Ionicons name="shield-checkmark" size={16} color={p.accentAmber} />
          <View>
            <Text style={[styles.levelTitle, { color: p.accentAmber }]}>{levelName}</Text>
            <Text style={[styles.levelPoints, { color: p.textSecondary }]}>{points} XP</Text>
          </View>
        </View>
      </View>
    </Animated.View>
  );
}

/* ─── Hero Instant Report Trigger ───────────────────── */
function InstantReportLauncher({ onPressCamera, isDark }: { onPressCamera: () => void; isDark: boolean }) {
  const p = isDark ? PALETTE.dark : PALETTE.light;
  const { scale, opacity, translateY } = useEntrance(120);

  return (
    <Animated.View style={[styles.heroLauncher, { opacity, transform: [{ scale }, { translateY }] }]}>
      <View style={[styles.heroLauncherBg, { backgroundColor: p.heroGradientBg, borderColor: p.borderStrong }]}>
        <View style={styles.launcherTextContent}>
          <View style={styles.tagCapsule}>
            <Ionicons name="flash-outline" size={12} color={p.accentPrimary} />
            <Text style={[styles.tagText, { color: p.accentPrimary }]}>AI-POWERED CIVIC DESK</Text>
          </View>

          <Text style={[styles.launcherTitle, { color: p.textPrimary }]}>
            Spot a pothole or issue?
          </Text>
          <Text style={[styles.launcherSub, { color: p.textSecondary }]}>
            Snap a quick photo. Our AI auto-detects urgency & alerts Ward 12 officers.
          </Text>

          <TouchableOpacity activeOpacity={0.88} style={[styles.snapButton, { backgroundColor: p.accentPrimary }]} onPress={onPressCamera}>
            <Ionicons name="camera" size={18} color="#FFFFFF" />
            <Text style={styles.snapButtonText}>File Instant Report</Text>
            <Ionicons name="arrow-forward" size={16} color="#FFFFFF" />
          </TouchableOpacity>
        </View>
      </View>
    </Animated.View>
  );
}

/* ─── Asymmetric Civic Metric Stats ───────────────────── */
function CityPulseMetrics({
  openCount,
  resolvedCount,
  avgDays,
  totalCount,
  isDark,
}: {
  openCount: number;
  resolvedCount: number;
  avgDays: number;
  totalCount: number;
  isDark: boolean;
}) {
  const p = isDark ? PALETTE.dark : PALETTE.light;
  const { scale, opacity, translateY } = useEntrance(220);

  return (
    <Animated.View style={[styles.metricsContainer, { opacity, transform: [{ scale }, { translateY }] }]}>
      <Text style={[styles.sectionTitleText, { color: p.textPrimary }]}>Ward Response Statistics</Text>

      {/* Main Wide Featured Card */}
      <View style={[styles.wideMetricCard, { backgroundColor: p.surface, borderColor: p.border }]}>
        <View style={styles.wideCardLeft}>
          <View style={[styles.metricIconWrap, { backgroundColor: `${p.accentCyan}18` }]}>
            <Ionicons name="pulse-outline" size={22} color={p.accentCyan} />
          </View>
          <View style={{ gap: 2 }}>
            <Text style={[styles.wideMetricVal, { color: p.textPrimary }]}>{avgDays} Days</Text>
            <Text style={[styles.wideMetricLabel, { color: p.textSecondary }]}>Average PMC Resolution Time</Text>
          </View>
        </View>

        <View style={[styles.statusBadgeCapsule, { backgroundColor: `${p.accentLime}20` }]}>
          <Ionicons name="trending-down-outline" size={14} color={p.accentLime} />
          <Text style={[styles.statusBadgeText, { color: p.accentLime }]}>Fast Pace</Text>
        </View>
      </View>

      {/* 3 Column Compact Grid */}
      <View style={styles.threeColRow}>
        <View style={[styles.miniMetricTile, { backgroundColor: p.surface, borderColor: p.border }]}>
          <Text style={[styles.miniVal, { color: p.accentRose }]}>{openCount}</Text>
          <Text style={[styles.miniLabel, { color: p.textSecondary }]}>Active</Text>
        </View>

        <View style={[styles.miniMetricTile, { backgroundColor: p.surface, borderColor: p.border }]}>
          <Text style={[styles.miniVal, { color: p.accentLime }]}>{resolvedCount}</Text>
          <Text style={[styles.miniLabel, { color: p.textSecondary }]}>Resolved</Text>
        </View>

        <View style={[styles.miniMetricTile, { backgroundColor: p.surface, borderColor: p.border }]}>
          <Text style={[styles.miniVal, { color: p.textPrimary }]}>{totalCount}</Text>
          <Text style={[styles.miniLabel, { color: p.textSecondary }]}>Total Filed</Text>
        </View>
      </View>
    </Animated.View>
  );
}

/* ─── Category Filter Chips ───────────────────────────── */
function FilterCategoryStrip({
  trending,
  selectedCategory,
  onSelectCategory,
  isDark,
}: {
  trending: { label: string; count: number; icon: string }[];
  selectedCategory: string | null;
  onSelectCategory: (cat: string | null) => void;
  isDark: boolean;
}) {
  const p = isDark ? PALETTE.dark : PALETTE.light;

  return (
    <View style={styles.filterStripContainer}>
      <View style={styles.sectionHeaderRow}>
        <Text style={[styles.sectionTitleText, { color: p.textPrimary }]}>Trending Categories</Text>
        {selectedCategory && (
          <TouchableOpacity onPress={() => onSelectCategory(null)}>
            <Text style={[styles.resetFilterText, { color: p.accentPrimary }]}>Show All</Text>
          </TouchableOpacity>
        )}
      </View>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipsScrollContent}>
        {trending.map((item) => {
          const isSelected = selectedCategory?.toLowerCase() === item.label.toLowerCase();
          return (
            <TouchableOpacity
              key={item.label}
              activeOpacity={0.75}
              style={[
                styles.categoryChip,
                {
                  backgroundColor: isSelected ? p.textPrimary : p.surface,
                  borderColor: isSelected ? p.textPrimary : p.border,
                },
              ]}
              onPress={() => onSelectCategory(isSelected ? null : item.label)}>
              <Ionicons name={item.icon as any} size={14} color={isSelected ? p.bg : p.accentCyan} />
              <Text style={[styles.chipText, { color: isSelected ? p.bg : p.textPrimary }]}>{item.label}</Text>
              <View style={[styles.chipBadge, { backgroundColor: isSelected ? p.bg : p.pillBg }]}>
                <Text style={[styles.chipBadgeText, { color: isSelected ? p.textPrimary : p.textSecondary }]}>
                  {item.count}
                </Text>
              </View>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
}

/* ─── Main Screen Component ───────────────────────────── */
export default function DashboardScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';
  const p = isDark ? PALETTE.dark : PALETTE.light;

  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const { stats, reports, trending, isLoading, isRefreshing, error, fetchDashboard, refresh } = useDashboardStore();
  const { user } = useAuthStore();

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const handleRefresh = useCallback(() => refresh(), [refresh]);

  const handleViewReport = useCallback(
    (id: string) => router.push({ pathname: '/report-details', params: { id } }),
    [router],
  );

  const filteredReports = selectedCategory
    ? reports.filter((r) => r.category?.toLowerCase() === selectedCategory.toLowerCase())
    : reports;

  const [featured, ...rest] = filteredReports;
  const reportCount = filteredReports.length;
  const openCount = stats?.openReports ?? 0;
  const resolvedCount = stats?.resolvedThisMonth ?? 0;
  const totalCount = stats?.totalReports ?? 0;
  const avgDays = stats?.avgResolutionDays ?? 2.4;

  const userName = user?.display_name || 'Citizen';
  const points = user?.points ?? 150;

  if (isLoading && !stats && !error) {
    return (
      <View style={[styles.screen, { backgroundColor: p.bg }]}>
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          <View style={[styles.skelCard, { height: 110, backgroundColor: p.surface }]} />
          <View style={[styles.skelCard, { height: 140, marginTop: 16, backgroundColor: p.surface }]} />
          <View style={[styles.skelCard, { height: 180, marginTop: 16, backgroundColor: p.surface }]} />
        </ScrollView>
      </View>
    );
  }

  if (error && !stats && !reports.length) {
    return (
      <View style={[styles.screen, { backgroundColor: p.bg }]}>
        <ErrorState message={error} onRetry={fetchDashboard} />
      </View>
    );
  }

  return (
    <View style={[styles.screen, { backgroundColor: p.bg }]}>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={isRefreshing} onRefresh={handleRefresh} tintColor={p.accentPrimary} colors={[p.accentPrimary]} />
        }>
        {/* Header & User Profile */}
        <HeroMasthead
          userName={userName}
          points={points}
          onPressProfile={() => router.push('/(tabs)/profile')}
          onPressNotif={() => router.push('/notifications')}
          unreadCount={openCount}
          isDark={isDark}
        />

        {/* Quick Report Launcher */}
        <InstantReportLauncher onPressCamera={() => router.push('/camera')} isDark={isDark} />

        {/* Ward Metrics Summary */}
        <CityPulseMetrics
          openCount={openCount}
          resolvedCount={resolvedCount}
          avgDays={avgDays}
          totalCount={totalCount}
          isDark={isDark}
        />

        {/* Category Filters */}
        {trending && trending.length > 0 && (
          <FilterCategoryStrip
            trending={trending}
            selectedCategory={selectedCategory}
            onSelectCategory={setSelectedCategory}
            isDark={isDark}
          />
        )}

        {/* Neighborhood Feed */}
        <View style={styles.reportsFeedSection}>
          <View style={styles.sectionHeaderRow}>
            <Text style={[styles.sectionTitleText, { color: p.textPrimary }]}>
              {selectedCategory ? `${selectedCategory} Issues` : 'Recent Reports'}
            </Text>
            <Text style={[styles.reportCountText, { color: p.textSecondary }]}>{reportCount} listed</Text>
          </View>

          {reportCount === 0 ? (
            <EmptyState onReport={() => router.push('/camera')} />
          ) : (
            <View style={styles.reportsList}>
              {featured && <FeaturedCard report={featured} onPress={() => handleViewReport(featured.id)} />}
              {rest.map((r: Report) => (
                <ReportRow key={r.id} report={r} onPress={() => handleViewReport(r.id)} />
              ))}
            </View>
          )}
        </View>

        <View style={{ height: 100 }} />
      </ScrollView>

      {/* Floating Camera FAB */}
      <FAB onPress={() => router.push('/camera')} />
    </View>
  );
}

/* ─── Screen Stylesheet ───────────────────────────────── */
const styles = StyleSheet.create({
  screen: {
    flex: 1,
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingTop: Platform.select({ ios: 56, android: 44 }) ?? 44,
    paddingHorizontal: H_PAD,
    paddingBottom: 24,
  },

  /* Masthead */
  mastheadWrapper: {
    gap: 14,
    marginBottom: 20,
  },
  topLocationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  locationChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    borderRadius: 20,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  liveDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  locationText: {
    fontSize: 10,
    letterSpacing: 0.5,
  },
  bellButton: {
    width: 40,
    height: 40,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  notifBadge: {
    position: 'absolute',
    top: 6,
    right: 6,
    minWidth: 16,
    height: 16,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
  },
  notifBadgeText: {
    color: '#FFF',
    fontSize: 9,
    fontWeight: '900',
  },

  userGreetingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  userProfileTouch: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  avatarBox: {
    width: 44,
    height: 44,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarLetter: {
    fontSize: 18,
    fontWeight: '800',
    color: '#FFF',
  },
  salutationText: {
    fontSize: 12,
    fontWeight: '500',
  },
  displayNameText: {
    fontSize: 18,
    fontWeight: '800',
    letterSpacing: -0.3,
  },

  levelCapsule: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    borderRadius: 12,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  levelTitle: {
    fontSize: 11,
    fontWeight: '800',
  },
  levelPoints: {
    fontSize: 10,
    fontWeight: '600',
  },

  /* Instant Launcher Banner */
  heroLauncher: {
    marginBottom: 24,
  },
  heroLauncherBg: {
    borderRadius: 20,
    borderWidth: 1,
    padding: 18,
  },
  launcherTextContent: {
    gap: 10,
  },
  tagCapsule: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    alignSelf: 'flex-start',
  },
  tagText: {
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 0.8,
  },
  launcherTitle: {
    fontSize: 18,
    fontWeight: '800',
    letterSpacing: -0.4,
  },
  launcherSub: {
    fontSize: 12,
    lineHeight: 18,
  },
  snapButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderRadius: 14,
    paddingVertical: 12,
    paddingHorizontal: 18,
    marginTop: 4,
    alignSelf: 'flex-start',
  },
  snapButtonText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '800',
  },

  /* Metrics Section */
  metricsContainer: {
    gap: 12,
    marginBottom: 24,
  },
  sectionTitleText: {
    fontSize: 16,
    fontWeight: '800',
    letterSpacing: -0.3,
  },
  wideMetricCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderRadius: 16,
    borderWidth: 1,
    padding: 16,
  },
  wideCardLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  metricIconWrap: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  wideMetricVal: {
    fontSize: 18,
    fontWeight: '800',
  },
  wideMetricLabel: {
    fontSize: 11,
    fontWeight: '500',
  },
  statusBadgeCapsule: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  statusBadgeText: {
    fontSize: 10,
    fontWeight: '800',
  },

  threeColRow: {
    flexDirection: 'row',
    gap: 10,
  },
  miniMetricTile: {
    flex: 1,
    borderRadius: 14,
    borderWidth: 1,
    paddingVertical: 14,
    paddingHorizontal: 12,
    alignItems: 'center',
    gap: 4,
  },
  miniVal: {
    fontSize: 20,
    fontWeight: '900',
    letterSpacing: -0.5,
  },
  miniLabel: {
    fontSize: 11,
    fontWeight: '600',
  },

  /* Filter Strip */
  filterStripContainer: {
    marginBottom: 24,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  resetFilterText: {
    fontSize: 12,
    fontWeight: '700',
  },
  chipsScrollContent: {
    gap: 10,
    paddingRight: H_PAD,
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    borderRadius: 20,
    borderWidth: 1,
    paddingVertical: 8,
    paddingHorizontal: 14,
  },
  chipText: {
    fontSize: 12,
    fontWeight: '700',
  },
  chipBadge: {
    borderRadius: 10,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  chipBadgeText: {
    fontSize: 10,
    fontWeight: '800',
  },

  /* Reports Feed */
  reportsFeedSection: {
    marginTop: 4,
  },
  reportCountText: {
    fontSize: 12,
    fontWeight: '500',
  },
  reportsList: {
    gap: 12,
  },

  skelCard: {
    borderRadius: 16,
  },
});