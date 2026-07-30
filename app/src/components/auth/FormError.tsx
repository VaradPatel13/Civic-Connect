import { StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface FormErrorProps {
  message?: string | null;
}

export function FormError({ message }: FormErrorProps) {
  if (!message) return null;

  return (
    <View style={styles.errorBanner}>
      <Ionicons name="alert-circle-outline" size={18} color="#DC2626" />
      <Text style={styles.errorBannerText}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FCA5A5',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginBottom: 20,
    gap: 8,
  },
  errorBannerText: {
    flex: 1,
    fontSize: 13,
    color: '#991B1B',
    fontWeight: '500',
  },
});
