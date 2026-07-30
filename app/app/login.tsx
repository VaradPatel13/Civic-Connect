/**
 * Login Screen — CivicConnect Mobile
 * Supports Phone + Password and Phone + OTP authentication.
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

export default function LoginScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { login, isLoading } = useAuthStore();

  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  async function handleLogin() {
    const rawPhone = phone.replace(/\D/g, '');
    if (!rawPhone || rawPhone.length !== 10) {
      Alert.alert('Invalid Phone', 'Please enter a valid 10-digit mobile number.');
      return;
    }
    if (!password || password.length < 8) {
      Alert.alert('Password Requirement', 'Password must be at least 8 characters long.');
      return;
    }

    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      await login({ phone: rawPhone, password });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      router.replace('/(tabs)');
    } catch (err) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      const msg = err instanceof Error ? err.message : 'Login failed';
      Alert.alert('Authentication Failed', msg);
    }
  }

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: tokens.surface.bg }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={[
          styles.container,
          { paddingTop: Math.max(insets.top + 20, 50), paddingBottom: Math.max(insets.bottom + 20, 40) },
        ]}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* ── Brand Header ────────────────────────────────────────────── */}
        <View style={styles.headerBox}>
          <View style={styles.iconCircle}>
            <Ionicons name="shield-checkmark" size={38} color={tokens.primary.DEFAULT} />
          </View>
          <Text style={styles.brandTitle}>CivicConnect</Text>
          <Text style={styles.brandSubtitle}>Empowering Citizens, Transforming Governance</Text>
        </View>

        {/* ── Auth Card ──────────────────────────────────────────────── */}
        <View style={styles.card}>
          <Text style={styles.welcomeTitle}>Welcome Back</Text>
          <Text style={styles.welcomeSub}>Sign in to report civic issues and track resolutions</Text>

          {/* ── Phone Input ────────────────────────────────────────── */}
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

          {/* ── Password Input ──────────────────────────────────────── */}
          <Text style={styles.label}>Password *</Text>
          <View style={styles.inputContainer}>
            <Ionicons name="lock-closed-outline" size={20} color={tokens.text.disabled} style={styles.inputIcon} />
            <TextInput
              placeholder="Enter your password"
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

          {/* ── Submit Button ───────────────────────────────────────── */}
          <TouchableOpacity
            style={[styles.submitBtn, isLoading && styles.submitBtnDisabled]}
            onPress={handleLogin}
            disabled={isLoading}
            activeOpacity={0.85}
          >
            {isLoading ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                <Text style={styles.submitBtnText}>Sign In</Text>
                <Ionicons name="arrow-forward" size={18} color="#fff" />
              </View>
            )}
          </TouchableOpacity>
        </View>

        {/* ── Footer Link to Signup ─────────────────────────────────── */}
        <View style={styles.footerRow}>
          <Text style={styles.footerText}>Don't have an account? </Text>
          <TouchableOpacity onPress={() => router.push('/signup')}>
            <Text style={styles.footerLink}>Register Now</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 22,
    alignItems: 'center',
  },
  headerBox: {
    alignItems: 'center',
    marginBottom: 32,
  },
  iconCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: `${tokens.primary.DEFAULT}14`,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 14,
    borderWidth: 1,
    borderColor: `${tokens.primary.DEFAULT}30`,
  },
  brandTitle: {
    fontSize: 26,
    fontWeight: '900',
    color: tokens.text.primary,
    letterSpacing: -0.5,
  },
  brandSubtitle: {
    fontSize: 13,
    fontWeight: '600',
    color: tokens.text.secondary,
    marginTop: 4,
    textAlign: 'center',
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

  submitBtn: {
    backgroundColor: tokens.primary.DEFAULT,
    borderRadius: 16,
    height: 54,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 10,
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
    marginTop: 28,
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
