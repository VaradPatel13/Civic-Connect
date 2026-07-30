/**
 * Login Screen — CivicConnect Mobile
 * Refactored using modular shared auth components.
 */
import { useState } from 'react';
import {
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';

import { useAuthStore } from '@src/store/useAuthStore';
import {
  AuthFooter,
  AuthHeader,
  AuthScreen,
  FormError,
  PrimaryButton,
} from '@src/components/auth';

export default function LoginScreen() {
  const router = useRouter();
  const { login, isLoading } = useAuthStore();

  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const [phoneError, setPhoneError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const [focusedInput, setFocusedInput] = useState<'phone' | 'password' | null>(null);

  function validate(): boolean {
    let isValid = true;
    setPhoneError(null);
    setPasswordError(null);
    setFormError(null);

    const rawPhone = phone.replace(/\D/g, '');
    if (!rawPhone || rawPhone.length !== 10) {
      setPhoneError('Enter a valid 10-digit mobile number');
      isValid = false;
    }

    if (!password || password.length < 8) {
      setPasswordError('Password must be at least 8 characters');
      isValid = false;
    }

    return isValid;
  }

  async function handleLogin() {
    if (!validate()) return;

    const rawPhone = phone.replace(/\D/g, '');
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

    try {
      await login({ phone: rawPhone, password });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      router.replace('/(tabs)');
    } catch (err) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      const msg = err instanceof Error ? err.message : 'Invalid credentials. Please try again.';
      setFormError(msg);
    }
  }

  return (
    <AuthScreen>
      <AuthHeader
        title="Sign in to your account"
        subtitle="Enter your registered mobile number to manage civic reports"
      />

      <FormError message={formError} />

      <View style={styles.formGroup}>
        {/* Phone Number Field */}
        <View style={styles.fieldContainer}>
          <Text style={styles.label}>Mobile Number</Text>
          <View
            style={[
              styles.inputWrapper,
              focusedInput === 'phone' && styles.inputWrapperFocused,
              Boolean(phoneError) && styles.inputWrapperError,
            ]}
          >
            <Text style={styles.countryPrefix}>+91</Text>
            <View style={styles.prefixDivider} />
            <TextInput
              style={styles.textInput}
              placeholder="9876543210"
              placeholderTextColor="#94A3B8"
              keyboardType="phone-pad"
              value={phone}
              onChangeText={(text) => {
                setPhone(text);
                if (phoneError) setPhoneError(null);
              }}
              onFocus={() => setFocusedInput('phone')}
              onBlur={() => setFocusedInput(null)}
              maxLength={10}
              accessibilityLabel="Mobile phone number input"
            />
          </View>
          {phoneError ? <Text style={styles.fieldErrorText}>{phoneError}</Text> : null}
        </View>

        {/* Password Field */}
        <View style={styles.fieldContainer}>
          <Text style={styles.label}>Password</Text>
          <View
            style={[
              styles.inputWrapper,
              focusedInput === 'password' && styles.inputWrapperFocused,
              Boolean(passwordError) && styles.inputWrapperError,
            ]}
          >
            <TextInput
              style={styles.textInput}
              placeholder="Enter your password"
              placeholderTextColor="#94A3B8"
              secureTextEntry={!showPassword}
              value={password}
              onChangeText={(text) => {
                setPassword(text);
                if (passwordError) setPasswordError(null);
              }}
              onFocus={() => setFocusedInput('password')}
              onBlur={() => setFocusedInput(null)}
              accessibilityLabel="Password input"
            />
            <TouchableOpacity
              onPress={() => setShowPassword(!showPassword)}
              style={styles.eyeBtn}
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
              accessibilityLabel={showPassword ? 'Hide password' : 'Show password'}
            >
              <Ionicons
                name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                size={20}
                color="#64748B"
              />
            </TouchableOpacity>
          </View>
          {passwordError ? <Text style={styles.fieldErrorText}>{passwordError}</Text> : null}
        </View>

        {/* Submit Action Button */}
        <PrimaryButton
          title="Sign in"
          onPress={handleLogin}
          isLoading={isLoading}
          accessibilityLabel="Sign in button"
        />
      </View>

      <AuthFooter
        text="Don't have an account?"
        linkText="Create account"
        onPressLink={() => router.push('/signup')}
      />
    </AuthScreen>
  );
}

const styles = StyleSheet.create({
  formGroup: {
    gap: 20,
  },
  fieldContainer: {
    gap: 6,
  },
  label: {
    fontSize: 13,
    fontWeight: '600',
    color: '#334155',
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    height: 48,
    backgroundColor: '#FAFAFA',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 8,
    paddingHorizontal: 14,
  },
  inputWrapperFocused: {
    borderColor: '#059669',
    backgroundColor: '#FFFFFF',
  },
  inputWrapperError: {
    borderColor: '#DC2626',
    backgroundColor: '#FEF2F2',
  },
  countryPrefix: {
    fontSize: 14,
    fontWeight: '600',
    color: '#0F172A',
    marginRight: 10,
  },
  prefixDivider: {
    width: 1,
    height: 20,
    backgroundColor: '#CBD5E1',
    marginRight: 10,
  },
  textInput: {
    flex: 1,
    height: '100%',
    fontSize: 15,
    color: '#0F172A',
  },
  eyeBtn: {
    paddingLeft: 8,
  },
  fieldErrorText: {
    fontSize: 12,
    color: '#DC2626',
    fontWeight: '500',
    marginTop: 2,
  },
});
