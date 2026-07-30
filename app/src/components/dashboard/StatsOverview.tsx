import { StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export function StatsOverview() {
  return (
    <View style={styles.container}>
      <Text style={styles.sectionTitle}>District Overview</Text>

      <View style={styles.statsRow}>
        <View style={styles.statTile}>
          <View style={[styles.iconBox, { backgroundColor: '#FEF2F2' }]}>
            <Ionicons name="alert-circle-outline" size={16} color="#DC2626" />
          </View>
          <Text style={styles.statVal}>24</Text>
          <Text style={styles.statLbl} numberOfLines={1}>Open Reports</Text>
        </View>

        <View style={styles.statTile}>
          <View style={[styles.iconBox, { backgroundColor: '#ECFDF5' }]}>
            <Ionicons name="checkmark-circle-outline" size={16} color="#059669" />
          </View>
          <Text style={styles.statVal}>142</Text>
          <Text style={styles.statLbl} numberOfLines={1}>Fixed (30d)</Text>
        </View>

        <View style={styles.statTile}>
          <View style={[styles.iconBox, { backgroundColor: '#F0F9FF' }]}>
            <Ionicons name="time-outline" size={16} color="#0284C7" />
          </View>
          <Text style={styles.statVal}>4.2h</Text>
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
