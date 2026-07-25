import { View, Text, Platform } from 'react-native';
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { tokens } from '@src/constants';

const TAB_ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
  index:         'home',
  reports:       'document-text',
  notifications: 'notifications-outline',
  profile:       'person',
};

const TAB_BAR_STYLE = {
  height:           64,
  paddingBottom:    Platform.OS === 'ios' ? 20 : 8,
  paddingTop:       8,
  backgroundColor:  tokens.surface.card,
  borderTopWidth:   1,
  borderTopColor:   tokens.surface.border,
  shadowColor:      '#000',
  shadowOffset:     { width: 0, height: -2 },
  shadowOpacity:    0.06,
  shadowRadius:     10,
  elevation:        8,
} as const;

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor:  tokens.primary.DEFAULT,
        tabBarInactiveTintColor: tokens.primary.light,
        tabBarStyle:            TAB_BAR_STYLE,
        tabBarLabelStyle: {
          fontSize:    10,
          fontWeight:  '700',
          marginTop:  2,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title:    'Dashboard',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name={TAB_ICONS['index']} size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="reports"
        options={{
          title:    'Reports',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name={TAB_ICONS['reports']} size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="notifications"
        options={{
          title:    'Alerts',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name={TAB_ICONS['notifications']} size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title:    'Profile',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name={TAB_ICONS['profile']} size={size} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}