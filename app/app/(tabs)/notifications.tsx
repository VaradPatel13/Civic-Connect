import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  RefreshControl,
  SectionList,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';

import { api } from '@src/lib/api';

type NotificationType = 'report_update' | 'comment' | 'status_change' | 'system';
type NotifStatus = 'read' | 'unread';

interface BackendNotification {
  id: string;
  title: string;
  message: string;
  notification_type: string;
  read_at: string | null;
  report_id: string | null;
  created_at: string;
}

interface NotificationItem {
  id: string;
  type: NotificationType;
  title: string;
  body: string;
  status: NotifStatus;
  time: string;
  createdAt: Date;
  reportId?: string;
}

const TYPE_CONFIG: Record<NotificationType, { icon: keyof typeof Ionicons.glyphMap; color: string; bg: string }> = {
  report_update: { icon: 'flag-outline', color: '#059669', bg: '#ECFDF5' },
  comment: { icon: 'chatbubble-ellipses-outline', color: '#0284C7', bg: '#F0F9FF' },
  status_change: { icon: 'checkmark-circle-outline', color: '#059669', bg: '#ECFDF5' },
  system: { icon: 'information-circle-outline', color: '#D97706', bg: '#FEF3C7' },
};

function formatTimeAgo(dateStr: string): string {
  const now = new Date();
  const created = new Date(dateStr);
  const diffMs = Math.max(0, now.getTime() - created.getTime());
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 60) return `${Math.max(1, diffMins)}m`;
  if (diffHours < 24) return `${diffHours}h`;
  return `${diffDays}d`;
}

function mapNotificationType(rawType: string): NotificationType {
  const t = (rawType || '').toLowerCase();
  if (t === 'report_update') return 'report_update';
  if (t === 'resolution' || t === 'status_change') return 'status_change';
  if (t === 'comment' || t === 'assignment') return 'comment';
  return 'system';
}

function groupByDay(items: NotificationItem[]) {
  const groups: Record<string, NotificationItem[]> = {
    Today: [],
    Yesterday: [],
    Earlier: [],
  };
  items.forEach((item) => {
    if (item.time.endsWith('m') || item.time.endsWith('h')) {
      groups['Today'].push(item);
    } else if (item.time === '1d') {
      groups['Yesterday'].push(item);
    } else {
      groups['Earlier'].push(item);
    }
  });
  return Object.entries(groups)
    .filter(([, data]) => data.length > 0)
    .map(([title, data]) => ({ title, data }));
}

