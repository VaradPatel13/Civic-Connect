import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { DeviceLocation } from '@src/lib/location';

interface LocationCardProps {
  location: DeviceLocation | null;
  loading: boolean;
  onRefresh: () => void;
}

export function LocationCard({ location, loading, onRefresh }: LocationCardProps) {
  const addressText = location?.address || 'Shivajinagar, Ward 12, Pune';
  const accuracyText = location?.accuracy ? `±${location.accuracy.toFixed(0)}m GPS` : 'Live GPS Active';

  return (
    <View style={styles.card}>
      <View style={styles.headerRow}>
        <View style={styles.titleLeft}>
          <View style={styles.iconWrap}>
            <Ionicons name="location" size={16} color="#059669" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.kicker}>CURRENT JURISDICTION</Text>
            <Text style={styles.addressText} numberOfLines={1}>
              {addressText}
            </Text>
          </View>
        </View>

        <TouchableOpacity
          activeOpacity={0.7}
          style={styles.refreshBtn}
          onPress={onRefresh}
          disabled={loading}
          accessibilityLabel="Refresh location"
        >
          {loading ? (
            <ActivityIndicator size="small" color="#059669" />
          ) : (
            <Ionicons name="refresh-outline" size={16} color="#059669" />
          )}
        </TouchableOpacity>
      </View>

      <View style={styles.divider} />

      <View style={styles.footerRow}>
        <Text style={styles.footerHint}>Tap refresh to sync coordinates</Text>
        <View style={styles.accuracyPill}>
          <View style={styles.liveDot} />
          <Text style={styles.accuracyText}>{accuracyText}</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    padding: 14,
    gap: 10,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  titleLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  iconWrap: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: '#ECFDF5',
    borderWidth: 1,
    borderColor: '#A7F3D0',
    alignItems: 'center',
    justifyContent: 'center',
  },
  kicker: {
    fontSize: 9,
    fontWeight: '700',
    color: '#64748B',
    letterSpacing: 0.5,
  },
  addressText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
  },
  refreshBtn: {
    width: 32,
    height: 32,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    backgroundColor: '#FAFAFA',
    alignItems: 'center',
    justifyContent: 'center',
  },
  divider: {
    height: 1,
    backgroundColor: '#F1F5F9',
  },
  footerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  footerHint: {
    fontSize: 11,
    color: '#64748B',
  },
  accuracyPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: '#ECFDF5',
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  liveDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#059669',
  },
  accuracyText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#059669',
  },
});
