import { useEffect } from 'react';
import { Platform } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { activateKeepAwakeAsync } from 'expo-keep-awake';
import { useAuthStore } from '@src/store/useAuthStore';

export default function RootLayout() {
  const initializeAuth = useAuthStore((state) => state.initializeAuth);

  useEffect(() => {
    initializeAuth();

    // Safely attempt to keep screen awake during dev, catching unhandled promise rejections on Android/Expo Go
    activateKeepAwakeAsync().catch(() => {
      // Ignored: Non-critical feature if device/emulator disallows keep-awake
    });

    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      const handleRejection = (event: PromiseRejectionEvent) => {
        if (event.reason && String(event.reason).toLowerCase().includes('keep awake')) {
          event.preventDefault();
        }
      };
      window.addEventListener('unhandledrejection', handleRejection);
      return () => window.removeEventListener('unhandledrejection', handleRejection);
    }
  }, [initializeAuth]);

  return (
    <SafeAreaProvider>
      <StatusBar style="auto" />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="login" />
        <Stack.Screen name="signup" />
        <Stack.Screen name="verify-otp" />
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="report-details" />
        <Stack.Screen name="create-report" options={{ presentation: 'modal' }} />
        <Stack.Screen name="camera" options={{ presentation: 'fullScreenModal' }} />
        <Stack.Screen name="submit-success" options={{ presentation: 'fullScreenModal' }} />
      </Stack>
    </SafeAreaProvider>
  );
}