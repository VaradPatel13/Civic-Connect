/**
 * Dashboard — CivicConnect
 *
 * Reads exclusively from useDashboardStore → Real Backend API.
 * Zero hardcoded data. All display tokens come from @src/constants/tokens.ts.
 */
import { useEffect, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity,
  RefreshControl, ActivityIndicator, Image,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { tokens } from '@src/constants';
import { useDashboardStore } from '@src/store';
import type { Report } from '@src/types';

// ─── UI-only constants (display logic, NOT data) ─────────────────────────────

const CATEGORY_ICON: Record<string, string> = {
  pothole:    'alert-circle',
  streetlight: 'flash',
  drainage:   'water',
  water:      'water-outline',
  sanitation: 'trash',
  traffic:    'trail-sign',
  noise:      'volume-high',
  other:      'location',
};

// ─── Helpers ────────────────────────────────────────────────────────────────

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins  = Math.floor(diff / 60_000);
  if (mins < 60)  return `${mins} m`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24)   return `${hrs} h`;
  return `${Math.floor(hrs / 24)} d`;
}

// ─── Sub-components ──────────────────────────────────────────────────────────

/* ── MASTHEAD ──────────────────────────────────────────────────────────────── */
function Masthead({ stats }: { stats: any }) {
  return (
    <View style={{ paddingHorizontal: 20, paddingTop: 48, paddingBottom: 20 }}>
      {/* Location row */}
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 14 }}>
        <View style={{ width: 7, height: 7, borderRadius: 3.5, backgroundColor: '#10b981' }} />
        <Text style={{ color: tokens.text.primary, fontSize: 12, fontWeight: '700', letterSpacing: 1.5, textTransform: 'uppercase' }}>
          pune
        </Text>
        <Text style={{ color: tokens.text.disabled, fontSize: 12 }}>·</Text>
        <Text style={{ color: tokens.text.secondary, fontSize: 12 }}>
          {stats ? `${stats.totalReports} reports this week` : 'Connecting…'}
        </Text>
      </View>

      {/* Editorial headline */}
      <View style={{ marginBottom: 22 }}>
        <Text style={{ color: tokens.text.primary, fontSize: 32, fontWeight: '800', lineHeight: 36, letterSpacing: -1 }}>
          Your City.
        </Text>
        <Text style={{
          color: tokens.primary.DEFAULT,
          fontSize: 32,
          fontWeight: '800',
          lineHeight: 36,
          letterSpacing: -1,
          marginTop: -4,
        }}>
          Your Voice.
        </Text>
      </View>

      {/* Stats */}
      {stats ? (
        <View>
          {/* Top row: two big numbers + labels */}
          <View style={{ flexDirection: 'row', gap: 0 }}>
            <View style={{ flex: 1, paddingRight: 16 }}>
              <Text style={{ color: tokens.text.primary, fontSize: 50, fontWeight: '800', lineHeight: 54, letterSpacing: -2 }}>
                {stats.openReports}
              </Text>
              <Text style={{ color: tokens.text.disabled, fontSize: 11, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 0.8, marginTop: -2 }}>
                Open Issues
              </Text>
            </View>
            <View style={{ width: 1, backgroundColor: tokens.surface.border, marginRight: 16 }} />
            <View style={{ flex: 1, paddingLeft: 0 }}>
              <Text style={{ color: tokens.primary.DEFAULT, fontSize: 50, fontWeight: '800', lineHeight: 54, letterSpacing: -2 }}>
                {stats.resolvedThisMonth}
              </Text>
              <Text style={{ color: tokens.text.disabled, fontSize: 11, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 0.8, marginTop: -2 }}>
                Resolved
              </Text>
            </View>
          </View>
        </View>
      ) : (
        /* Placeholder skeleton before data loads */
        <View style={{ flexDirection: 'row', gap: 20 }}>
          {[1, 2].map((k) => (
            <View key={k}>
              <View style={{ width: 60, height: 50, backgroundColor: tokens.surface.border, borderRadius: 6 }} />
              <View style={{ width: 80, height: 10, backgroundColor: tokens.surface.border, borderRadius: 4, marginTop: 6 }} />
            </View>
          ))}
        </View>
      )}
    </View>
  );
}

