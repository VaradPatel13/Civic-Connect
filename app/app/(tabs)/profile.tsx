/**
 * Profile — CivicConnect
 *
 * Citizen profile with stats and settings.
 * Same editorial design language as the dashboard.
 */
import {
  View, Text, ScrollView, TouchableOpacity, Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { tokens } from '@src/constants';
import { useAuthStore } from '@src/store/useAuthStore';

// ─── Sub-components ──────────────────────────────────────────────────────────

function Masthead() {
  return (
    <View style={{ paddingHorizontal: 20, paddingTop: 48, paddingBottom: 16 }}>
      <Text style={{ fontSize: 10, fontWeight: '700', color: tokens.text.disabled, textTransform: 'uppercase', letterSpacing: 1.2, marginBottom: 4 }}>
        CivicConnect
      </Text>
      <Text style={{ color: tokens.text.primary, fontSize: 28, fontWeight: '800', lineHeight: 32, letterSpacing: -0.5 }}>
        Profile
      </Text>
    </View>
  );
}

function ProfileCard() {
  const user = useAuthStore((state) => state.user);
  const name = user?.display_name ?? 'Citizen';
  const email = user?.phone ?? 'varad.patel@example.com';
  const role = user?.role ?? 'Citizen';

  const initials = name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase();

  return (
    <View style={{
      marginHorizontal: 20,
      backgroundColor: tokens.surface.card,
      borderRadius: 16,
      padding: 20,
      flexDirection: 'row',
      alignItems: 'center',
      gap: 16,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.06,
      shadowRadius: 8,
      elevation: 2,
    }}>
      {/* Avatar */}
      <View style={{
        width: 64,
        height: 64,
        borderRadius: 16,
        backgroundColor: `${tokens.primary.DEFAULT}18`,
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        <Text style={{ fontSize: 24, fontWeight: '800', color: tokens.primary.DEFAULT, letterSpacing: -0.5 }}>
          {initials || 'C'}
        </Text>
      </View>

      {/* Info */}
      <View style={{ flex: 1 }}>
        <Text style={{ color: tokens.text.primary, fontSize: 18, fontWeight: '800', marginBottom: 2 }}>
          {name}
        </Text>
        <Text style={{ color: tokens.text.secondary, fontSize: 13, marginBottom: 6 }}>
          {email}
        </Text>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
          <View style={{ backgroundColor: tokens.primary.DEFAULT, borderRadius: 20, paddingHorizontal: 8, paddingVertical: 2 }}>
            <Text style={{ fontSize: 10, fontWeight: '800', color: '#fff' }}>{role}</Text>
          </View>
        </View>
      </View>

      <Ionicons name="chevron-forward" size={18} color={tokens.text.disabled} />
    </View>
  );
}

function StatsRow() {
  const stats = [
    { value: '12', label: 'Reports\nFiled'       },
    { value: '7',  label: 'Reports\nResolved'     },
    { value: '850', label: 'Reward\nPoints'        },
  ];

  return (
    <View style={{ marginHorizontal: 20, marginTop: 14 }}>
      <View style={{
        backgroundColor: tokens.primary.DEFAULT,
        borderRadius: 16,
        padding: 20,
        flexDirection: 'row',
      }}>
        {stats.map(({ value, label }, i) => (
          <View key={label} style={{ flex: 1, alignItems: 'center' }}>
            {i > 0 && <View style={{ width: 1, backgroundColor: '#ffffff28', marginHorizontal: 4 }} />}
            <Text style={{ color: '#fff', fontSize: 30, fontWeight: '800', lineHeight: 34, letterSpacing: -1 }}>
              {value}
            </Text>
            <Text style={{ color: '#ffffff90', fontSize: 10, fontWeight: '600', textAlign: 'center', marginTop: 2, lineHeight: 14 }}>
              {label}
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
}

function SettingsGroup({ title, items }: { title?: string; items: { label: string; icon: string; color?: string; badge?: string; onPress: () => void }[] }) {
  return (
    <View style={{ marginTop: 16 }}>
      {title && (
        <View style={{ paddingHorizontal: 20, marginBottom: 6 }}>
          <Text style={{ fontSize: 11, fontWeight: '700', color: tokens.text.disabled, textTransform: 'uppercase', letterSpacing: 1 }}>
            {title}
          </Text>
        </View>
      )}
      <View style={{
        marginHorizontal: 20,
        backgroundColor: tokens.surface.card,
        borderRadius: 14,
        overflow: 'hidden',
      }}>
        {items.map((item, i) => (
          <TouchableOpacity
            key={item.label}
            onPress={item.onPress}
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              gap: 12,
              paddingHorizontal: 16,
              paddingVertical: 14,
              borderBottomWidth: i < items.length - 1 ? 1 : 0,
              borderBottomColor: tokens.surface.border,
            }}
          >
            <View style={{
              width: 34, height: 34, borderRadius: 9,
              backgroundColor: `${item.color ?? tokens.primary.DEFAULT}18`,
              alignItems: 'center', justifyContent: 'center',
            }}>
              <Ionicons name={item.icon as any} size={17} color={item.color ?? tokens.primary.DEFAULT} />
            </View>
            <Text style={{ flex: 1, fontSize: 15, fontWeight: '600', color: tokens.text.primary }}>
              {item.label}
            </Text>
            {item.badge && (
              <View style={{ backgroundColor: tokens.accent.DEFAULT, borderRadius: 10, paddingHorizontal: 7, paddingVertical: 2 }}>
                <Text style={{ fontSize: 10, fontWeight: '800', color: '#fff' }}>{item.badge}</Text>
              </View>
            )}
            <Ionicons name="chevron-forward" size={15} color={tokens.text.disabled} />
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

function SignOutButton() {
  const logout = useAuthStore((state) => state.logout);
  const router = useRouter();

  return (
    <View style={{ marginHorizontal: 20, marginTop: 24, marginBottom: 10 }}>
      <TouchableOpacity
        activeOpacity={0.75}
        onPress={() => Alert.alert('Sign Out', 'Are you sure you want to sign out?', [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Sign Out',
            style: 'destructive',
            onPress: async () => {
              await logout();
              router.replace('/login');
            },
          },
        ])}
        style={{
          backgroundColor: tokens.error.light,
          borderRadius: 14,
          paddingVertical: 15,
          alignItems: 'center',
        }}
      >
        <Text style={{ fontSize: 15, fontWeight: '700', color: tokens.error.DEFAULT }}>
          Sign Out
        </Text>
      </TouchableOpacity>
    </View>
  );
}

function VersionFooter() {
  return (
    <View style={{ alignItems: 'center', paddingBottom: 40, marginTop: 16 }}>
      <Text style={{ fontSize: 11, color: tokens.text.disabled }}>
        CivicConnect v0.1.0 · Pune, India
      </Text>
    </View>
  );
}

// ─── Screen ───────────────────────────────────────────────────────────────────

export default function ProfileScreen() {
  const showSetting = (label: string) => {
    Alert.alert(label, `${label} settings will be updated.`);
  };

  return (
    <View style={{ flex: 1, backgroundColor: tokens.surface.bg }}>
      <ScrollView showsVerticalScrollIndicator={false}>
        <Masthead />
        <ProfileCard />
        <StatsRow />

        {/* Account settings */}
        <SettingsGroup
          title="Account"
          items={[
            { label: 'Edit Profile',    icon: 'person-outline',    color: tokens.primary.DEFAULT, onPress: () => showSetting('Edit Profile') },
            { label: 'Manage Address',  icon: 'location-outline',  color: tokens.accent.DEFAULT,  onPress: () => showSetting('Manage Address') },
          ]}
        />

        {/* Preferences */}
        <SettingsGroup
          title="Preferences"
          items={[
            { label: 'Language',        icon: 'language',             color: tokens.info.DEFAULT,  onPress: () => showSetting('Language') },
            { label: 'Notifications', icon: 'notifications-outline', color: tokens.primary.DEFAULT, badge: '3', onPress: () => showSetting('Notifications') },
            { label: 'Privacy',        icon: 'shield-outline',      color: tokens.success.DEFAULT, onPress: () => showSetting('Privacy') },
          ]}
        />

        {/* Support */}
        <SettingsGroup
          title="Support"
          items={[
            { label: 'Help & FAQ',      icon: 'help-circle-outline', color: tokens.primary.light, onPress: () => showSetting('Help & FAQ') },
            { label: 'Report a Bug',   icon: 'bug-outline',         color: tokens.accent.DEFAULT, onPress: () => showSetting('Report a Bug') },
            { label: 'Rate the App',   icon: 'star-outline',         color: '#f59e0b',             onPress: () => showSetting('Rate the App') },
          ]}
        />

        <SignOutButton />
        <VersionFooter />
      </ScrollView>
    </View>
  );
}