import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Alert,
  StyleSheet,
  useColorScheme,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { TOKENS } from '@src/theme/tokens';
import { useAuthStore } from '@src/store/useAuthStore';

export default function ProfileScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';
  const p = isDark ? TOKENS.colors.dark : TOKENS.colors.light;

  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  const displayName = user?.display_name ?? 'Active Citizen';
  const phone = user?.phone ?? '8007182716';
  const trustScore = user?.trust_score ?? 94;
  const isVerified = user?.is_verified ?? true;

  const initials = displayName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase();

  const handleSignOut = () => {
    Alert.alert('Sign Out', 'Are you sure you want to log out of CivicConnect?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Sign Out',
        style: 'destructive',
        onPress: async () => {
          await logout();
          router.replace('/login');
        },
      },
    ]);
  };

  const handleSettingTap = (label: string) => {
    Alert.alert(label, `${label} preferences updated.`);
  };

  return (
    <View style={[styles.screen, { backgroundColor: p.bg }]}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.headerContainer}>
          <Text style={[styles.kickerText, { color: p.accentPrimary }]}>CITIZEN PROFILE</Text>
          <Text style={[styles.headerTitle, { color: p.textPrimary }]}>Account & Impact</Text>
        </View>

        {/* Profile Card */}
        <View style={[styles.profileCard, { backgroundColor: p.surface, borderColor: p.border }]}>
          <View style={[styles.avatarBox, { backgroundColor: `${p.accentPrimary}20` }]}>
            <Text style={[styles.avatarText, { color: p.accentPrimary }]}>{initials}</Text>
          </View>

          <View style={styles.profileDetails}>
            <View style={styles.nameRow}>
              <Text style={[styles.nameText, { color: p.textPrimary }]} numberOfLines={1}>
                {displayName}
              </Text>
              {isVerified && <Ionicons name="checkmark-circle" size={16} color={p.accentCyan} />}
            </View>

            <Text style={[styles.phoneText, { color: p.textSecondary }]}>+91 {phone}</Text>

            <View style={styles.badgeRow}>
              <View style={[styles.pillBadge, { backgroundColor: `${p.accentLime}20`, borderColor: `${p.accentLime}40` }]}>
                <Text style={[styles.pillText, { color: p.accentLime }]}>Ward 12 Guardian</Text>
              </View>
              <View style={[styles.pillBadge, { backgroundColor: p.pillBg, borderColor: p.border }]}>
                <Text style={[styles.pillText, { color: p.textSecondary }]}>Score {trustScore}%</Text>
              </View>
            </View>
          </View>
        </View>

        {/* Bento Stats Matrix */}
        <View style={styles.statsMatrix}>
          <View style={[styles.statTile, { backgroundColor: p.surface, borderColor: p.border }]}>
            <Ionicons name="document-text-outline" size={20} color={p.accentPrimary} />
            <Text style={[styles.statNum, { color: p.textPrimary }]}>14</Text>
            <Text style={[styles.statLabel, { color: p.textSecondary }]}>Filed</Text>
          </View>

          <View style={[styles.statTile, { backgroundColor: p.surface, borderColor: p.border }]}>
            <Ionicons name="checkmark-done-circle-outline" size={20} color={p.accentLime} />
            <Text style={[styles.statNum, { color: p.textPrimary }]}>11</Text>
            <Text style={[styles.statLabel, { color: p.textSecondary }]}>Resolved</Text>
          </View>

          <View style={[styles.statTile, { backgroundColor: p.surface, borderColor: p.border }]}>
            <Ionicons name="trophy-outline" size={20} color={p.accentAmber} />
            <Text style={[styles.statNum, { color: p.textPrimary }]}>850</Text>
            <Text style={[styles.statLabel, { color: p.textSecondary }]}>Points</Text>
          </View>
        </View>

        {/* Settings Group 1: Dispatch Account */}
        <View style={styles.settingsSection}>
          <Text style={[styles.sectionHeading, { color: p.textMuted }]}>ACCOUNT & LOCATION</Text>
          <View style={[styles.groupContainer, { backgroundColor: p.surface, borderColor: p.border }]}>
            <TouchableOpacity style={styles.settingRow} onPress={() => handleSettingTap('Personal Details')}>
              <View style={[styles.settingIcon, { backgroundColor: `${p.accentPrimary}15` }]}>
                <Ionicons name="person-outline" size={16} color={p.accentPrimary} />
              </View>
              <Text style={[styles.settingLabel, { color: p.textPrimary }]}>Personal Information</Text>
              <Ionicons name="chevron-forward" size={16} color={p.textMuted} />
            </TouchableOpacity>

            <View style={[styles.rowDivider, { backgroundColor: p.border }]} />

            <TouchableOpacity style={styles.settingRow} onPress={() => handleSettingTap('Primary Ward')}>
              <View style={[styles.settingIcon, { backgroundColor: `${p.accentCyan}15` }]}>
                <Ionicons name="location-outline" size={16} color={p.accentCyan} />
              </View>
              <Text style={[styles.settingLabel, { color: p.textPrimary }]}>Ward & Jurisdiction</Text>
              <Text style={[styles.settingValue, { color: p.textMuted }]}>Shivajinagar</Text>
              <Ionicons name="chevron-forward" size={16} color={p.textMuted} />
            </TouchableOpacity>
          </View>
        </View>

        {/* Settings Group 2: App Preferences */}
        <View style={styles.settingsSection}>
          <Text style={[styles.sectionHeading, { color: p.textMuted }]}>PREFERENCES & SECURITY</Text>
          <View style={[styles.groupContainer, { backgroundColor: p.surface, borderColor: p.border }]}>
            <TouchableOpacity style={styles.settingRow} onPress={() => handleSettingTap('Language')}>
              <View style={[styles.settingIcon, { backgroundColor: `${p.accentAmber}15` }]}>
                <Ionicons name="language-outline" size={16} color={p.accentAmber} />
              </View>
              <Text style={[styles.settingLabel, { color: p.textPrimary }]}>App Language</Text>
              <Text style={[styles.settingValue, { color: p.textMuted }]}>English</Text>
              <Ionicons name="chevron-forward" size={16} color={p.textMuted} />
            </TouchableOpacity>

            <View style={[styles.rowDivider, { backgroundColor: p.border }]} />

            <TouchableOpacity style={styles.settingRow} onPress={() => handleSettingTap('Notification Rules')}>
              <View style={[styles.settingIcon, { backgroundColor: `${p.accentLime}15` }]}>
                <Ionicons name="notifications-outline" size={16} color={p.accentLime} />
              </View>
              <Text style={[styles.settingLabel, { color: p.textPrimary }]}>Push Dispatch Alerts</Text>
              <Ionicons name="chevron-forward" size={16} color={p.textMuted} />
            </TouchableOpacity>
          </View>
        </View>

        {/* Sign Out Button */}
        <TouchableOpacity activeOpacity={0.8} style={[styles.signOutButton, { backgroundColor: `${p.accentRose}15`, borderColor: `${p.accentRose}30` }]} onPress={handleSignOut}>
          <Ionicons name="log-out-outline" size={18} color={p.accentRose} />
          <Text style={[styles.signOutText, { color: p.accentRose }]}>Sign Out Session</Text>
        </TouchableOpacity>

        {/* Footer info */}
        <Text style={[styles.footerText, { color: p.textMuted }]}>CivicConnect Mobile v1.2.0 • Pune City Ward 12</Text>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
  },
  scrollContent: {
    paddingTop: Platform.select({ ios: 56, android: 44 }) ?? 44,
    paddingHorizontal: 20,
    paddingBottom: 40,
    gap: 20,
  },
  headerContainer: {},
  kickerText: {
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 0.8,
    marginBottom: 2,
  },
  headerTitle: {
    fontSize: 26,
    fontWeight: '800',
    letterSpacing: -0.5,
  },

  profileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 20,
    borderWidth: 1,
    padding: 16,
    gap: 14,
  },
  avatarBox: {
    width: 60,
    height: 60,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 22,
    fontWeight: '900',
  },
  profileDetails: {
    flex: 1,
    gap: 4,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  nameText: {
    fontSize: 17,
    fontWeight: '800',
  },
  phoneText: {
    fontSize: 12,
    fontWeight: '500',
  },
  badgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 4,
  },
  pillBadge: {
    borderRadius: 10,
    borderWidth: 1,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  pillText: {
    fontSize: 9,
    fontWeight: '800',
  },

  statsMatrix: {
    flexDirection: 'row',
    gap: 10,
  },
  statTile: {
    flex: 1,
    borderRadius: 16,
    borderWidth: 1,
    paddingVertical: 14,
    paddingHorizontal: 12,
    alignItems: 'center',
    gap: 4,
  },
  statNum: {
    fontSize: 18,
    fontWeight: '900',
  },
  statLabel: {
    fontSize: 10,
    fontWeight: '600',
  },

  settingsSection: {
    gap: 8,
  },
  sectionHeading: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
  },
  groupContainer: {
    borderRadius: 18,
    borderWidth: 1,
    overflow: 'hidden',
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    gap: 12,
  },
  settingIcon: {
    width: 32,
    height: 32,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  settingLabel: {
    fontSize: 14,
    fontWeight: '600',
    flex: 1,
  },
  settingValue: {
    fontSize: 12,
    fontWeight: '500',
    marginRight: 4,
  },
  rowDivider: {
    height: 1,
    marginLeft: 58,
  },

  signOutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderRadius: 16,
    borderWidth: 1,
    paddingVertical: 14,
    marginTop: 8,
  },
  signOutText: {
    fontSize: 14,
    fontWeight: '800',
  },
  footerText: {
    textAlign: 'center',
    fontSize: 10,
    fontWeight: '500',
    marginTop: 10,
  },
});