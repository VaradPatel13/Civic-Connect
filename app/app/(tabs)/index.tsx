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
  Image,
  FlatList,
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
import { useDashboardStore } from '@src/store';
import type { Report } from '@src/types';
import { getCurrentLocation, DeviceLocation } from '@src/lib/location';

const { width: SCREEN_W } = Dimensions.get('window');
const H_PAD = 20;

/* ─── Emerald & Forest Civic Theme Palette ─────────────── */
const CIVIC_GREEN_PALETTE = {
  dark: {
    bg: '#05160E',
    surface: '#0B2419',
    surfaceHover: '#123324',
    border: 'rgba(16, 185, 129, 0.18)',
    borderStrong: 'rgba(16, 185, 129, 0.35)',
    textPrimary: '#ECFDF5',
    textSecondary: '#A7F3D0',
    textMuted: '#6EE7B7',
    accentPrimary: '#10B981', // Vivid Emerald Green
    accentMint: '#34D399',    // Mint Green
    accentCyan: '#06B6D4',    // Ocean Cyan
    accentLime: '#84CC16',    // Fresh Lime
    accentAmber: '#F59E0B',   // Warm Amber
    accentRose: '#F43F5E',    // Vivid Coral Rose
    pillBg: '#092F20',
    cardBg: '#0D2D20',
  },
  light: {
    bg: '#F0FDF4',
    surface: '#FFFFFF',
    surfaceHover: '#E6F4EA',
    border: 'rgba(5, 150, 105, 0.15)',
    borderStrong: 'rgba(5, 150, 105, 0.3)',
    textPrimary: '#064E3B',
    textSecondary: '#047857',
    textMuted: '#059669',
    accentPrimary: '#059669', // Deep Emerald Green
    accentMint: '#10B981',
    accentCyan: '#0891B2',
    accentLime: '#65A30D',
    accentAmber: '#D97706',
    accentRose: '#E11D48',
    pillBg: '#DCFCE7',
    cardBg: '#FFFFFF',
  },
};

/* ─── Civic Announcement Slider Data ───────────────────── */
const CIVIC_SLIDES = [
  {
    id: 'slide-1',
    badge: 'MUNICIPAL DRIVE',
    title: 'Clean Ward 12 & Zero Waste Drive 2026',
    sub: 'Join 1,200+ citizens segregating waste & planting 500 native trees.',
    colorBg: '#064E3B',
    accentColor: '#34D399',
    icon: 'leaf',
  },
  {
    id: 'slide-2',
    badge: 'INFRASTRUCTURE UPDATE',
    title: '100% Solar Streetlights on Main Arterial Roads',
    sub: 'Smart LED grids installed across University Road & FC Road junction.',
    colorBg: '#047857',
    accentColor: '#84CC16',
    icon: 'flash',
  },
  {
    id: 'slide-3',
    badge: 'MONSOON PREPAREDNESS',
    title: 'High-Capacity Drainage Cleaning Drive',
    sub: 'PMC engineering teams clearing 45km stormwater drains ahead of monsoon.',
    colorBg: '#065F46',
    accentColor: '#06B6D4',
    icon: 'water',
  },
];

