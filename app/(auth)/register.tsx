import React, { useState } from 'react';
import { StyleSheet, Text, TextInput, Alert, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { authService } from '../services';
import { useAuthStore } from '../stores/authStore';

export default function RegisterScreen() {
  const router = useRouter();
  const setAuth = useAuthStore((state: any) => state.setAuth);

  const [displayName, setDisplayName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    if (!displayName || !phone || !password) {
      Alert.alert('Missing Fields', 'Please complete all required fields.');
      return;
    }
    setLoading(true);
    try {
      const data = await authService.register({
        display_name: displayName,
        phone,
        email: email || undefined,
        password,
      });
      setAuth(data.user, data.access_token, data.refresh_token);
      router.replace('/(tabs)');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Registration failed. Please check inputs.';
      Alert.alert('Registration Error', msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Card style={styles.card}>
        <Text style={styles.cardTitle}>Create Citizen Account</Text>

        <Text style={styles.label}>Full Name *</Text>
        <TextInput
          style={styles.input}
          placeholder="Jane Doe"
          placeholderTextColor="#64748b"
          value={displayName}
          onChangeText={setDisplayName}
        />

        <Text style={styles.label}>Phone Number (10 digits) *</Text>
        <TextInput
          style={styles.input}
          placeholder="9876543210"
          placeholderTextColor="#64748b"
          keyboardType="phone-pad"
          maxLength={10}
          value={phone}
          onChangeText={setPhone}
        />

        <Text style={styles.label}>Email Address (Optional)</Text>
        <TextInput
          style={styles.input}
          placeholder="jane@example.com"
          placeholderTextColor="#64748b"
          keyboardType="email-address"
          value={email}
          onChangeText={setEmail}
        />

        <Text style={styles.label}>Password (Min 8 characters) *</Text>
        <TextInput
          style={styles.input}
          placeholder="Create Secure Password"
          placeholderTextColor="#64748b"
          secureTextEntry
          value={password}
          onChangeText={setPassword}
        />

        <Button title="Register & Continue" onPress={handleRegister} loading={loading} />
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: '#0f172a',
    padding: 20,
    justifyContent: 'center',
  },
  card: {
    padding: 24,
  },
  cardTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#f8fafc',
    marginBottom: 20,
  },
  label: {
    color: '#cbd5e1',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 6,
  },
  input: {
    backgroundColor: '#0f172a',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 10,
    padding: 12,
    color: '#f8fafc',
    fontSize: 16,
    marginBottom: 16,
  },
});
