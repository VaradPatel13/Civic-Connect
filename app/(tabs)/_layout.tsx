import React from 'react';
import { Tabs } from 'expo-router';
import { Home, FileText, PlusCircle, Bell, User } from 'lucide-react-native';

const HomeIcon = Home as any;
const FileTextIcon = FileText as any;
const PlusCircleIcon = PlusCircle as any;
const BellIcon = Bell as any;
const UserIcon = User as any;

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarStyle: {
          backgroundColor: '#0f172a',
          borderTopColor: '#334155',
          height: 60,
          paddingBottom: 8,
        },
        tabBarActiveTintColor: '#38bdf8',
        tabBarInactiveTintColor: '#64748b',
        headerStyle: { backgroundColor: '#0f172a' },
        headerTintColor: '#f8fafc',
        headerTitleStyle: { fontWeight: 'bold' },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: (props: { color: string }) => <HomeIcon color={props.color} size={22} />,
        }}
      />
      <Tabs.Screen
        name="reports"
        options={{
          title: 'My Reports',
          tabBarIcon: (props: { color: string }) => <FileTextIcon color={props.color} size={22} />,
        }}
      />
      <Tabs.Screen
        name="new-report"
        options={{
          title: 'New Report',
          tabBarIcon: (props: { color: string }) => <PlusCircleIcon color={props.color} size={22} />,
        }}
      />
      <Tabs.Screen
        name="notifications"
        options={{
          title: 'Alerts',
          tabBarIcon: (props: { color: string }) => <BellIcon color={props.color} size={22} />,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: (props: { color: string }) => <UserIcon color={props.color} size={22} />,
        }}
      />
    </Tabs>
  );
}
