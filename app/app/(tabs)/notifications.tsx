import { useState, useCallback } from 'react';
import {
  View,
  Text,
  SectionList,
  TouchableOpacity,
  RefreshControl,
  StyleSheet,
  useColorScheme,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { TOKENS } from '@src/theme/tokens';
import { useRouter } from 'expo-router';

type NotificationType = 'report_update' | 'comment' | 'status_change' | 'system';
type NotifStatus = 'read' | 'unread';

interface NotificationItem {
  id: string;
  type: NotificationType;
  title: string;
  body: string;
  status: NotifStatus;
  time: string;
  reportId?: string;
}

const TYPE_CONFIG: Record<NotificationType, { icon: string; colorKey: keyof typeof TOKENS.colors.dark }> = {
  report_update: { icon: 'flag', colorKey: 'accentPrimary' },
  comment: { icon: 'chatbubble-ellipses', colorKey: 'accentCyan' },
  status_change: { icon: 'checkmark-circle', colorKey: 'accentLime' },
  system: { icon: 'information-circle', colorKey: 'accentAmber' },
};

function groupByDay(items: NotificationItem[]) {
  const groups: Record<string, NotificationItem[]> = {
    Today: [],
    Yesterday: [],
    Earlier: [],
  };
  items.forEach((item) => {
    if (item.time.endsWith('m') || item.time.endsWith('h')) {
      groups['Today'].push(item);
    } else if (item.time.includes('1d')) {
      groups['Yesterday'].push(item);
    } else {
      groups['Earlier'].push(item);
    }
  });
  return Object.entries(groups)
    .filter(([, data]) => data.length > 0)
    .map(([title, data]) => ({ title, data }));
}

const MOCK_NOTIFS: NotificationItem[] = [
  {
    id: '1',
    type: 'report_update',
    title: 'Ward Officer Dispatched',
    body: 'Pothole report #102 on FC Road has been assigned to Junior Engineer R. Deshmukh.',
    status: 'unread',
    time: '15m',
    reportId: '1',
  },
  {
    id: '2',
    type: 'comment',
    title: 'New Community Comment',
    body: 'Citizen Priya K. commented: "Water level is rising, please expedite repair."',
    status: 'unread',
    time: '2h',
    reportId: '1',
  },
  {
    id: '3',
    type: 'status_change',
    title: 'Work In Progress',
    body: 'Streetlight repair crew is currently on-site on University Road.',
    status: 'unread',
    time: '4h',
    reportId: '2',
  },
  {
    id: '4',
    type: 'system',
    title: 'Civic Points Awarded',
    body: 'You earned +50 XP for verifying a resolved issue in Ward 12.',
    status: 'read',
    time: '1d',
  },
  {
    id: '5',
    type: 'status_change',
    title: 'Issue Resolved & Closed',
    body: 'Drainage blockage near Kothrud Bus Depot has been cleared.',
    status: 'read',
    time: '3d',
    reportId: '3',
  },
];

export default function NotificationsScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';
  const p = isDark ? TOKENS.colors.dark : TOKENS.colors.light;

  const [notifs, setNotifs] = useState<NotificationItem[]>(MOCK_NOTIFS);
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = useCallback(() => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 500);
  }, []);

  const unreadCount = notifs.filter((n) => n.status === 'unread').length;

  const handleMarkAllRead = () => {
    setNotifs((prev) => prev.map((n) => ({ ...n, status: 'read' as NotifStatus })));
  };

  const handlePressItem = (item: NotificationItem) => {
    setNotifs((prev) =>
      prev.map((n) => (n.id === item.id ? { ...n, status: 'read' as NotifStatus } : n)),
    );
    if (item.reportId) {
      router.push({ pathname: '/report-details', params: { id: item.reportId } });
    }
  };

  const grouped = groupByDay(notifs);

  return (
    <View style={[styles.screen, { backgroundColor: p.bg }]}>
      {/* Header Bar */}
      <View style={styles.headerRow}>
        <View>
          <Text style={[styles.kickerText, { color: p.accentPrimary }]}>NOTIFICATIONS</Text>
          <Text style={[styles.headerTitle, { color: p.textPrimary }]}>District Alerts</Text>
        </View>

        {unreadCount > 0 && (
          <TouchableOpacity activeOpacity={0.8} style={[styles.markAllButton, { backgroundColor: p.pillBg }]} onPress={handleMarkAllRead}>
            <Ionicons name="checkmark-done" size={14} color={p.accentPrimary} />
            <Text style={[styles.markAllText, { color: p.accentPrimary }]}>Mark read ({unreadCount})</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Content */}
      {notifs.length === 0 ? (
        <View style={styles.emptyContainer}>
          <View style={[styles.emptyIconCircle, { backgroundColor: p.pillBg }]}>
            <Ionicons name="notifications-off-outline" size={32} color={p.textMuted} />
          </View>
          <Text style={[styles.emptyTitle, { color: p.textPrimary }]}>No active alerts</Text>
          <Text style={[styles.emptySub, { color: p.textSecondary }]}>
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
            <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} tintColor={p.accentPrimary} />
          }
          renderSectionHeader={({ section: { title } }) => (
            <View style={[styles.sectionHeaderWrap, { backgroundColor: p.bg }]}>
              <Text style={[styles.sectionHeaderText, { color: p.textMuted }]}>{title}</Text>
            </View>
          )}
          renderItem={({ item }) => {
            const config = TYPE_CONFIG[item.type];
            const iconColor = p[config.colorKey] as string;
            const isUnread = item.status === 'unread';

            return (
              <TouchableOpacity
                activeOpacity={0.78}
                style={[
                  styles.notifRow,
                  {
                    backgroundColor: isUnread ? `${p.accentPrimary}08` : p.surface,
                    borderColor: isUnread ? `${p.accentPrimary}30` : p.border,
                  },
                ]}
                onPress={() => handlePressItem(item)}>
                <View style={[styles.iconBox, { backgroundColor: `${iconColor}15` }]}>
                  <Ionicons name={config.icon as any} size={18} color={iconColor} />
                </View>

                <View style={styles.textContent}>
                  <View style={styles.titleRow}>
                    <Text style={[styles.notifTitle, { color: p.textPrimary, fontWeight: isUnread ? '800' : '600' }]} numberOfLines={1}>
                      {item.title}
                    </Text>
                    <Text style={[styles.timeText, { color: p.textMuted }]}>{item.time}</Text>
                  </View>

                  <Text style={[styles.notifBody, { color: p.textSecondary }]} numberOfLines={2}>
                    {item.body}
                  </Text>
                </View>

                {isUnread && <View style={[styles.unreadDot, { backgroundColor: p.accentPrimary }]} />}
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
  },
  headerRow: {
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
  markAllButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  markAllText: {
    fontSize: 11,
    fontWeight: '800',
  },

  listContent: {
    paddingHorizontal: 20,
    paddingBottom: 40,
    gap: 8,
  },
  sectionHeaderWrap: {
    paddingVertical: 8,
    marginTop: 8,
  },
  sectionHeaderText: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
    textTransform: 'uppercase',
  },

  notifRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    borderRadius: 16,
    borderWidth: 1,
    padding: 14,
  },
  iconBox: {
    width: 38,
    height: 38,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  textContent: {
    flex: 1,
    gap: 4,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  notifTitle: {
    fontSize: 14,
    flex: 1,
    paddingRight: 8,
  },
  timeText: {
    fontSize: 10,
    fontWeight: '600',
  },
  notifBody: {
    fontSize: 12,
    lineHeight: 17,
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginTop: 4,
  },

  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 40,
    gap: 10,
  },
  emptyIconCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '800',
  },
  emptySub: {
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 18,
  },
});