/**
 * Signup / Citizen Registration Screen — CivicConnect Mobile
 * Refactored using modular shared auth components.
 */
import { useEffect, useState } from 'react';
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

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'mr', label: 'मराठी' },
  { code: 'hi', label: 'हिंदी' },
] as const;

export default function SignupScreen() {
  const router = useRouter();
  const { register, isLoading, isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      router.replace('/(tabs)');
    }
  }, [isAuthenticated, router]);

  const [displayName, setDisplayName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [language, setLanguage] = useState<'en' | 'mr' | 'hi'>('en');
  const [showPassword, setShowPassword] = useState(false);

  const [nameError, setNameError] = useState<string | null>(null);
  const [phoneError, setPhoneError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const [focusedInput, setFocusedInput] = useState<'name' | 'phone' | 'email' | 'password' | null>(null);

  function validate(): boolean {
    let isValid = true;
    setNameError(null);
    setPhoneError(null);
    setPasswordError(null);
    setFormError(null);

    if (!displayName.trim()) {
      setNameError('Full name is required');
      isValid = false;
    }

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

  async function handleRegister() {
    if (!validate()) return;

    const rawPhone = phone.replace(/\D/g, '');
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

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
      const msg = err instanceof Error ? err.message : 'Registration failed. Please try again.';
      setFormError(msg);
    }
  }

  return (
    <AuthScreen showBackHeader headerTitle="Create Account">
      <AuthHeader
        title="Join CivicConnect"
        subtitle="Create an account to report civic issues and track resolutions in real time"
        showLogoBadge={false}
      />

      <FormError message={formError} />

      <View style={styles.formGroup}>
        {/* Full Name */}
        <View style={styles.fieldContainer}>
          <Text style={styles.label}>Full Name</Text>
          <View
            style={[
              styles.inputWrapper,
              focusedInput === 'name' && styles.inputWrapperFocused,
              Boolean(nameError) && styles.inputWrapperError,
            ]}
          >
            <TextInput
              style={styles.textInput}
              placeholder="e.g. Rahul Sharma"
              placeholderTextColor="#94A3B8"
              autoCapitalize="words"
              value={displayName}
              onChangeText={(text) => {
                setDisplayName(text);
                if (nameError) setNameError(null);
              }}
              onFocus={() => setFocusedInput('name')}
              onBlur={() => setFocusedInput(null)}
              accessibilityLabel="Full name input"
            />
          </View>
          {nameError ? <Text style={styles.fieldErrorText}>{nameError}</Text> : null}
        </View>

        {/* Mobile Phone */}
        <View style={styles.fieldContainer}>
          <Text style={styles.label}>Mobile Phone Number</Text>
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

        {/* Email Address */}
        <View style={styles.fieldContainer}>
          <Text style={styles.label}>Email Address</Text>
          <View
            style={[
              styles.inputWrapper,
              focusedInput === 'email' && styles.inputWrapperFocused,
            ]}
          >
            <TextInput
              style={styles.textInput}
              placeholder="rahul@example.com"
              placeholderTextColor="#94A3B8"
              keyboardType="email-address"
              autoCapitalize="none"
              value={email}
              onChangeText={setEmail}
              onFocus={() => setFocusedInput('email')}
              onBlur={() => setFocusedInput(null)}
              accessibilityLabel="Email address input"
            />
          </View>
        </View>

        {/* Password */}
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
              placeholder="At least 8 characters"
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

        {/* Preferred Language Selector */}
        <View style={styles.fieldContainer}>
          <Text style={styles.label}>Preferred Language</Text>
          <View style={styles.langRow}>
            {LANGUAGES.map((item) => {
              const active = language === item.code;
              return (
                <TouchableOpacity
                  key={item.code}
                  onPress={() => {
                    setLanguage(item.code);
                    Haptics.selectionAsync();
                  }}
                  style={[styles.langChip, active && styles.langChipActive]}
                  activeOpacity={0.7}
                >
                  <Text style={[styles.langText, active && styles.langTextActive]}>
                    {item.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        {/* Primary Action Button */}
        <PrimaryButton
          title="Create account"
          onPress={handleRegister}
          isLoading={isLoading}
          accessibilityLabel="Create account button"
        />
      </View>

      <AuthFooter
        text="Already have an account?"
        linkText="Sign in"
        onPressLink={() => router.push('/login')}
      />
    </AuthScreen>
  );
}

const styles = StyleSheet.create({
  formGroup: {
    gap: 18,
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
  langRow: {
    flexDirection: 'row',
    gap: 8,
  },
  langChip: {
    flex: 1,
    height: 40,
    borderRadius: 8,
    backgroundColor: '#FAFAFA',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    alignItems: 'center',
    justifyContent: 'center',
  },
  langChipActive: {
    backgroundColor: '#ECFDF5',
    borderColor: '#059669',
  },
  langText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#475569',
  },
  langTextActive: {
    fontWeight: '600',
    color: '#059669',
  },
});
