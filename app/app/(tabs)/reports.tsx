/**
 * Reports — CivicConnect
 *
 * Editorial list of all reports filed by the citizen.
 * Follows the same design language as the dashboard.
 *
 * Data flow: Component → ReportsStore → Real Backend API
 */
import { useEffect, useState } from 'react';
import {
  View, Text, FlatList, TouchableOpacity,
  RefreshControl, ActivityIndicator, Image, Dimensions,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { tokens } from '@src/constants';
import type { Report } from '@src/types';

// ─── UI-only constants ───────────────────────────────────────────────────────

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

const FILTER_TABS = ['All', 'Open', 'In Progress', 'Resolved'] as const;
type FilterTab = typeof FILTER_TABS[number];

// ─── Helpers ─────────────────────────────────────────────────────────────────

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins  = Math.floor(diff / 60_000);
  if (mins < 60)  return `${mins} m`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24)   return `${hrs} h`;
  return `${Math.floor(hrs / 24)} d`;
}

// ─── Header ──────────────────────────────────────────────────────────────────

function Masthead() {
  return (
    <View style={{ paddingHorizontal: 20, paddingTop: 48, paddingBottom: 16 }}>
      <Text style={{ fontSize: 10, fontWeight: '700', color: tokens.text.disabled, textTransform: 'uppercase', letterSpacing: 1.2, marginBottom: 4 }}>
        CivicConnect
      </Text>
      <Text style={{ color: tokens.text.primary, fontSize: 28, fontWeight: '800', lineHeight: 32, letterSpacing: -0.5 }}>
        My Reports
      </Text>
    </View>
  );
}

// ─── Filter Tabs ─────────────────────────────────────────────────────────────

