import React from 'react';
import { StyleSheet, Text, View, FlatList, TouchableOpacity, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { reportService } from '../services';

export default function ReportsScreen() {
  const router = useRouter();

  const { data: reports = [], isLoading, refetch } = useQuery({
    queryKey: ['my_reports'],
    queryFn: () => reportService.listReports(),
  });

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Track Civic Issues</Text>

      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#38bdf8" />
        </View>
      ) : (
        <FlatList
          data={reports}
          keyExtractor={(item) => item.id}
          onRefresh={refetch}
          refreshing={isLoading}
          contentContainerStyle={styles.listContent}
          ListEmptyComponent={
            <View style={styles.center}>
              <Text style={styles.emptyText}>No civic reports found.</Text>
            </View>
          }
          renderItem={({ item }) => (
            <TouchableOpacity
              onPress={() => router.push(`/report/${item.id}`)}
              activeOpacity={0.8}
            >
              <Card style={styles.card}>
                <View style={styles.rowBetween}>
                  <Text style={styles.title} numberOfLines={1}>
                    {item.title}
                  </Text>
                  <Badge label={item.status} status={item.status} />
                </View>

                <Text style={styles.categoryTag}>Category: {item.issue_category.toUpperCase()}</Text>

                <Text style={styles.desc} numberOfLines={2}>
                  {item.description}
                </Text>

                {item.address && (
                  <Text style={styles.address} numberOfLines={1}>
                    📍 {item.address}
                  </Text>
                )}

                <Text style={styles.date}>Reported on: {new Date(item.created_at).toLocaleString()}</Text>
              </Card>
            </TouchableOpacity>
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
  },
  card: {
    marginBottom: 12,
  },
  rowBetween: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: '#f8fafc',
    flex: 1,
    marginRight: 8,
  },
  categoryTag: {
    fontSize: 12,
    fontWeight: '600',
    color: '#38bdf8',
    marginVertical: 4,
  },
  desc: {
    fontSize: 14,
    color: '#cbd5e1',
    marginVertical: 6,
  },
  address: {
    fontSize: 12,
    color: '#94a3b8',
    marginVertical: 2,
  },
  date: {
    fontSize: 11,
    color: '#64748b',
    marginTop: 8,
  },
});