/* ── TRENDING STRIP ───────────────────────────────────────────────────────── */
function TrendingStrip({ trending }: { trending: any[] }) {
  if (!trending?.length) return null;
  return (
    <View style={{ paddingLeft: 20, marginBottom: 18, marginTop: 2 }}>
      <Text style={{ color: tokens.text.disabled, fontSize: 10, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
        Trending
      </Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        {trending.map((item) => (
          <View key={item.label} style={{
            borderWidth: 1,
            borderColor: tokens.surface.border,
            borderRadius: 20,
            paddingVertical: 4,
            paddingHorizontal: 10,
            marginRight: 7,
            flexDirection: 'row',
            alignItems: 'center',
            gap: 4,
          }}>
            <Ionicons name={item.icon as any} size={10} color={tokens.text.disabled} />
            <Text style={{ fontSize: 11, color: tokens.text.secondary, fontWeight: '500' }}>{item.label}</Text>
            <Text style={{ fontSize: 11, color: tokens.text.disabled, fontWeight: '600' }}>{item.count}</Text>
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

/* ── SECTION DIVIDER ──────────────────────────────────────────────────────── */
function SectionDivider({ label }: { label: string }) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, marginBottom: 4, marginTop: 8 }}>
      <Text style={{ color: tokens.text.disabled, fontSize: 10, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 1.2 }}>
        {label}
      </Text>
      <View style={{ flex: 1, height: 1, backgroundColor: tokens.surface.border, marginLeft: 10 }} />
    </View>
  );
}

/* ── FEATURED REPORT CARD ─────────────────────────────────────────────────── */
function FeaturedCard({ report, onPress }: { report: Report; onPress: () => void }) {
  const [imgError, setImgError] = useState(false);
  const catIcon  = CATEGORY_ICON[report.category] ?? 'location';
  const statusColor = report.status === 'resolved' ? tokens.success.DEFAULT
    : report.status === 'in_progress' ? tokens.info.DEFAULT
    : tokens.accent.DEFAULT;

  return (
    <TouchableOpacity activeOpacity={0.75} onPress={onPress} style={{ paddingHorizontal: 20, marginBottom: 4 }}>
      <View style={{
        borderRadius: 14,
        overflow:      'hidden',
        backgroundColor: tokens.surface.card,
        shadowColor:   '#000',
        shadowOffset:  { width: 0, height: 1 },
        shadowOpacity: 0.06,
        shadowRadius:  8,
        elevation:     2,
      }}>
        {/* Image area */}
        <View style={{ height: 148, backgroundColor: `${tokens.primary.DEFAULT}10`, overflow: 'hidden' }}>
          {report.images?.length && !imgError ? (
            <Image
              source={{ uri: report.images[0].url }}
              style={{ width: '100%', height: '100%' }}
              onError={() => setImgError(true)}
              resizeMode="cover"
            />
          ) : (
            <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
              <Ionicons name={catIcon as any} size={38} color={tokens.primary.light} />
            </View>
          )}
          {/* Status badge — top left */}
          <View style={{ position: 'absolute', top: 10, left: 10 }}>
            <View style={{
              backgroundColor: statusColor,
              borderRadius: 6,
              paddingHorizontal: 8,
              paddingVertical: 3,
            }}>
              <Text style={{ fontSize: 10, fontWeight: '800', color: '#fff', letterSpacing: 0.3 }}>
                {(report.status ?? 'open').toUpperCase()}
              </Text>
            </View>
          </View>
        </View>

        {/* Content */}
        <View style={{ padding: 14 }}>
          <Text style={{
            color:     tokens.text.primary,
            fontSize:  15,
            fontWeight: '700',
            lineHeight: 20,
            marginBottom: 4,
          }} numberOfLines={2}>
            {report.title}
          </Text>

          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 10 }}>
            <Text style={{ color: tokens.text.secondary, fontSize: 11, textTransform: 'capitalize' }}>
              {report.category}
            </Text>
            <Text style={{ color: tokens.text.disabled, fontSize: 11 }}>·</Text>
            <Text style={{ color: tokens.text.secondary, fontSize: 11 }} numberOfLines={1}>
              {report.location.address ?? 'Pune'}
            </Text>
            <Text style={{ color: tokens.text.disabled, fontSize: 11 }}>·</Text>
            <Text style={{ color: tokens.text.disabled, fontSize: 11 }}>{timeAgo(report.createdAt)}</Text>
          </View>

          <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                <Ionicons name="heart" size={13} color="#ef4444" />
                <Text style={{ fontSize: 12, color: tokens.text.secondary, fontWeight: '600' }}>{report.upvotes}</Text>
              </View>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                <Ionicons name="chatbubble-outline" size={13} color={tokens.text.disabled} />
                <Text style={{ fontSize: 12, color: tokens.text.secondary, fontWeight: '600' }}>{report.commentCount}</Text>
              </View>
            </View>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
              <Ionicons name="person-outline" size={11} color={tokens.text.disabled} />
              <Text style={{ fontSize: 11, color: tokens.text.disabled }}>{report.authorName}</Text>
            </View>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
}

/* ── REPORT ROW (compact list item) ─────────────────────────────────────── */
function ReportRow({ report, onPress }: { report: Report; onPress: () => void }) {
  const [imgError, setImgError] = useState(false);
  const catIcon = CATEGORY_ICON[report.category] ?? 'location';

  return (
    <TouchableOpacity
      activeOpacity={0.75}
      onPress={onPress}
      style={{ paddingHorizontal: 20 }}
    >
      <View style={{
        flexDirection:  'row',
        alignItems:    'stretch',
        gap:           12,
        paddingVertical: 13,
        borderBottomWidth: 1,
        borderBottomColor: tokens.surface.border,
      }}>
        {/* Thumbnail */}
        <View style={{
          width:         72,
          height:        72,
          borderRadius:  10,
          overflow:      'hidden',
          backgroundColor: `${tokens.primary.DEFAULT}0e`,
          flexShrink:   0,
        }}>
          {report.images?.length && !imgError ? (
            <Image
              source={{ uri: report.images[0].url }}
              style={{ width: '100%', height: '100%' }}
              onError={() => setImgError(true)}
              resizeMode="cover"
            />
          ) : (
            <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
              <Ionicons name={catIcon as any} size={22} color={tokens.primary.light} />
            </View>
          )}
        </View>

        {/* Text content */}
        <View style={{ flex: 1, justifyContent: 'space-between' }}>
          <View>
            <Text style={{ color: tokens.text.primary, fontSize: 14, fontWeight: '600', lineHeight: 18 }} numberOfLines={2}>
              {report.title}
            </Text>
            <Text style={{ color: tokens.text.disabled, fontSize: 11, marginTop: 2 }} numberOfLines={1}>
              {report.category} · {report.location.address?.split(',')[0] ?? 'Pune'}
            </Text>
          </View>

          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 6 }}>
            {/* Inline status chip */}
            <View style={{
              backgroundColor: report.status === 'open'      ? tokens.accent.light
                            : report.status === 'resolved' ? tokens.success.light
                            : tokens.info.light,
              borderRadius: 4,
              paddingHorizontal: 6,
              paddingVertical: 1,
            }}>
              <Text style={{
                fontSize:  9,
                fontWeight: '800',
                color:     report.status === 'open'      ? tokens.accent.DEFAULT
                          : report.status === 'resolved' ? tokens.success.DEFAULT
                          : tokens.info.DEFAULT,
                textTransform: 'uppercase',
                letterSpacing: 0.3,
              }}>
                {report.status ?? 'open'}
              </Text>
            </View>

            {/* Meta */}
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 3 }}>
                <Ionicons name="heart-outline" size={11} color={tokens.text.disabled} />
                <Text style={{ fontSize: 11, color: tokens.text.disabled }}>{report.upvotes}</Text>
              </View>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 3 }}>
                <Ionicons name="chatbubble-outline" size={11} color={tokens.text.disabled} />
                <Text style={{ fontSize: 11, color: tokens.text.disabled }}>{report.commentCount}</Text>
              </View>
              <Text style={{ fontSize: 11, color: tokens.text.disabled }}>· {timeAgo(report.createdAt)}</Text>
            </View>
          </View>
        </View>

        {/* Chevron */}
        <View style={{ alignItems: 'center', justifyContent: 'center', paddingLeft: 4 }}>
          <Ionicons name="chevron-forward" size={13} color={tokens.text.disabled} />
        </View>
      </View>
    </TouchableOpacity>
  );
}

