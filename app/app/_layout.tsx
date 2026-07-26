import { useEffect } from 'react';
import { Platform } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

export default function RootLayout() {
  useEffect(() => {
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      const handleRejection = (event: PromiseRejectionEvent) => {
        if (event.reason && String(event.reason).toLowerCase().includes('keep awake')) {
          event.preventDefault();
        }
      };
      window.addEventListener('unhandledrejection', handleRejection);
      return () => window.removeEventListener('unhandledrejection', handleRejection);
    }
  }, []);

  return (
    <SafeAreaProvider>
      <StatusBar style="auto" />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="report-details" />
        <Stack.Screen name="create-report" options={{ presentation: 'modal' }} />
        <Stack.Screen name="camera" options={{ presentation: 'fullScreenModal' }} />
        <Stack.Screen name="submit-success" options={{ presentation: 'fullScreenModal' }} />
      </Stack>
    </SafeAreaProvider>
  );
}