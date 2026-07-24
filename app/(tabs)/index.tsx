import React from 'react';
import { StyleSheet, Text, View, ScrollView, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { reportService, rewardService } from '../services';
import { useAuthStore } from '../stores/authStore';
import { PlusCircle, Award, CheckCircle2, Clock } from 'lucide-react-native';
import { ReportItem } from '../types/domain';

const AwardIcon = Award as any;
const PlusCircleIcon = PlusCircle as any;
const ClockIcon = Clock as any;
const CheckCircle2Icon = CheckCircle2 as any;

export default function HomeScreen() {
  const router = useRouter();
  const user = useAuthStore((state: any) => state.user);

  const { data: reports = [] } = useQuery<ReportItem[]>({
    queryKey: ['reports'],
    queryFn: () => reportService.listReports(),
  });

  const { data: rewards } = useQuery({
    queryKey: ['rewards'],
    queryFn: () => rewardService.getSummary(),
  });

  const pendingCount = reports.filter((r: ReportItem) => r.status === 'pending' || r.status === 'triaged').length;
  const resolvedCount = reports.filter((r: ReportItem) => r.status === 'resolved').length;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Welcome Banner */}
      <View style={styles.welcomeBanner}>
        <Text style={styles.greeting}>Namaste, {user?.display_name || 'Citizen'}! 👋</Text>
        <Text style={styles.subGreeting}>Empowering PMC Civic Services</Text>
      </View>

      {/* Rewards Card */}
      <Card style={styles.rewardsCard}>
        <View style={styles.row}>
          <AwardIcon color="#fbbf24" size={32} />
          <View style={styles.rewardTextCol}>
            <Text style={styles.rewardsTitle}>Civic Rewards Points</Text>
            <Text style={styles.rewardPoints}>{rewards?.total_points || user?.points || 0} Points</Text>
          </View>
          <Badge label={rewards?.tier || 'Bronze'} status="pending" />
        </View>
      </Card>

      {/* Quick Action Button */}
      <TouchableOpacity
        style={styles.actionBtn}
        onPress={() => router.push('/(tabs)/new-report')}
        activeOpacity={0.85}
      >
        <PlusCircleIcon color="#ffffff" size={24} />
        <Text style={styles.actionBtnText}>Report a New Civic Issue</Text>
      </TouchableOpacity>

      {/* Stats Section */}
      <View style={styles.statsRow}>
        <Card style={styles.statCard}>
          <ClockIcon color="#60a5fa" size={24} />
          <Text style={styles.statNumber}>{pendingCount}</Text>
          <Text style={styles.statLabel}>Pending</Text>
        </Card>
        <Card style={styles.statCard}>
          <CheckCircle2Icon color="#34d399" size={24} />
          <Text style={styles.statNumber}>{resolvedCount}</Text>
          <Text style={styles.statLabel}>Resolved</Text>
        </Card>
      </View>

      {/* Recent Reports List */}
      <Text style={styles.sectionTitle}>Recent Activity</Text>
      {reports.slice(0, 3).map((item: ReportItem) => (
        <TouchableOpacity
          key={item.id}
          onPress={() => router.push(`/report/${item.id}`)}
          activeOpacity={0.8}
        >
          <Card style={styles.reportCard}>
            <View style={styles.rowBetween}>
              <Text style={styles.reportTitle} numberOfLines={1}>
                {item.title}
              </Text>
              <Badge label={item.status} status={item.status} />
            </View>
            <Text style={styles.reportDesc} numberOfLines={2}>
              {item.description}
            </Text>
            <Text style={styles.reportDate}>{new Date(item.created_at).toLocaleDateString()}</Text>
          </Card>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  content: {
    padding: 16,
  },
  welcomeBanner: {
    marginBottom: 16,
  },
  greeting: {
    fontSize: 24,
    fontWeight: '800',
    color: '#f8fafc',
  },
  subGreeting: {
    fontSize: 14,
    color: '#94a3b8',
    marginTop: 4,
  },
  rewardsCard: {
    backgroundColor: '#1e1b4b',
    borderColor: '#4338ca',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  rowBetween: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  rewardTextCol: {
    flex: 1,
    marginLeft: 12,
  },
  rewardsTitle: {
    fontSize: 13,
    color: '#a5b4fc',
    fontWeight: '600',
  },
  rewardPoints: {
    fontSize: 22,
    fontWeight: '800',
    color: '#fbbf24',
  },
  actionBtn: {
    backgroundColor: '#2563eb',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 14,
    marginVertical: 14,
    gap: 8,
  },
  actionBtnText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
  },
  statsRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  statCard: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 20,
  },
  statNumber: {
    fontSize: 24,
    fontWeight: '800',
    color: '#f8fafc',
    marginVertical: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#94a3b8',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#f8fafc',
    marginVertical: 12,
  },
  reportCard: {
    marginBottom: 10,
  },
  reportTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#f8fafc',
    flex: 1,
    marginRight: 8,
  },
  reportDesc: {
    fontSize: 14,
    color: '#94a3b8',
    marginVertical: 6,
  },
  reportDate: {
    fontSize: 12,
    color: '#64748b',
  },
});