/* ── STATE SCREENS ────────────────────────────────────────────────────────── */
function LoadingState() {
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', paddingTop: 60 }}>
      <ActivityIndicator size="large" color={tokens.primary.DEFAULT} />
      <Text style={{ color: tokens.text.secondary, fontSize: 13, marginTop: 14 }}>Loading…</Text>
    </View>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 40 }}>
      <Ionicons name="cloud-offline-outline" size={48} color={tokens.error.DEFAULT} />
      <Text style={{ color: tokens.text.primary, fontWeight: '700', fontSize: 18, marginTop: 16, textAlign: 'center' }}>
        Couldn't load dashboard
      </Text>
      <Text style={{ color: tokens.text.secondary, fontSize: 13, marginTop: 6, textAlign: 'center', lineHeight: 20 }}>
        {message}
      </Text>
      <TouchableOpacity onPress={onRetry} style={{
        backgroundColor: tokens.primary.DEFAULT,
        borderRadius: 24,
        paddingVertical:   12,
        paddingHorizontal: 28,
        marginTop: 22,
      }}>
        <Text style={{ color: '#fff', fontWeight: '700', fontSize: 14 }}>Try again</Text>
      </TouchableOpacity>
    </View>
  );
}

function EmptyState({ onReport }: { onReport: () => void }) {
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 40, paddingTop: 20 }}>
      <Text style={{ fontSize: 68 }}>🏙️</Text>
      <Text style={{ color: tokens.text.primary, fontWeight: '800', fontSize: 19, marginTop: 14, textAlign: 'center' }}>
        No reports yet
      </Text>
      <Text style={{ color: tokens.text.secondary, fontSize: 14, marginTop: 7, textAlign: 'center', lineHeight: 22 }}>
        You haven't filed a civic report yet.{'\n'}Be the first to make a difference.
      </Text>
      <TouchableOpacity
        onPress={onReport}
        style={{
          backgroundColor: tokens.primary.DEFAULT,
          borderRadius: 24,
          paddingVertical:   13,
          paddingHorizontal: 28,
          marginTop: 22,
          shadowColor: tokens.primary.DEFAULT,
          shadowOffset: { width: 0, height: 3 },
          shadowOpacity: 0.3,
          shadowRadius: 6,
          elevation: 4,
        }}
      >
        <Text style={{ color: '#fff', fontWeight: '800', fontSize: 15 }}>Report an Issue</Text>
      </TouchableOpacity>
    </View>
  );
}

