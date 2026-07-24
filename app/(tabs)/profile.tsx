import React from 'react';
import { StyleSheet, Text, View, ScrollView, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { useAuthStore } from '../stores/authStore';
import { useSettingsStore } from '../stores/settingsStore';
import { User, Phone, Mail, Globe } from 'lucide-react-native';

const UserIcon = User as any;
const PhoneIcon = Phone as any;
const MailIcon = Mail as any;
const GlobeIcon = Globe as any;

export default function ProfileScreen() {
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const { language, setLanguage } = useSettingsStore();

  const handleLogout = () => {
    Alert.alert('Sign Out', 'Are you sure you want to sign out?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Sign Out',
        style: 'destructive',
        onPress: () => {
          logout();
          router.replace('/(auth)/login');
        },
      },
    ]);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Card style={styles.profileHeader}>
        <View style={styles.avatar}>
          <UserIcon color="#38bdf8" size={36} />
        </View>
        <Text style={styles.name}>{user?.display_name || 'Citizen User'}</Text>
        <Text style={styles.phone}>+{user?.phone || '9876543210'}</Text>
        <View style={styles.badgeWrap}>
          <Badge label={user?.role || 'Citizen'} status="in_progress" />
        </View>
      </Card>

      <Text style={styles.sectionTitle}>Account Details</Text>
      <Card style={styles.card}>
        <View style={styles.infoRow}>
          <PhoneIcon color="#94a3b8" size={20} />
          <Text style={styles.infoLabel}>Mobile Number:</Text>
          <Text style={styles.infoVal}>{user?.phone || '9876543210'}</Text>
        </View>
        <View style={styles.infoRow}>
          <MailIcon color="#94a3b8" size={20} />
          <Text style={styles.infoLabel}>Email Address:</Text>
          <Text style={styles.infoVal}>{user?.email || 'Not provided'}</Text>
        </View>
      </Card>

      <Text style={styles.sectionTitle}>Language Preferences</Text>
      <Card style={styles.card}>
        <View style={styles.langRow}>
          <GlobeIcon color="#38bdf8" size={20} />
          <Text style={styles.langTitle}>Preferred Language</Text>
        </View>

        <View style={styles.btnGroup}>
          <Button
            title="English (EN)"
            variant={language === 'en' ? 'primary' : 'outline'}
            onPress={() => setLanguage('en')}
          />
          <Button
            title="हिन्दी (HI)"
            variant={language === 'hi' ? 'primary' : 'outline'}
            onPress={() => setLanguage('hi')}
          />
          <Button
            title="मराठी (MR)"
            variant={language === 'mr' ? 'primary' : 'outline'}
            onPress={() => setLanguage('mr')}
          />
        </View>
      </Card>

      <Button title="Sign Out of CivicConnect" variant="danger" onPress={handleLogout} />
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
  profileHeader: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  avatar: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#0f172a',
    borderWidth: 2,
    borderColor: '#38bdf8',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  name: {
    fontSize: 22,
    fontWeight: '800',
    color: '#f8fafc',
  },
  phone: {
    fontSize: 14,
    color: '#94a3b8',
    marginTop: 4,
  },
  badgeWrap: {
    marginTop: 10,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#f8fafc',
    marginVertical: 12,
  },
  card: {
    marginBottom: 16,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  infoLabel: {
    color: '#94a3b8',
    fontSize: 14,
    marginLeft: 8,
    width: 110,
  },
  infoVal: {
    color: '#f8fafc',
    fontSize: 14,
    fontWeight: '600',
    flex: 1,
  },
  langRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  langTitle: {
    color: '#f8fafc',
    fontSize: 15,
    fontWeight: '700',
    marginLeft: 8,
  },
  btnGroup: {
    gap: 4,
  },
});
