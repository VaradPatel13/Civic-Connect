/**
 * Notifications / Alerts — CivicConnect
 *
 * Shows update notifications for civic reports.
 * Same editorial design language as the dashboard.
 */
import { useState } from 'react';
import {
  View, Text, SectionList, TouchableOpacity,
  RefreshControl, ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { tokens } from '@src/constants';

// ─── Types ────────────────────────────────────────────────────────────────────

type NotificationType = 'report_update' | 'comment' | 'status_change' | 'system';
type NotifStatus     = 'read' | 'unread';

interface NotificationItem {
  id: string;
  type:       NotificationType;
  title:      string;
  body:       string;
  status:     NotifStatus;
  time:       string;
  reportId?:  string;
}

// ─── UI helpers ──────────────────────────────────────────────────────────────

const TYPE_ICON: Record<NotificationType, { name: string; color: string }> = {
  report_update:  { name: 'flag',           color: tokens.accent.DEFAULT  },
  comment:        { name: 'chatbubble-ellipses', color: tokens.info.DEFAULT  },
  status_change:  { name: 'checkmark-circle', color: tokens.success.DEFAULT },
  system:         { name: 'information-circle', color: tokens.primary.light },
};

type Section = { title: string; data: NotificationItem[] };

function groupByDay(items: NotificationItem[]): Section[] {
  const groups: Record<string, NotificationItem[]> = {
    Today: [], Yesterday: [], Earlier: [],
  };
  items.forEach((item) => {
    const val = parseInt(item.time, 10);
    if (item.time.endsWith('m') || item.time.endsWith('h')) {
      groups['Today'].push(item);
    } else if (item.time.endsWith('d') && val === 1) {
      groups['Yesterday'].push(item);
    } else {
      groups['Earlier'].push(item);
    }
  });
  return Object.entries(groups)
    .filter(([, data]) => data.length > 0)
    .map(([title, data]) => ({ title, data }));
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function Masthead() {
  return (
    <View style={{ paddingHorizontal: 20, paddingTop: 48, paddingBottom: 16 }}>
      <Text style={{ fontSize: 10, fontWeight: '700', color: tokens.text.disabled, textTransform: 'uppercase', letterSpacing: 1.2, marginBottom: 4 }}>
        CivicConnect
      </Text>
      <Text style={{ color: tokens.text.primary, fontSize: 28, fontWeight: '800', lineHeight: 32, letterSpacing: -0.5 }}>
        Alerts
      </Text>
    </View>
  );
}

function SectionHeader({ title }: { title: string }) {
  return (
    <View style={{
      paddingHorizontal: 20,
      paddingTop: 16,
      paddingBottom: 6,
      backgroundColor: tokens.surface.bg,
    }}>
      <Text style={{ fontSize: 11, fontWeight: '700', color: tokens.text.disabled, textTransform: 'uppercase', letterSpacing: 1 }}>
        {title}
      </Text>
    </View>
  );
}

function NotificationRow({ item }: { item: NotificationItem }) {
  const { name: iconName, color } = TYPE_ICON[item.type];
  const isUnread = item.status === 'unread';

  return (
    <TouchableOpacity activeOpacity={0.72} style={{
      flexDirection: 'row',
      alignItems:   'flex-start',
      gap:          12,
      paddingHorizontal: 20,
      paddingVertical:   13,
      backgroundColor: isUnread ? `${tokens.primary.DEFAULT}06` : tokens.surface.card,
      borderBottomWidth: 1,
      borderBottomColor: tokens.surface.border,
    }}>
      {/* Icon */}
      <View style={{
        width: 38, height: 38,
        borderRadius: 10,
        backgroundColor: `${color}18`,
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
      }}>
        <Ionicons name={iconName as any} size={18} color={color} />
      </View>

      {/* Content */}
      <View style={{ flex: 1 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 2 }}>
          <Text style={{
            fontSize:      14,
            fontWeight:    isUnread ? '700' : '600',
            color:         tokens.text.primary,
            flex:          1,
          }} numberOfLines={1}>
            {item.title}
          </Text>
          {isUnread && (
            <View style={{ width: 7, height: 7, borderRadius: 3.5, backgroundColor: tokens.primary.DEFAULT, marginLeft: 8 }} />
          )}
        </View>
        <Text style={{ fontSize: 13, color: tokens.text.secondary, lineHeight: 18, marginBottom: 4 }} numberOfLines={2}>
          {item.body}
        </Text>
        <Text style={{ fontSize: 11, color: tokens.text.disabled }}>{item.time}</Text>
      </View>
    </TouchableOpacity>
  );
}

function EmptyState() {
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 40, paddingTop: 60 }}>
      <Text style={{ fontSize: 56 }}>🔔</Text>
      <Text style={{ color: tokens.text.primary, fontWeight: '700', fontSize: 17, marginTop: 14, textAlign: 'center' }}>
        No alerts yet
      </Text>
      <Text style={{ color: tokens.text.secondary, fontSize: 13, marginTop: 6, textAlign: 'center', lineHeight: 20 }}>
        When your reports get updates,{'\n'}we'll notify you here.
      </Text>
    </View>
  );
}

