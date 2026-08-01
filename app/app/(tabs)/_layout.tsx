import { Platform, StyleSheet, Text, TouchableOpacity, View, useColorScheme } from 'react-native';
import { Tabs, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { TOKENS } from '@src/theme/tokens';

const TAB_ICONS: Record<string, { focused: keyof typeof Ionicons.glyphMap; unfocused: keyof typeof Ionicons.glyphMap }> = {
  index: { focused: 'grid', unfocused: 'grid-outline' },
  reports: { focused: 'document-text', unfocused: 'document-text-outline' },
  notifications: { focused: 'notifications', unfocused: 'notifications-outline' },
  profile: { focused: 'person', unfocused: 'person-outline' },
};

export default function TabLayout() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';
  const p = isDark ? TOKENS.colors.dark : TOKENS.colors.light;

  const activeColor = p.accentPrimary;
  const inactiveColor = isDark ? '#64748B' : '#64748B';

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: activeColor,
        tabBarInactiveTintColor: inactiveColor,
        tabBarStyle: {
          height: Platform.OS === 'ios' ? 84 : 64,
          paddingBottom: Platform.OS === 'ios' ? 24 : 10,
          paddingTop: 8,
          backgroundColor: p.surface,
          borderTopWidth: 1,
          borderTopColor: isDark ? 'rgba(255, 255, 255, 0.08)' : '#E2E8F0',
          elevation: 10,
        },
        tabBarLabelStyle: {
          fontSize: 10,
          fontWeight: '700',
          marginTop: 2,
        },
      }}>
      <Tabs.Screen
        name="index"
        options={{
          title: 'Dashboard',
          tabBarIcon: ({ color, focused }) => (
            <Ionicons name={focused ? TAB_ICONS.index.focused : TAB_ICONS.index.unfocused} size={22} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="reports"
        options={{
          title: 'Reports',
          tabBarIcon: ({ color, focused }) => (
            <Ionicons name={focused ? TAB_ICONS.reports.focused : TAB_ICONS.reports.unfocused} size={22} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="create"
        options={{
          title: 'Report',
          tabBarButton: () => (
            <TouchableOpacity
              activeOpacity={0.85}
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
                router.push('/camera');
              }}
              style={styles.centerFabContainer}
              accessibilityRole="button"
              accessibilityLabel="Report a civic issue"
            >
              <View style={[styles.centerFabCircle, { borderColor: isDark ? '#1E293B' : '#FFFFFF' }]}>
                <Ionicons name="camera" size={22} color="#FFFFFF" />
              </View>
              <Text style={styles.centerFabLabel}>Report</Text>
            </TouchableOpacity>
          ),
        }}
      />
      <Tabs.Screen
        name="notifications"
        options={{
          title: 'Alerts',
          tabBarIcon: ({ color, focused }) => (
            <Ionicons name={focused ? TAB_ICONS.notifications.focused : TAB_ICONS.notifications.unfocused} size={22} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color, focused }) => (
            <Ionicons name={focused ? TAB_ICONS.profile.focused : TAB_ICONS.profile.unfocused} size={22} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  centerFabContainer: {
    top: -14,
    justifyContent: 'center',
    alignItems: 'center',
    width: 68,
  },
  centerFabCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#059669',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#059669',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 8,
    elevation: 8,
    borderWidth: 3,
  },
  centerFabLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: '#059669',
    marginTop: 2,
  },
});