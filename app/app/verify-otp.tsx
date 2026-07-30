/**
 * OTP Verification Screen — CivicConnect Mobile
 * Refactored using modular shared auth components and 6-digit OTPInput box design.
 */
import { useEffect, useState } from 'react';
import {
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import * as Haptics from 'expo-haptics';

import { useAuthStore } from '@src/store/useAuthStore';
import { api } from '@src/lib/api';
import {
  AuthHeader,
  AuthScreen,
  FormError,
  OTPInput,
  PrimaryButton,
} from '@src/components/auth';

export default function VerifyOTPScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ phone?: string; purpose?: string }>();
  const { verifyOTP, isLoading } = useAuthStore();

  const phone = (params.phone ?? '9876543210').replace(/\D/g, '');
  const purpose = params.purpose ?? 'register';

  const [code, setCode] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [resendCountdown, setResendCountdown] = useState(30);
  const [isResending, setIsResending] = useState(false);
  const [resendSuccess, setResendSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (resendCountdown <= 0) return;
    const timer = setInterval(() => {
      setResendCountdown((prev) => prev - 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [resendCountdown]);

  async function handleVerify(otpToVerify?: string) {
    const finalCode = otpToVerify || code;
    if (!finalCode || finalCode.trim().length < 6) {
      setFormError('Please enter the complete 6-digit verification code.');
      return;
    }

    setFormError(null);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      await verifyOTP({ phone, code: finalCode.trim(), purpose });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      router.replace('/(tabs)');
    } catch (err) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      const msg = err instanceof Error ? err.message : 'Verification failed. Invalid code.';
      setFormError(msg);
    }
  }

  async function handleResendCode() {
    if (resendCountdown > 0 || isResending) return;

    setIsResending(true);
    setFormError(null);
    setResendSuccess(null);

    try {
      await api.post<unknown>(`/auth/request-otp?phone=${encodeURIComponent(phone)}&purpose=${encodeURIComponent(purpose)}`, {});
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setResendSuccess('A new 6-digit verification code has been dispatched.');
      setResendCountdown(30);
    } catch (err) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      const msg = err instanceof Error ? err.message : 'Failed to resend code. Please try again.';
      setFormError(msg);
    } finally {
      setIsResending(false);
    }
  }

  return (
    <AuthScreen showBackHeader headerTitle="Verify OTP">
      <AuthHeader
        title="Enter Verification Code"
        subtitle={`We have sent a 6-digit code to +91 ${phone}`}
        iconName="shield-checkmark-outline"
      />

      <FormError message={formError} />

      {resendSuccess ? (
        <View style={styles.successBanner}>
          <Text style={styles.successText}>{resendSuccess}</Text>
        </View>
      ) : null}

      <View style={styles.formGroup}>
        {/* 6-Digit Box Input */}
        <OTPInput
          length={6}
          value={code}
          onChange={(newCode) => {
            setCode(newCode);
            if (formError) setFormError(null);
          }}
          onComplete={(completedCode) => handleVerify(completedCode)}
        />

        {/* Submit Verification Action */}
        <PrimaryButton
          title="Verify code"
          onPress={() => handleVerify()}
          isLoading={isLoading}
          disabled={code.length < 6}
          accessibilityLabel="Verify code button"
        />
      </View>

      {/* Resend OTP Section */}
      <View style={styles.resendContainer}>
        <Text style={styles.resendLabel}>Didn't receive the code?</Text>
        <TouchableOpacity
          onPress={handleResendCode}
          disabled={resendCountdown > 0 || isResending}
          activeOpacity={0.7}
        >
          <Text
            style={[
              styles.resendLink,
              (resendCountdown > 0 || isResending) && styles.resendLinkDisabled,
            ]}
          >
            {isResending
              ? 'Resending...'
              : resendCountdown > 0
              ? `Resend code in ${resendCountdown}s`
              : 'Resend code'}
          </Text>
        </TouchableOpacity>
      </View>
    </AuthScreen>
  );
}

const styles = StyleSheet.create({
  formGroup: {
    gap: 16,
  },
  successBanner: {
    backgroundColor: '#ECFDF5',
    borderWidth: 1,
    borderColor: '#A7F3D0',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginBottom: 20,
  },
  successText: {
    fontSize: 13,
    color: '#065F46',
    fontWeight: '500',
  },
  resendContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 32,
    gap: 6,
  },
  resendLabel: {
    fontSize: 14,
    color: '#64748B',
  },
  resendLink: {
    fontSize: 14,
    fontWeight: '600',
    color: '#059669',
  },
  resendLinkDisabled: {
    color: '#94A3B8',
  },
});
