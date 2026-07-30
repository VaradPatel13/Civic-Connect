/**
 * OTP Verification Screen — CivicConnect Mobile
 * Verifies 6-digit verification code sent via SMS/WhatsApp.
 */
import { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';

import { tokens } from '@src/constants';
import { useAuthStore } from '@src/store/useAuthStore';

export default function VerifyOTPScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const params = useLocalSearchParams<{ phone?: string; purpose?: string }>();
  const { verifyOTP, isLoading } = useAuthStore();

  const phone = (params.phone ?? '9876543210').replace(/\D/g, '');
  const purpose = params.purpose ?? 'register';
  const [code, setCode] = useState('');

  async function handleVerify() {
    if (!code || code.trim().length < 4) {
      Alert.alert('Invalid Code', 'Please enter the verification code sent to your phone.');
      return;
    }

    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      await verifyOTP({ phone, code: code.trim(), purpose });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      Alert.alert('Verification Successful', 'Your account has been verified!', [
        { text: 'Continue', onPress: () => router.replace('/(tabs)') },
      ]);
    } catch (err) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      const msg = err instanceof Error ? err.message : 'Verification failed';
      Alert.alert('Verification Error', msg);
    }
  }

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: tokens.surface.bg }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <View style={[styles.header, { paddingTop: Math.max(insets.top + 8, 44) }]}>
        <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
          <Ionicons name="chevron-back" size={24} color={tokens.text.primary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Verify OTP</Text>
        <View style={{ width: 36 }} />
      </View>

      <View style={styles.container}>
        <View style={styles.card}>
          <View style={styles.iconCircle}>
            <Ionicons name="key-outline" size={32} color={tokens.primary.DEFAULT} />
          </View>

          <Text style={styles.title}>Enter Verification Code</Text>
          <Text style={styles.subTitle}>
            We have sent a verification code to{' '}
            <Text style={{ fontWeight: '800', color: tokens.text.primary }}>{phone}</Text>
          </Text>

          {/* ── OTP Input ─────────────────────────────────────────────── */}
          <View style={styles.otpInputBox}>
            <TextInput
              placeholder="123456"
              placeholderTextColor={tokens.text.disabled}
              keyboardType="number-pad"
              maxLength={6}
              value={code}
              onChangeText={setCode}
              style={styles.otpText}
              autoFocus
            />
          </View>

          {/* ── Submit Button ─────────────────────────────────────────── */}
          <TouchableOpacity
            style={[styles.submitBtn, isLoading && styles.submitBtnDisabled]}
            onPress={handleVerify}
            disabled={isLoading}
            activeOpacity={0.85}
          >
            {isLoading ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                <Text style={styles.submitBtnText}>Verify Code</Text>
                <Ionicons name="checkmark-circle" size={18} color="#fff" />
              </View>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.resendBtn}
            onPress={() => Alert.alert('OTP Sent', 'A new verification code has been dispatched.')}
          >
            <Text style={styles.resendText}>Resend Code</Text>
          </TouchableOpacity>
        </View>
      </View>
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
    flex: 1,
    paddingHorizontal: 22,
    paddingTop: 36,
    alignItems: 'center',
  },
  card: {
    width: '100%',
    backgroundColor: tokens.surface.card,
    borderRadius: 24,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: tokens.surface.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 12,
    elevation: 3,
  },
  iconCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: `${tokens.primary.DEFAULT}14`,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 20,
    fontWeight: '800',
    color: tokens.text.primary,
    marginBottom: 8,
  },
  subTitle: {
    fontSize: 13,
    color: tokens.text.secondary,
    textAlign: 'center',
    lineHeight: 18,
    marginBottom: 24,
  },

  otpInputBox: {
    width: '100%',
    height: 56,
    backgroundColor: tokens.surface.bg,
    borderRadius: 16,
    borderWidth: 1.5,
    borderColor: tokens.primary.DEFAULT,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  otpText: {
    fontSize: 24,
    fontWeight: '900',
    color: tokens.text.primary,
    letterSpacing: 8,
    textAlign: 'center',
    width: '100%',
  },

  submitBtn: {
    width: '100%',
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

  resendBtn: {
    marginTop: 18,
    padding: 8,
  },
  resendText: {
    fontSize: 13,
    fontWeight: '700',
    color: tokens.primary.DEFAULT,
  },
});
