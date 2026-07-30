import { Redirect } from 'expo-router';
import { useAuthStore } from '@src/store/useAuthStore';

export default function Index() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  if (!isAuthenticated) {
    return <Redirect href="/login" />;
  }
  return <Redirect href="/(tabs)" />;
}
