/**
 * Profile Tab Screen — CivicConnect Mobile
 * Clean, production-grade citizen account portal matching the app design system.
 */
import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';

import { api } from '@src/lib/api';
import { useAuthStore } from '@src/store/useAuthStore';
import type { Report } from '@src/types';

interface RewardSummary {
  total_points: number;
  tier?: string;
}

export default function ProfileScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();

  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [filedCount, setFiledCount] = useState<number>(0);
  const [resolvedCount, setResolvedCount] = useState<number>(0);
  const [pointsCount, setPointsCount] = useState<number>(0);

  const loadProfileData = useCallback(async () => {
    try {
      // 1. Fetch user's filed reports to calculate Filed & Resolved counts
      const userReports = await api.get<Report[]>('/api/v1/reports/?mine_only=true').catch(() => []);
      if (Array.isArray(userReports)) {
        setFiledCount(userReports.length);
        const resolved = userReports.filter(
          (r) => (r.status || '').toLowerCase() === 'resolved'
        ).length;
        setResolvedCount(resolved);
      }

      // 2. Fetch user's actual rewards summary
      const rewardSummary = await api.get<RewardSummary>('/api/v1/rewards/summary').catch(() => null);
      if (rewardSummary?.total_points !== undefined) {
        setPointsCount(rewardSummary.total_points);
      }
    } catch {
      // Keep fallbacks on failure
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    loadProfileData();
  }, [loadProfileData]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadProfileData();
  };

  const displayName = user?.display_name || 'Citizen User';
  const phone = user?.phone || '';
  const trustScore = user?.trust_score ?? 100;
  const isVerified = user?.is_verified ?? false;
  const roleTitle = user?.role ? user.role.toUpperCase() : 'CITIZEN';

  const initials = displayName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase();

  const handleSignOut = () => {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
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
    Haptics.selectionAsync();
    Alert.alert(label, `${label} section accessed.`);
  };

  return (
    <View style={styles.screen}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor="#059669"
          />
        }
        contentContainerStyle={[
          styles.scrollContent,
          { paddingTop: Math.max(insets.top + 6, 40) },
        ]}
      >
        {/* Header */}
        <View style={styles.headerContainer}>
          <Text style={styles.kickerText}>CITIZEN ACCOUNT</Text>
          <Text style={styles.headerTitle}>Profile & Settings</Text>
        </View>

        {/* Profile Card */}
        <View style={styles.profileCard}>
          <View style={styles.avatarBox}>
            <Text style={styles.avatarText}>{initials}</Text>
          </View>

          <View style={styles.profileDetails}>
            <View style={styles.nameRow}>
              <Text style={styles.nameText} numberOfLines={1}>
                {displayName}
              </Text>
              {isVerified ? (
                <Ionicons name="checkmark-circle" size={16} color="#059669" />
              ) : null}
            </View>

            {phone ? <Text style={styles.phoneText}>+91 {phone}</Text> : null}

            <View style={styles.badgeRow}>
              <View style={styles.pillBadgeEmerald}>
                <Text style={styles.pillTextEmerald}>{roleTitle}</Text>
              </View>
              <View style={styles.pillBadgeSlate}>
                <Text style={styles.pillTextSlate}>Score {trustScore}%</Text>
              </View>
            </View>
          </View>
        </View>

        {/* Bento Stats Matrix */}
        <View style={styles.statsMatrix}>
          <View style={styles.statTile}>
            <Ionicons name="document-text-outline" size={18} color="#059669" />
            <Text style={styles.statNum}>{loading ? '-' : filedCount}</Text>
            <Text style={styles.statLabel}>Filed</Text>
          </View>

          <View style={styles.statTile}>
            <Ionicons name="checkmark-circle-outline" size={18} color="#059669" />
            <Text style={styles.statNum}>{loading ? '-' : resolvedCount}</Text>
            <Text style={styles.statLabel}>Resolved</Text>
          </View>

          <View style={styles.statTile}>
            <Ionicons name="trophy-outline" size={18} color="#D97706" />
            <Text style={styles.statNum}>{loading ? '-' : pointsCount}</Text>
            <Text style={styles.statLabel}>Points</Text>
          </View>
        </View>

        {/* Settings Group 1: Account */}
        <View style={styles.settingsSection}>
          <Text style={styles.sectionHeading}>ACCOUNT & LOCATION</Text>
          <View style={styles.groupContainer}>
            <TouchableOpacity style={styles.settingRow} onPress={() => handleSettingTap('Personal Details')}>
              <View style={styles.settingIcon}>
                <Ionicons name="person-outline" size={16} color="#059669" />
              </View>
              <Text style={styles.settingLabel}>Personal Information</Text>
              <Ionicons name="chevron-forward" size={16} color="#94A3B8" />
            </TouchableOpacity>

            <View style={styles.rowDivider} />

            <TouchableOpacity style={styles.settingRow} onPress={() => handleSettingTap('Primary Ward')}>
              <View style={[styles.settingIcon, { backgroundColor: '#F0F9FF' }]}>
                <Ionicons name="location-outline" size={16} color="#0284C7" />
              </View>
              <Text style={styles.settingLabel}>Ward & Jurisdiction</Text>
              <Text style={styles.settingValue}>Pune Central</Text>
              <Ionicons name="chevron-forward" size={16} color="#94A3B8" />
            </TouchableOpacity>
          </View>
        </View>

        {/* Settings Group 2: Preferences */}
        <View style={styles.settingsSection}>
          <Text style={styles.sectionHeading}>PREFERENCES & SECURITY</Text>
          <View style={styles.groupContainer}>
            <TouchableOpacity style={styles.settingRow} onPress={() => handleSettingTap('Language')}>
              <View style={[styles.settingIcon, { backgroundColor: '#FEF3C7' }]}>
                <Ionicons name="language-outline" size={16} color="#D97706" />
              </View>
              <Text style={styles.settingLabel}>App Language</Text>
              <Text style={styles.settingValue}>
                {user?.preferred_language ? user.preferred_language.toUpperCase() : 'ENGLISH'}
              </Text>
              <Ionicons name="chevron-forward" size={16} color="#94A3B8" />
            </TouchableOpacity>

            <View style={styles.rowDivider} />

            <TouchableOpacity style={styles.settingRow} onPress={() => handleSettingTap('Notification Rules')}>
              <View style={styles.settingIcon}>
                <Ionicons name="notifications-outline" size={16} color="#059669" />
              </View>
              <Text style={styles.settingLabel}>Push Dispatch Alerts</Text>
              <Ionicons name="chevron-forward" size={16} color="#94A3B8" />
            </TouchableOpacity>
          </View>
        </View>

        {/* Sign Out Button */}
        <TouchableOpacity
          activeOpacity={0.8}
          style={styles.signOutButton}
          onPress={handleSignOut}
        >
          <Ionicons name="log-out-outline" size={18} color="#DC2626" />
          <Text style={styles.signOutText}>Sign Out Session</Text>
        </TouchableOpacity>

        {/* Footer info */}
        <Text style={styles.footerText}>CivicConnect Mobile v1.2.0 • Pune Municipal Corporation</Text>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingBottom: 40,
    gap: 16,
  },
  headerContainer: {
    marginBottom: 4,
  },
  kickerText: {
    fontSize: 9,
    fontWeight: '700',
    color: '#059669',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#0F172A',
    letterSpacing: -0.4,
  },

  profileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    padding: 14,
    gap: 12,
  },
  avatarBox: {
    width: 52,
    height: 52,
    borderRadius: 12,
    backgroundColor: '#ECFDF5',
    borderWidth: 1,
    borderColor: '#A7F3D0',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#059669',
  },
  profileDetails: {
    flex: 1,
    gap: 2,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  nameText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#0F172A',
  },
  phoneText: {
    fontSize: 12,
    color: '#64748B',
    fontWeight: '500',
  },
  badgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 4,
  },
  pillBadgeEmerald: {
    borderRadius: 6,
    backgroundColor: '#ECFDF5',
    borderWidth: 1,
    borderColor: '#A7F3D0',
    paddingHorizontal: 7,
    paddingVertical: 2,
  },
  pillTextEmerald: {
    fontSize: 10,
    fontWeight: '700',
    color: '#059669',
  },
  pillBadgeSlate: {
    borderRadius: 6,
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    paddingHorizontal: 7,
    paddingVertical: 2,
  },
  pillTextSlate: {
    fontSize: 10,
    fontWeight: '600',
    color: '#64748B',
  },

  statsMatrix: {
    flexDirection: 'row',
    gap: 8,
  },
  statTile: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    paddingVertical: 10,
    paddingHorizontal: 8,
    alignItems: 'center',
    gap: 2,
  },
  statNum: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
  },
  statLabel: {
    fontSize: 10,
    fontWeight: '500',
    color: '#64748B',
  },

  settingsSection: {
    gap: 6,
  },
  sectionHeading: {
    fontSize: 10,
    fontWeight: '700',
    color: '#64748B',
    letterSpacing: 0.8,
  },
  groupContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    overflow: 'hidden',
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    gap: 10,
  },
  settingIcon: {
    width: 30,
    height: 30,
    borderRadius: 8,
    backgroundColor: '#ECFDF5',
    alignItems: 'center',
    justifyContent: 'center',
  },
  settingLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#334155',
    flex: 1,
  },
  settingValue: {
    fontSize: 12,
    fontWeight: '500',
    color: '#64748B',
    marginRight: 4,
  },
  rowDivider: {
    height: 1,
    backgroundColor: '#F1F5F9',
    marginLeft: 50,
  },

  signOutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#FEF2F2',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#FCA5A5',
    paddingVertical: 12,
    marginTop: 4,
  },
  signOutText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#DC2626',
  },
  footerText: {
    textAlign: 'center',
    fontSize: 11,
    color: '#94A3B8',
    marginTop: 6,
  },
});