/* ── FAB ──────────────────────────────────────────────────────────────────── */
function FAB({ onPress }: { onPress: () => void }) {
  return (
    <TouchableOpacity
      activeOpacity={0.82}
      onPress={onPress}
      style={{
        position:    'absolute',
        right:       20,
        bottom:      32,
        width:       54,
        height:      54,
        borderRadius: 16,
        backgroundColor: tokens.primary.DEFAULT,
        alignItems:  'center',
        justifyContent: 'center',
        shadowColor: tokens.primary.DEFAULT,
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.35,
        shadowRadius: 8,
        elevation: 8,
      }}
    >
      <Ionicons name="add" size={26} color="#fff" />
    </TouchableOpacity>
  );
}

// ─── Screen ──────────────────────────────────────────────────────────────────

export default function DashboardScreen() {
  const router = useRouter();
  const { stats, reports, trending, isLoading, isRefreshing, error, fetchDashboard, refresh } =
    useDashboardStore();

  useEffect(() => { fetchDashboard(); }, []);

  const handleRefresh     = () => refresh();
  const handleReport     = () => { router.push('/create-report'); };
  const handleReportPress = () => { router.push('/create-report'); };

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
        <SectionDivider label={reportCount > 0 ? `Recent Reports · ${reportCount}` : 'Recent Reports'} />

        {reportCount === 0 ? (
          <EmptyState onReport={handleReport} />
        ) : (
          <>
            {/* Large featured card — first report */}
            {featured && <FeaturedCard report={featured} onPress={handleReportPress} />}

            {/* Compact list — remaining reports */}
            {rest.map((r) => (
              <ReportRow key={r.id} report={r} onPress={handleReportPress} />
            ))}

            <View style={{ height: 90 }} />
          </>
        )}
      </ScrollView>

      <FAB onPress={handleReport} />
    </View>
  );
}