function FilterBar({ selected, onChange }: { selected: FilterTab; onChange: (t: FilterTab) => void }) {
  return (
    <View style={{ paddingHorizontal: 20, marginBottom: 16 }}>
      <View style={{
        flexDirection: 'row',
        backgroundColor: tokens.surface.border,
        borderRadius: 10,
        padding: 3,
      }}>
        {FILTER_TABS.map((tab) => {
          const active = tab === selected;
          return (
            <TouchableOpacity
              key={tab}
              onPress={() => onChange(tab)}
              style={{
                flex: 1,
                paddingVertical: 7,
                borderRadius: 8,
                backgroundColor: active ? tokens.surface.card : 'transparent',
                alignItems: 'center',
              }}
            >
              <Text style={{
                fontSize: 12,
                fontWeight: '700',
                color: active ? tokens.primary.DEFAULT : tokens.text.secondary,
              }}>
                {tab}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

// ─── Report Card ──────────────────────────────────────────────────────────────

function ReportCard({ report, onPress }: { report: Report; onPress: () => void }) {
  const [imgError, setImgError] = useState(false);
  const catIcon = CATEGORY_ICON[report.category] ?? 'location';
  const statusColor = report.status === 'resolved' ? tokens.success.DEFAULT
    : report.status === 'in_progress' ? tokens.info.DEFAULT
    : tokens.accent.DEFAULT;

  const firstImg = report.images?.[0];
  const imageUrl = typeof firstImg === 'string' ? firstImg : firstImg?.url;

  return (
    <TouchableOpacity activeOpacity={0.75} onPress={onPress} style={{ marginBottom: 6 }}>
      <View style={{
        marginHorizontal: 20,
        borderRadius: 14,
        overflow: 'hidden',
        backgroundColor: tokens.surface.card,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.06,
        shadowRadius: 8,
        elevation: 2,
      }}>
        {/* Image */}
        <View style={{ height: 130, backgroundColor: `${tokens.primary.DEFAULT}10`, overflow: 'hidden' }}>
          {Boolean(imageUrl) && !imgError ? (
            <Image
              source={{ uri: imageUrl }}
              style={{ width: '100%', height: '100%' }}
              onError={() => setImgError(true)}
              resizeMode="cover"
            />
          ) : (
            <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
              <Ionicons name={catIcon as any} size={34} color={tokens.primary.light} />
            </View>
          )}
          {/* Status */}
          <View style={{ position: 'absolute', top: 10, left: 10 }}>
            <View style={{ backgroundColor: statusColor, borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3 }}>
              <Text style={{ fontSize: 10, fontWeight: '800', color: '#fff', letterSpacing: 0.3 }}>
                {(report.status ?? 'open').toUpperCase()}
              </Text>
            </View>
          </View>
        </View>

        {/* Text */}
        <View style={{ padding: 14 }}>
          <Text style={{
            color: tokens.text.primary,
            fontSize: 15,
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
              {report.location?.address ?? 'Pune'}
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
              <Ionicons name="person-outline" size={12} color={tokens.text.disabled} />
              <Text style={{ fontSize: 11, color: tokens.text.disabled }}>{report.authorName}</Text>
            </View>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
}

// ─── State Screens ───────────────────────────────────────────────────────────

function LoadingState() {
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
      <ActivityIndicator size="large" color={tokens.primary.DEFAULT} />
    </View>
  );
}

function EmptyState({ filter }: { filter: FilterTab }) {
  const messages: Record<FilterTab, string> = {
    All:        "You haven't filed any reports yet.",
    Open:       "No open reports.",
    'In Progress': "No reports in progress.",
    Resolved:   "No resolved reports yet.",
  };
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 40, marginTop: 40 }}>
      <Text style={{ fontSize: 52 }}>📋</Text>
      <Text style={{ color: tokens.text.primary, fontWeight: '700', fontSize: 17, marginTop: 14, textAlign: 'center' }}>
        {messages[filter]}
      </Text>
      <Text style={{ color: tokens.text.secondary, fontSize: 13, marginTop: 6, textAlign: 'center', lineHeight: 20 }}>
        When you file a civic report, it will appear here.
      </Text>
    </View>
  );
}

// ─── FAB ──────────────────────────────────────────────────────────────────────

function FAB({ onPress }: { onPress: () => void }) {
  return (
    <TouchableOpacity
      activeOpacity={0.82}
      onPress={onPress}
      style={{
        position: 'absolute',
        right: 20,
        bottom: 32,
        width: 54,
        height: 54,
        borderRadius: 16,
        backgroundColor: tokens.primary.DEFAULT,
        alignItems: 'center',
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

// ─── Screen ───────────────────────────────────────────────────────────────────

const MOCK_REPORTS: Report[] = [
  {
    id: '1',
    title: 'Large pothole near FC Road junction — dangerous after rain',
    description: '',
    category: 'pothole',
    status: 'open',
    location: { lat: 18.5167, lng: 73.8563, address: 'FC Road, Shivajinagar, Pune' },
    images: [],
    authorId: 'u1',
    authorName: 'You',
    upvotes: 14,
    commentCount: 3,
    isUpvoted: false,
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: '2',
    title: 'Streetlight not working for 3 weeks on University Road',
    description: '',
    category: 'streetlight',
    status: 'in_progress',
    location: { lat: 18.5333, lng: 73.8667, address: 'University Road, Pune' },
    images: [],
    authorId: 'u1',
    authorName: 'You',
    upvotes: 8,
    commentCount: 1,
    isUpvoted: false,
    createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: '3',
    title: 'Drainage overflowing near Kothrud bus stop',
    description: '',
    category: 'drainage',
    status: 'resolved',
    location: { lat: 18.5084, lng: 73.8077, address: 'Kothrud, Pune' },
    images: [],
    authorId: 'u1',
    authorName: 'You',
    upvotes: 22,
    commentCount: 7,
    isUpvoted: false,
    createdAt: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
  },
];

export default function ReportsScreen() {
  const router = useRouter();
  const [filter, setFilter] = useState<FilterTab>('All');
  const [refreshing, setRefreshing] = useState(false);
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchReports = async () => {
    try {
      const baseUrl = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${baseUrl}/api/v1/reports/`);
      if (res.ok) {
        const data = await res.json();
        setReports(Array.isArray(data) ? data : []);
      }
    } catch {
      setReports([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchReports();
  };

  const filtered = reports.filter((r) => {
    if (filter === 'All')          return true;
    if (filter === 'Open' && (r.status === 'open' || r.status === 'pending'))  return true;
    if (filter === 'In Progress' && (r.status === 'in_progress' || r.status === 'assigned')) return true;
    if (filter === 'Resolved' && r.status === 'resolved') return true;
    return false;
  });

  return (
    <View style={{ flex: 1, backgroundColor: tokens.surface.bg }}>
      <Masthead />
      <FilterBar selected={filter} onChange={setFilter} />

      {reports.length === 0 ? (
        <EmptyState filter={filter} />
      ) : (
        <FlatList
          data={filtered}
          keyExtractor={(item) => item.id}
          contentContainerStyle={{ paddingBottom: 90 }}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={handleRefresh}
              tintColor={tokens.primary.DEFAULT}
            />
          }
          ListEmptyComponent={<EmptyState filter={filter} />}
          renderItem={({ item }) => (
            <ReportCard
              report={item}
              onPress={() => router.push({ pathname: '/report-details', params: { id: item.id } })}
            />
          )}
        />
      )}

      <FAB onPress={() => router.push('/create-report')} />
    </View>
  );
}