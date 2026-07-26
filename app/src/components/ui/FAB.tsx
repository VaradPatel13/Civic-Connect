import { TouchableOpacity, Text } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { tokens } from '@src/constants';

export interface FABProps {
  onPress: () => void;
}

export function FAB({ onPress }: FABProps) {
  return (
    <TouchableOpacity
      activeOpacity={0.85}
      onPress={onPress}
      style={{
        position: 'absolute',
        right: 20,
        bottom: 28,
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        backgroundColor: tokens.primary.DEFAULT,
        paddingVertical: 14,
        paddingHorizontal: 22,
        borderRadius: 30,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.2,
        shadowRadius: 8,
        elevation: 6,
      }}
    >
      <Ionicons name="camera-outline" size={20} color="#fff" />
      <Text style={{ color: '#fff', fontSize: 14, fontWeight: '900', letterSpacing: 0.3 }}>
        Report Issue
      </Text>
    </TouchableOpacity>
  );
}