function MarkAllButton({ onPress }: { onPress: () => void }) {
  return (
    <TouchableOpacity onPress={onPress} style={{ paddingHorizontal: 20, paddingBottom: 8 }}>
      <Text style={{ fontSize: 13, fontWeight: '600', color: tokens.primary.light }}>
        Mark all as read
      </Text>
    </TouchableOpacity>
  );
}

// ─── Mock data ───────────────────────────────────────────────────────────────

const MOCK_NOTIFS: NotificationItem[] = [
  {
    id: '1', type: 'report_update',
    title: 'Report Acknowledged',
    body: 'Your pothole report on FC Road has been received by PMC.',
    status: 'unread', time: '10m', reportId: '1',
  },
  {
    id: '2', type: 'comment',
    title: 'New Comment',
    body: 'Rahul M. commented: "Still there, getting worse after rain."',
    status: 'unread', time: '2h', reportId: '1',
  },
  {
    id: '3', type: 'status_change',
    title: 'Work Started',
    body: 'Your streetlight report on University Road is now being worked on.',
    status: 'unread', time: '5h', reportId: '2',
  },
  {
    id: '4', type: 'report_update',
    title: 'Report Assigned',
    body: 'Your drainage issue has been assigned to the Kothrud ward office.',
    status: 'unread', time: '1d', reportId: '3',
  },
  {
    id: '5', type: 'status_change',
    title: 'Report Resolved',
    body: 'Your drainage report near Kothrud bus stop has been resolved.',
    status: 'read', time: '7d', reportId: '3',
  },
];

// ─── Screen ───────────────────────────────────────────────────────────────────

const sections = groupByDay(MOCK_NOTIFS);

export default function NotificationsScreen() {
  const [refreshing, setRefreshing] = useState(false);
  const [notifs, setNotifs] = useState<NotificationItem[]>(MOCK_NOTIFS);

  const handleRefresh = () => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 600);
  };

  const unreadCount = notifs.filter((n) => n.status === 'unread').length;
  const groupedSections = groupByDay(notifs);

  return (
    <View style={{ flex: 1, backgroundColor: tokens.surface.bg }}>
      <Masthead />

      {unreadCount > 0 && (
        <MarkAllButton onPress={() => {
          setNotifs((prev) => prev.map((n) => ({ ...n, status: 'read' as NotifStatus })));
        }} />
      )}

      {notifs.length === 0 ? (
        <EmptyState />
      ) : (
        <SectionList
          sections={groupedSections}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => <NotificationRow item={item} />}
          renderSectionHeader={({ section: { title } }) => <SectionHeader title={title} />}
          contentContainerStyle={{ paddingBottom: 30 }}
          showsVerticalScrollIndicator={false}
          stickySectionHeadersEnabled={false}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={handleRefresh}
              tintColor={tokens.primary.DEFAULT}
            />
          }
        />
      )}
    </View>
  );
}