export default function NotificationsScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();

  const [notifs, setNotifs] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchNotifications = useCallback(async () => {
    try {
      const data = await api.get<BackendNotification[]>('/api/v1/notifications/');
      if (Array.isArray(data)) {
        const mapped: NotificationItem[] = data.map((n) => ({
          id: n.id,
          type: mapNotificationType(n.notification_type),
          title: n.title,
          body: n.message,
          status: n.read_at ? 'read' : 'unread',
          time: formatTimeAgo(n.created_at),
          createdAt: new Date(n.created_at),
          reportId: n.report_id || undefined,
        }));
        setNotifs(mapped);
      } else {
        setNotifs([]);
      }
    } catch {
      setNotifs([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const handleRefresh = useCallback(() => {
    setRefreshing(true);
    fetchNotifications();
  }, [fetchNotifications]);

  const unreadCount = notifs.filter((n) => n.status === 'unread').length;

  const handleMarkAllRead = async () => {
    Haptics.selectionAsync();
    const unreadIds = notifs.filter((n) => n.status === 'unread').map((n) => n.id);
    setNotifs((prev) => prev.map((n) => ({ ...n, status: 'read' as NotifStatus })));

    if (unreadIds.length > 0) {
      try {
        await api.post('/api/v1/notifications/read', { notification_ids: unreadIds });
      } catch {
        // Ignored
      }
    }
  };

  const handlePressItem = async (item: NotificationItem) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    if (item.status === 'unread') {
      setNotifs((prev) =>
        prev.map((n) => (n.id === item.id ? { ...n, status: 'read' as NotifStatus } : n)),
      );
      try {
        await api.post('/api/v1/notifications/read', { notification_ids: [item.id] });
      } catch {
        // Ignored
      }
    }

    if (item.reportId) {
      router.push({ pathname: '/report-details', params: { id: item.reportId } });
    }
  };

  const grouped = groupByDay(notifs);

  return (
    <View style={styles.screen}>
      {/* Header Bar */}
      <View style={[styles.headerRow, { paddingTop: Math.max(insets.top + 6, 40) }]}>
        <View>
          <Text style={styles.kickerText}>DISTRICT ALERTS</Text>
          <Text style={styles.headerTitle}>Notifications</Text>
        </View>

        {unreadCount > 0 && (
          <TouchableOpacity
            activeOpacity={0.8}
            style={styles.markAllButton}
            onPress={handleMarkAllRead}
          >
            <Ionicons name="checkmark-done" size={14} color="#059669" />
            <Text style={styles.markAllText}>Mark read ({unreadCount})</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Content List */}
      {loading ? (
        <View style={styles.emptyContainer}>
          <ActivityIndicator size="large" color="#059669" />
          <Text style={styles.emptySub}>Fetching district notifications...</Text>
        </View>
      ) : notifs.length === 0 ? (
        <View style={styles.emptyContainer}>
          <View style={styles.emptyIconCircle}>
            <Ionicons name="notifications-off-outline" size={28} color="#059669" />
          </View>
          <Text style={styles.emptyTitle}>No active alerts</Text>
          <Text style={styles.emptySub}>
            When officers update your reported issues, real-time alerts will show up here.
          </Text>
        </View>
      ) : (
        <SectionList
          sections={grouped}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={handleRefresh}
              tintColor="#059669"
            />
          }
          renderSectionHeader={({ section: { title } }) => (
            <View style={styles.sectionHeaderWrap}>
              <Text style={styles.sectionHeaderText}>{title}</Text>
            </View>
          )}
          renderItem={({ item }) => {
            const config = TYPE_CONFIG[item.type];
            const isUnread = item.status === 'unread';

            return (
              <TouchableOpacity
                activeOpacity={0.78}
                style={[
                  styles.notifRow,
                  isUnread && styles.notifRowUnread,
                ]}
                onPress={() => handlePressItem(item)}
              >
                <View style={[styles.iconBox, { backgroundColor: config.bg }]}>
                  <Ionicons name={config.icon} size={18} color={config.color} />
                </View>

                <View style={styles.textContent}>
                  <View style={styles.titleRow}>
                    <Text
                      style={[
                        styles.notifTitle,
                        isUnread && styles.notifTitleUnread,
                      ]}
                      numberOfLines={1}
                    >
                      {item.title}
                    </Text>
                    <Text style={styles.timeText}>{item.time}</Text>
                  </View>

                  <Text style={styles.notifBody} numberOfLines={2}>
                    {item.body}
                  </Text>
                </View>

                {isUnread && <View style={styles.unreadDot} />}
              </TouchableOpacity>
            );
          }}
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
  headerRow: {
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
  markAllButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#ECFDF5',
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderWidth: 1,
    borderColor: '#A7F3D0',
  },
  markAllText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#059669',
  },

  listContent: {
    paddingHorizontal: 20,
    paddingBottom: 40,
    gap: 8,
  },
  sectionHeaderWrap: {
    paddingVertical: 10,
  },
  sectionHeaderText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#64748B',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },

  notifRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    padding: 12,
    marginBottom: 8,
  },
  notifRowUnread: {
    backgroundColor: '#FAFAFA',
    borderColor: '#A7F3D0',
  },
  iconBox: {
    width: 36,
    height: 36,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  textContent: {
    flex: 1,
    gap: 2,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  notifTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#334155',
    flex: 1,
    paddingRight: 6,
  },
  notifTitleUnread: {
    fontWeight: '700',
    color: '#0F172A',
  },
  timeText: {
    fontSize: 11,
    color: '#64748B',
    fontWeight: '500',
  },
  notifBody: {
    fontSize: 12,
    color: '#475569',
    lineHeight: 17,
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#059669',
    marginTop: 4,
  },

  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 40,
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
    lineHeight: 17,
  },
});