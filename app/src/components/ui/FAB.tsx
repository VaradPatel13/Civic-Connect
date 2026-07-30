import { StyleSheet, Text, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

export interface FABProps {
  onPress: () => void;
  bottomOffset?: number;
}

export function FAB({ onPress, bottomOffset }: FABProps) {
  const insets = useSafeAreaInsets();
  const bottomPosition = bottomOffset ?? Math.max(insets.bottom + 64, 80);

  return (
    <TouchableOpacity
      activeOpacity={0.85}
      onPress={onPress}
      style={[styles.fab, { bottom: bottomPosition }]}
      accessibilityRole="button"
      accessibilityLabel="Report a civic issue"
    >
      <Ionicons name="camera-outline" size={18} color="#FFFFFF" />
      <Text style={styles.text}>Report Issue</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  fab: {
    position: 'absolute',
    right: 20,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#059669',
    paddingVertical: 12,
    paddingHorizontal: 18,
    borderRadius: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 6,
    elevation: 5,
  },
  text: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
});