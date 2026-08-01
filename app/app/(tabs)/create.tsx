import { useEffect } from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import { useRouter } from 'expo-router';

/**
 * Fallback route for Report tab item.
 * Directs to full-screen camera issue creation flow.
 */
export default function CreateTabScreen() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/camera');
  }, [router]);

  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color="#059669" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
    alignItems: 'center',
    justifyContent: 'center',
  },
});
