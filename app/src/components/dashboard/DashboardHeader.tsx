import { Image, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

interface DashboardHeaderProps {
  title?: string;
  subtitle?: string;
  onNotificationPress: () => void;
}

export function DashboardHeader({
  title = 'CivicConnect',
  subtitle = 'District 12 Portal',
  onNotificationPress,
}: DashboardHeaderProps) {
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.header, { paddingTop: Math.max(insets.top + 6, 40) }]}>
      <View style={styles.brandRow}>
        <View style={styles.logoBadge}>
          <Image
            source={require('../../../assets/images/civic_logo.png')}
            style={styles.logoImage}
            resizeMode="contain"
          />
        </View>
        <View>
          <Text style={styles.title}>{title}</Text>
          <Text style={styles.subtitle}>{subtitle}</Text>
        </View>
      </View>

      <TouchableOpacity
        style={styles.actionBtn}
        onPress={onNotificationPress}
        activeOpacity={0.7}
        accessibilityLabel="Notifications"
      >
        <Ionicons name="notifications-outline" size={20} color="#0F172A" />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingBottom: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  logoBadge: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: '#ECFDF5',
    borderWidth: 1,
    borderColor: '#A7F3D0',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoImage: {
    width: 22,
    height: 22,
    borderRadius: 4,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: '#0F172A',
    letterSpacing: -0.3,
  },
  subtitle: {
    fontSize: 11,
    color: '#64748B',
    fontWeight: '500',
  },
  actionBtn: {
    width: 36,
    height: 36,
    borderRadius: 8,
    backgroundColor: '#F8FAFC',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
});
