import { StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useDashboardStore } from '@src/store';
import type { DashboardStats } from '@src/types';

interface StatsOverviewProps {
  stats?: DashboardStats | null;
  isLoading?: boolean;
}

function formatSLA(avgDays?: number | null): string {
  if (avgDays == null) return 'N/A';
  if (avgDays <= 0) return '< 1h';
  const hours = avgDays * 24;
  if (hours < 24) {
    return `${hours.toFixed(1)}h`;
  }
  return `${avgDays.toFixed(1)}d`;
}

export function StatsOverview({ stats: propStats, isLoading: propLoading }: StatsOverviewProps = {}) {
  const storeStats = useDashboardStore((state) => state.stats);
  const storeLoading = useDashboardStore((state) => state.isLoading);

  const stats = propStats ?? storeStats;
  const isLoading = propLoading ?? storeLoading;

  const openCount = isLoading && !stats ? '...' : (stats?.openReports ?? 0);
  const fixedCount = isLoading && !stats ? '...' : (stats?.resolvedThisMonth ?? 0);
  const slaText = isLoading && !stats ? '...' : formatSLA(stats?.avgResolutionDays);

  return (
    <View style={styles.container}>
      <Text style={styles.sectionTitle}>District Overview</Text>

      <View style={styles.statsRow}>
        <View style={styles.statTile}>
          <View style={[styles.iconBox, { backgroundColor: '#FEF2F2' }]}>
            <Ionicons name="alert-circle-outline" size={16} color="#DC2626" />
          </View>
          <Text style={styles.statVal}>{openCount}</Text>
          <Text style={styles.statLbl} numberOfLines={1}>Open Reports</Text>
        </View>

        <View style={styles.statTile}>
          <View style={[styles.iconBox, { backgroundColor: '#ECFDF5' }]}>
            <Ionicons name="checkmark-circle-outline" size={16} color="#059669" />
          </View>
          <Text style={styles.statVal}>{fixedCount}</Text>
          <Text style={styles.statLbl} numberOfLines={1}>Fixed (30d)</Text>
        </View>

        <View style={styles.statTile}>
          <View style={[styles.iconBox, { backgroundColor: '#F0F9FF' }]}>
            <Ionicons name="time-outline" size={16} color="#0284C7" />
          </View>
          <Text style={styles.statVal}>{slaText}</Text>
          <Text style={styles.statLbl} numberOfLines={1}>Avg SLA</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 10,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
    letterSpacing: -0.3,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  statTile: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 6,
  },
  iconBox: {
    width: 28,
    height: 28,
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
  },
  statVal: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
  },
  statLbl: {
    fontSize: 10,
    color: '#64748B',
    fontWeight: '500',
    textAlign: 'center',
  },
});
