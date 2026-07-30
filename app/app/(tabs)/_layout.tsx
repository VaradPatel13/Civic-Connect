import { Platform, useColorScheme } from 'react-native';
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { TOKENS } from '@src/theme/tokens';

const TAB_ICONS: Record<string, { focused: keyof typeof Ionicons.glyphMap; unfocused: keyof typeof Ionicons.glyphMap }> = {
  index: { focused: 'grid', unfocused: 'grid-outline' },
  reports: { focused: 'document-text', unfocused: 'document-text-outline' },
  notifications: { focused: 'notifications', unfocused: 'notifications-outline' },
  profile: { focused: 'person', unfocused: 'person-outline' },
};

export default function TabLayout() {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';
  const p = isDark ? TOKENS.colors.dark : TOKENS.colors.light;

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: p.accentPrimary,
        tabBarInactiveTintColor: p.textMuted,
        tabBarStyle: {
          height: Platform.OS === 'ios' ? 84 : 64,
          paddingBottom: Platform.OS === 'ios' ? 24 : 10,
          paddingTop: 8,
          backgroundColor: p.surface,
          borderTopWidth: 1,
          borderTopColor: p.border,
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