/**
 * Signup / Citizen Registration Screen — CivicConnect Mobile
 * Collects full name, phone number, email, and password.
 * Advances to verify-otp upon successful creation.
 */
import { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';

import { tokens } from '@src/constants';
import { useAuthStore } from '@src/store/useAuthStore';

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'mr', label: 'मराठी' },
  { code: 'hi', label: 'हिंदी' },
] as const;

export default function SignupScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { register, isLoading } = useAuthStore();

  const [displayName, setDisplayName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [language, setLanguage] = useState<'en' | 'mr' | 'hi'>('en');
  const [showPassword, setShowPassword] = useState(false);

  async function handleRegister() {
    if (!displayName.trim()) {
      Alert.alert('Name Required', 'Please enter your full name.');
      return;
    }
    const rawPhone = phone.replace(/\D/g, '');
    if (!rawPhone || rawPhone.length !== 10) {
      Alert.alert('Phone Required', 'Please enter a valid 10-digit mobile phone number.');
      return;
    }
    if (!password || password.length < 8) {
      Alert.alert('Password Requirement', 'Password must be at least 8 characters long.');
      return;
    }

    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      await register({
        display_name: displayName.trim(),
        phone: rawPhone,
        email: email.trim() || undefined,
        password,
        preferred_language: language,
      });

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      router.push({
        pathname: '/verify-otp',
        params: { phone: rawPhone, purpose: 'register' },
      });
    } catch (err) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      const msg = err instanceof Error ? err.message : 'Registration failed';
      Alert.alert('Registration Error', msg);
    }
  }

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: tokens.surface.bg }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      {/* Top Header */}
      <View style={[styles.header, { paddingTop: Math.max(insets.top + 8, 44) }]}>
        <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
          <Ionicons name="chevron-back" size={24} color={tokens.text.primary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Create Account</Text>
        <View style={{ width: 36 }} />
      </View>

      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={[
          styles.container,
          { paddingBottom: Math.max(insets.bottom + 30, 40) },
        ]}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.card}>
          <Text style={styles.welcomeTitle}>Join CivicConnect</Text>
          <Text style={styles.welcomeSub}>Report issues, engage with PMC, and improve your city</Text>

          {/* ── Full Name Input ──────────────────────────────────────── */}
          <Text style={styles.label}>Full Name *</Text>
          <View style={styles.inputContainer}>
            <Ionicons name="person-outline" size={20} color={tokens.text.disabled} style={styles.inputIcon} />
            <TextInput
              placeholder="e.g. Ramesh Patil"
              placeholderTextColor={tokens.text.disabled}
              value={displayName}
              onChangeText={setDisplayName}
              style={styles.input}
            />
          </View>

          {/* ── Mobile Phone Input ────────────────────────────────────── */}
          <Text style={styles.label}>Mobile Phone Number *</Text>
          <View style={styles.inputContainer}>
            <Ionicons name="call-outline" size={20} color={tokens.text.disabled} style={styles.inputIcon} />
            <Text style={styles.countryCode}>+91</Text>
            <TextInput
              placeholder="9876543210"
              placeholderTextColor={tokens.text.disabled}
              keyboardType="phone-pad"
              value={phone}
              onChangeText={setPhone}
              maxLength={10}
              style={styles.input}
            />
          </View>

          {/* ── Email Address Input (Optional) ────────────────────────── */}
          <Text style={styles.label}>Email Address (Optional)</Text>
          <View style={styles.inputContainer}>
            <Ionicons name="mail-outline" size={20} color={tokens.text.disabled} style={styles.inputIcon} />
            <TextInput
              placeholder="ramesh@example.com"
              placeholderTextColor={tokens.text.disabled}
              keyboardType="email-address"
              autoCapitalize="none"
              value={email}
              onChangeText={setEmail}
              style={styles.input}
            />
          </View>

          {/* ── Password Input ────────────────────────────────────────── */}
          <Text style={styles.label}>Password *</Text>
          <View style={styles.inputContainer}>
            <Ionicons name="lock-closed-outline" size={20} color={tokens.text.disabled} style={styles.inputIcon} />
            <TextInput
              placeholder="At least 6 characters"
              placeholderTextColor={tokens.text.disabled}
              secureTextEntry={!showPassword}
              value={password}
              onChangeText={setPassword}
              style={styles.input}
            />
            <TouchableOpacity onPress={() => setShowPassword(!showPassword)} style={{ padding: 4 }}>
              <Ionicons
                name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                size={20}
                color={tokens.text.disabled}
              />
            </TouchableOpacity>
          </View>

          {/* ── Preferred Language ────────────────────────────────────── */}
          <Text style={styles.label}>Preferred Language</Text>
          <View style={styles.langRow}>
            {LANGUAGES.map((item) => {
              const active = language === item.code;
              return (
                <TouchableOpacity
                  key={item.code}
                  onPress={() => { setLanguage(item.code); Haptics.selectionAsync(); }}
                  style={[styles.langChip, active ? styles.langChipActive : styles.langChipInactive]}
                >
                  <Text style={[styles.langText, active ? styles.langTextActive : styles.langTextInactive]}>
                    {item.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>

          {/* ── Submit Button ─────────────────────────────────────────── */}
          <TouchableOpacity
            style={[styles.submitBtn, isLoading && styles.submitBtnDisabled]}
            onPress={handleRegister}
            disabled={isLoading}
            activeOpacity={0.85}
          >
            {isLoading ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                <Text style={styles.submitBtnText}>Create Account</Text>
                <Ionicons name="arrow-forward" size={18} color="#fff" />
              </View>
            )}
          </TouchableOpacity>
        </View>

        {/* ── Footer Link to Login ──────────────────────────────────── */}
        <View style={styles.footerRow}>
          <Text style={styles.footerText}>Already have an account? </Text>
          <TouchableOpacity onPress={() => router.push('/login')}>
            <Text style={styles.footerLink}>Sign In</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 18,
    paddingBottom: 14,
    backgroundColor: tokens.surface.card,
    borderBottomWidth: 1,
    borderBottomColor: tokens.surface.border,
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: `${tokens.primary.DEFAULT}0a`,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '900',
    color: tokens.text.primary,
  },

  container: {
    paddingHorizontal: 22,
    paddingTop: 20,
    alignItems: 'center',
  },
  card: {
    width: '100%',
    backgroundColor: tokens.surface.card,
    borderRadius: 24,
    padding: 24,
    borderWidth: 1,
    borderColor: tokens.surface.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 12,
    elevation: 3,
  },
  welcomeTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: tokens.text.primary,
  },
  welcomeSub: {
    fontSize: 13,
    color: tokens.text.secondary,
    marginTop: 4,
    marginBottom: 20,
    lineHeight: 18,
  },

  label: {
    fontSize: 12,
    fontWeight: '800',
    color: tokens.text.disabled,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    marginBottom: 8,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: tokens.surface.bg,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: tokens.surface.border,
    paddingHorizontal: 14,
    height: 52,
    marginBottom: 16,
  },
  inputIcon: {
    marginRight: 10,
  },
  countryCode: {
    fontSize: 15,
    fontWeight: '700',
    color: tokens.text.primary,
    marginRight: 8,
  },
  input: {
    flex: 1,
    fontSize: 15,
    fontWeight: '600',
    color: tokens.text.primary,
  },

  langRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 22,
  },
  langChip: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
  },
  langChipActive: {
    backgroundColor: tokens.primary.DEFAULT,
    borderColor: tokens.primary.DEFAULT,
  },
  langChipInactive: {
    backgroundColor: tokens.surface.bg,
    borderColor: tokens.surface.border,
  },
  langText: {
    fontSize: 13,
    fontWeight: '700',
  },
  langTextActive: {
    color: '#fff',
  },
  langTextInactive: {
    color: tokens.text.primary,
  },

  submitBtn: {
    backgroundColor: tokens.primary.DEFAULT,
    borderRadius: 16,
    height: 54,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: tokens.primary.DEFAULT,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 4,
  },
  submitBtnDisabled: { opacity: 0.6 },
  submitBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '800',
    letterSpacing: 0.3,
  },

  footerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 24,
  },
  footerText: {
    fontSize: 14,
    color: tokens.text.secondary,
  },
  footerLink: {
    fontSize: 14,
    fontWeight: '800',
    color: tokens.primary.DEFAULT,
  },
});