/* ─── Smooth Micro Entrance Hook ─────────────────────── */
function useEntrance(delay = 0) {
  const scale = useRef(new Animated.Value(0.96)).current;
  const opacity = useRef(new Animated.Value(0)).current;
  const translateY = useRef(new Animated.Value(10)).current;

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

/* ─── 1. Top Section: Image Carousel Slider ──────────── */
function CivicImageSlider({ isDark }: { isDark: boolean }) {
  const p = isDark ? CIVIC_GREEN_PALETTE.dark : CIVIC_GREEN_PALETTE.light;
  const [activeIndex, setActiveIndex] = useState(0);
  const flatListRef = useRef<FlatList>(null);
  const { scale, opacity } = useEntrance(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveIndex((prev) => {
        const next = (prev + 1) % CIVIC_SLIDES.length;
        flatListRef.current?.scrollToIndex({ index: next, animated: true });
        return next;
      });
    }, 4500);
    return () => clearInterval(timer);
  }, []);

  const slideWidth = SCREEN_W - H_PAD * 2;

  return (
    <Animated.View style={[styles.sliderContainer, { opacity, transform: [{ scale }] }]}>
      <FlatList
        ref={flatListRef}
        data={CIVIC_SLIDES}
        keyExtractor={(item) => item.id}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={(ev) => {
          const newIdx = Math.round(ev.nativeEvent.contentOffset.x / slideWidth);
          setActiveIndex(newIdx);
        }}
        renderItem={({ item }) => (
          <View style={[styles.slideCard, { width: slideWidth, backgroundColor: item.colorBg, borderColor: p.borderStrong }]}>
            <View style={styles.slideHeaderRow}>
              <View style={[styles.slideBadge, { backgroundColor: 'rgba(255, 255, 255, 0.15)' }]}>
                <Ionicons name={item.icon as any} size={12} color={item.accentColor} />
                <Text style={[styles.slideBadgeText, { color: item.accentColor }]}>{item.badge}</Text>
              </View>
            </View>

            <Text style={styles.slideTitle}>{item.title}</Text>
            <Text style={styles.slideSub}>{item.sub}</Text>
          </View>
        )}
      />

      {/* Slide Indicators */}
      <View style={styles.dotsRow}>
        {CIVIC_SLIDES.map((_, i) => (
          <View
            key={i}
            style={[
              styles.dot,
              {
                backgroundColor: i === activeIndex ? p.accentMint : isDark ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.15)',
                width: i === activeIndex ? 20 : 6,
              },
            ]}
          />
        ))}
      </View>
    </Animated.View>
  );
}

/* ─── 2. Second Section: Current Location Banner ─────── */
function LocationBanner({
  location,
  loadingLoc,
  onRefresh,
  isDark,
}: {
  location: DeviceLocation | null;
  loadingLoc: boolean;
  onRefresh: () => void;
  isDark: boolean;
}) {
  const p = isDark ? CIVIC_GREEN_PALETTE.dark : CIVIC_GREEN_PALETTE.light;
  const { opacity, translateY } = useEntrance(100);

  const addressText = location?.address || 'Shivajinagar, Ward 12, Pune';
  const coordsText = location
    ? `${location.latitude.toFixed(4)}° N, ${location.longitude.toFixed(4)}° E`
    : '18.5204° N, 73.8567° E';
  const accuracyText = location?.accuracy ? `± ${location.accuracy.toFixed(1)}m GPS Accuracy` : 'High GPS Accuracy';

  return (
    <Animated.View style={[styles.locationCard, { backgroundColor: p.surface, borderColor: p.border }, { opacity, transform: [{ translateY }] }]}>
      <View style={styles.locationHeaderRow}>
        <View style={styles.locationTitleLeft}>
          <View style={[styles.locationIconWrap, { backgroundColor: `${p.accentPrimary}20` }]}>
            <Ionicons name="navigate" size={18} color={p.accentPrimary} />
          </View>
          <View>
            <Text style={[styles.locationKicker, { color: p.textMuted }]}>CURRENT CIVIC JURISDICTION</Text>
            <Text style={[styles.locationAddressText, { color: p.textPrimary }]} numberOfLines={1}>
              {addressText}
            </Text>
          </View>
        </View>

        <TouchableOpacity
          activeOpacity={0.7}
          style={[styles.refreshLocBtn, { backgroundColor: p.pillBg, borderColor: p.border }]}
          onPress={onRefresh}
          disabled={loadingLoc}>
          <Ionicons name={loadingLoc ? 'sync-outline' : 'refresh-outline'} size={16} color={p.accentPrimary} />
        </TouchableOpacity>
      </View>

      <View style={[styles.locationDivider, { backgroundColor: p.border }]} />

      <View style={styles.locationFooterRow}>
        <View style={styles.locBadgeItem}>
          <Ionicons name="location-outline" size={12} color={p.textMuted} />
          <Text style={[styles.locFooterText, { color: p.textSecondary }]}>{coordsText}</Text>
        </View>

        <View style={[styles.locBadgePill, { backgroundColor: `${p.accentLime}20` }]}>
          <View style={[styles.liveDot, { backgroundColor: p.accentLime }]} />
          <Text style={[styles.locPillText, { color: p.accentLime }]}>{accuracyText}</Text>
        </View>
      </View>
    </Animated.View>
  );
}

