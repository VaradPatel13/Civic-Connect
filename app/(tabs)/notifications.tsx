import React from 'react';
import { StyleSheet, Text, View, FlatList, ActivityIndicator } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { Card } from '../components/ui/Card';
import { notificationService } from '../services';
import { Bell } from 'lucide-react-native';

const BellIcon = Bell as any;

export default function NotificationsScreen() {
  const { data: notifications = [], isLoading, refetch } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationService.listNotifications(),
  });

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Civic Alerts & Updates</Text>

      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#38bdf8" />
        </View>
      ) : (
        <FlatList
          data={notifications}
          keyExtractor={(item) => item.id}
          onRefresh={refetch}
          refreshing={isLoading}
          contentContainerStyle={styles.listContent}
          ListEmptyComponent={
            <View style={styles.center}>
              <BellIcon color="#64748b" size={40} />
              <Text style={styles.emptyText}>No notifications yet.</Text>
            </View>
          }
          renderItem={({ item }) => (
            <Card style={styles.card}>
              <Text style={styles.title}>{item.title}</Text>
              <Text style={styles.msg}>{item.message}</Text>
              <Text style={styles.time}>{new Date(item.created_at).toLocaleString()}</Text>
            </Card>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
    paddingHorizontal: 16,
  },
  header: {
    fontSize: 20,
    fontWeight: '800',
    color: '#f8fafc',
    marginVertical: 16,
  },
  listContent: {
    paddingBottom: 24,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 60,
  },
  emptyText: {
    color: '#94a3b8',
    fontSize: 16,
    marginTop: 12,
  },
  card: {
    marginBottom: 10,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: '#38bdf8',
  },
  msg: {
    fontSize: 14,
    color: '#cbd5e1',
    marginVertical: 6,
  },
  time: {
    fontSize: 11,
    color: '#64748b',
  },
});