/* ─── 3. Third Section: City & Ward Statistics Bento ───── */
function CityStatsBento({ isDark }: { isDark: boolean }) {
  const p = isDark ? CIVIC_GREEN_PALETTE.dark : CIVIC_GREEN_PALETTE.light;
  const { opacity, translateY } = useEntrance(200);

  return (
    <Animated.View style={[styles.statsSection, { opacity, transform: [{ translateY }] }]}>
      <Text style={[styles.sectionTitle, { color: p.textPrimary }]}>District Response Pulse</Text>

      <View style={styles.statsGrid}>
        {/* Wide Main Metric Tile */}
        <View style={[styles.wideStatTile, { backgroundColor: p.surface, borderColor: p.border }]}>
          <View style={styles.wideStatLeft}>
            <View style={[styles.statIconBox, { backgroundColor: `${p.accentPrimary}20` }]}>
              <Ionicons name="alert-circle-outline" size={22} color={p.accentPrimary} />
            </View>
            <View>
              <Text style={[styles.wideStatNum, { color: p.textPrimary }]}>24 Active</Text>
              <Text style={[styles.wideStatLbl, { color: p.textSecondary }]}>Ward 12 Open Dispatches</Text>
            </View>
          </View>
          <View style={[styles.statusCapsule, { backgroundColor: `${p.accentRose}20` }]}>
            <Text style={[styles.statusCapsuleText, { color: p.accentRose }]}>HIGH PRIORITY</Text>
          </View>
        </View>

        {/* 3-Column Mini Tiles */}
        <View style={styles.miniStatsRow}>
          <View style={[styles.miniStatTile, { backgroundColor: p.surface, borderColor: p.border }]}>
            <Ionicons name="checkmark-done-circle" size={18} color={p.accentLime} />
            <Text style={[styles.miniStatVal, { color: p.textPrimary }]}>142</Text>
            <Text style={[styles.miniStatLbl, { color: p.textSecondary }]}>Fixed (30d)</Text>
          </View>

          <View style={[styles.miniStatTile, { backgroundColor: p.surface, borderColor: p.border }]}>
            <Ionicons name="time" size={18} color={p.accentCyan} />
            <Text style={[styles.miniStatVal, { color: p.textPrimary }]}>4.2h</Text>
            <Text style={[styles.miniStatLbl, { color: p.textSecondary }]}>Avg SLA</Text>
          </View>

          <View style={[styles.miniStatTile, { backgroundColor: p.surface, borderColor: p.border }]}>
            <Ionicons name="people" size={18} color={p.accentAmber} />
            <Text style={[styles.miniStatVal, { color: p.textPrimary }]}>18</Text>
            <Text style={[styles.miniStatLbl, { color: p.textSecondary }]}>Crews On-Site</Text>
          </View>
        </View>
      </View>
    </Animated.View>
  );
}

/* ─── 4. Fourth Section: Trending Categories ──────────── */
const TRENDING_CATS = [
  { id: 'pothole', label: 'Potholes & Roads', icon: 'construct', count: 12, color: '#10B981' },
  { id: 'streetlight', label: 'Street Lights', icon: 'flash', count: 8, color: '#84CC16' },
  { id: 'drainage', label: 'Water & Drainage', icon: 'water', count: 6, color: '#06B6D4' },
  { id: 'sanitation', label: 'Waste Disposal', icon: 'trash-bin', count: 5, color: '#F59E0B' },
  { id: 'traffic', label: 'Traffic Signals', icon: 'trail-sign', count: 3, color: '#EC4899' },
];

function TrendingCategoriesSection({
  selectedCategory,
  onSelect,
  isDark,
}: {
  selectedCategory: string | null;
  onSelect: (catId: string | null) => void;
  isDark: boolean;
}) {
  const p = isDark ? CIVIC_GREEN_PALETTE.dark : CIVIC_GREEN_PALETTE.light;
  const { opacity, translateY } = useEntrance(300);

  return (
    <Animated.View style={[styles.categoriesSection, { opacity, transform: [{ translateY }] }]}>
      <View style={styles.catHeaderRow}>
        <Text style={[styles.sectionTitle, { color: p.textPrimary }]}>Trending Categories</Text>
        {selectedCategory && (
          <TouchableOpacity onPress={() => onSelect(null)}>
            <Text style={[styles.resetText, { color: p.accentPrimary }]}>Show All</Text>
          </TouchableOpacity>
        )}
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.catScrollContent}>
        {TRENDING_CATS.map((cat) => {
          const isSelected = selectedCategory === cat.id;
          return (
            <TouchableOpacity
              key={cat.id}
              activeOpacity={0.8}
              style={[
                styles.catTile,
                {
                  backgroundColor: isSelected ? p.accentPrimary : p.surface,
                  borderColor: isSelected ? p.accentMint : p.border,
                },
              ]}
              onPress={() => onSelect(isSelected ? null : cat.id)}>
              <View style={[styles.catIconWrap, { backgroundColor: isSelected ? 'rgba(255,255,255,0.2)' : `${cat.color}20` }]}>
                <Ionicons name={cat.icon as any} size={18} color={isSelected ? '#FFF' : cat.color} />
              </View>
              <Text style={[styles.catLabel, { color: isSelected ? '#FFF' : p.textPrimary }]}>{cat.label}</Text>
              <View style={[styles.catCountBadge, { backgroundColor: isSelected ? 'rgba(255,255,255,0.25)' : p.pillBg }]}>
                <Text style={[styles.catCountText, { color: isSelected ? '#FFF' : p.textSecondary }]}>{cat.count}</Text>
              </View>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </Animated.View>
  );
}

/* ─── 5. Fifth Section: Recent Reports Feed ───────────── */
export default function DashboardScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';
  const p = isDark ? CIVIC_GREEN_PALETTE.dark : CIVIC_GREEN_PALETTE.light;

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
    <View style={[styles.screen, { backgroundColor: p.bg }]}>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} tintColor={p.accentPrimary} />
        }>
        {/* Section 1: Top Civic Announcement Carousel Slider */}
        <CivicImageSlider isDark={isDark} />

        {/* Section 2: User Current Location Banner */}
        <LocationBanner
          location={deviceLoc}
          loadingLoc={loadingLoc}
          onRefresh={loadLocation}
          isDark={isDark}
        />

        {/* Section 3: District Response Stats Bento */}
        <CityStatsBento isDark={isDark} />

        {/* Section 4: Trending Categories */}
        <TrendingCategoriesSection
          selectedCategory={selectedCategory}
          onSelect={setSelectedCategory}
          isDark={isDark}
        />

        {/* Section 5: Recent Reports Feed */}
        <View style={styles.feedSection}>
          <View style={styles.feedHeaderRow}>
            <Text style={[styles.sectionTitle, { color: p.textPrimary }]}>Recent District Reports</Text>
            <Text style={[styles.feedCountText, { color: p.textMuted }]}>{filteredReports.length} Filed</Text>
          </View>

          {isLoading && reports.length === 0 ? (
            <View style={styles.skelStack}>
              <View style={[styles.skelCard, { backgroundColor: p.surface }]} />
              <View style={[styles.skelCard, { backgroundColor: p.surface }]} />
            </View>
          ) : error && reports.length === 0 ? (
            <ErrorState message={error} onRetry={fetchDashboard} />
          ) : filteredReports.length === 0 ? (
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

      {/* Floating Action Camera FAB */}
      <FAB onPress={() => router.push('/camera')} />
    </View>
  );
}

/* ─── Stylesheet ───────────────────────────────────────── */
const styles = StyleSheet.create({
  screen: { flex: 1 },
  scroll: { flex: 1 },
  scrollContent: {
    paddingTop: Platform.select({ ios: 56, android: 44 }) ?? 44,
    paddingHorizontal: H_PAD,
    paddingBottom: 24,
    gap: 20,
  },

  /* 1. Carousel Slider */
  sliderContainer: {
    marginBottom: 4,
  },
  slideCard: {
    borderRadius: 20,
    borderWidth: 1,
    padding: 18,
    gap: 8,
    minHeight: 140,
    justifyContent: 'center',
  },
  slideHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  slideBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderRadius: 20,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  slideBadgeText: {
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 0.8,
  },
  slideTitle: {
    color: '#FFFFFF',
    fontSize: 17,
    fontWeight: '800',
    letterSpacing: -0.4,
    lineHeight: 22,
  },
  slideSub: {
    color: 'rgba(255, 255, 255, 0.85)',
    fontSize: 12,
    lineHeight: 17,
  },
  dotsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 10,
  },
  dot: {
    height: 6,
    borderRadius: 3,
  },

  /* 2. Current Location Banner */
  locationCard: {
    borderRadius: 18,
    borderWidth: 1,
    padding: 16,
    gap: 12,
  },
  locationHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  locationTitleLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  locationIconWrap: {
    width: 38,
    height: 38,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  locationKicker: {
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 0.8,
  },
  locationAddressText: {
    fontSize: 15,
    fontWeight: '800',
    maxWidth: 220,
  },
  refreshLocBtn: {
    width: 36,
    height: 36,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  locationDivider: {
    height: 1,
  },
  locationFooterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  locBadgeItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  locFooterText: {
    fontSize: 11,
    fontWeight: '600',
  },
  locBadgePill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  liveDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  locPillText: {
    fontSize: 10,
    fontWeight: '800',
  },

  /* 3. Stats Section */
  statsSection: {
    gap: 12,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: '800',
    letterSpacing: -0.3,
  },
  statsGrid: {
    gap: 10,
  },
  wideStatTile: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderRadius: 16,
    borderWidth: 1,
    padding: 16,
  },
  wideStatLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  statIconBox: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  wideStatNum: {
    fontSize: 18,
    fontWeight: '800',
  },
  wideStatLbl: {
    fontSize: 11,
    fontWeight: '500',
  },
  statusCapsule: {
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  statusCapsuleText: {
    fontSize: 9,
    fontWeight: '900',
  },

  miniStatsRow: {
    flexDirection: 'row',
    gap: 10,
  },
  miniStatTile: {
    flex: 1,
    borderRadius: 14,
    borderWidth: 1,
    paddingVertical: 12,
    paddingHorizontal: 10,
    alignItems: 'center',
    gap: 4,
  },
  miniStatVal: {
    fontSize: 16,
    fontWeight: '900',
  },
  miniStatLbl: {
    fontSize: 10,
    fontWeight: '600',
  },

  /* 4. Categories Section */
  categoriesSection: {
    gap: 12,
  },
  catHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  resetText: {
    fontSize: 12,
    fontWeight: '700',
  },
  catScrollContent: {
    gap: 10,
  },
  catTile: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    borderRadius: 16,
    borderWidth: 1,
    paddingVertical: 10,
    paddingHorizontal: 14,
  },
  catIconWrap: {
    width: 28,
    height: 28,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  catLabel: {
    fontSize: 13,
    fontWeight: '700',
  },
  catCountBadge: {
    borderRadius: 10,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  catCountText: {
    fontSize: 10,
    fontWeight: '800',
  },

  /* 5. Reports Feed Section */
  feedSection: {
    gap: 12,
  },
  feedHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  feedCountText: {
    fontSize: 12,
    fontWeight: '600',
  },
  reportsList: {
    gap: 12,
  },
  skelStack: {
    gap: 12,
  },
  skelCard: {
    height: 120,
    borderRadius: 16,
  },
});