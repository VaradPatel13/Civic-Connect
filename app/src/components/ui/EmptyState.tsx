import { View, Text, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { tokens } from '@src/constants';

export interface EmptyStateProps {
  onReport: () => void;
}

export function EmptyState({ onReport }: EmptyStateProps) {
  return (
    <View style={{
      marginHorizontal: 20,
      backgroundColor: tokens.surface.card,
      borderWidth: 1,
      borderColor: tokens.surface.border,
      borderRadius: 20,
      alignItems: 'center',
      paddingHorizontal: 24,
      paddingVertical: 36,
      marginTop: 10,
    }}>
      <View style={{
        width: 56,
        height: 56,
        borderRadius: 28,
        backgroundColor: `${tokens.primary.DEFAULT}12`,
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: 14,
      }}>
        <Ionicons name="sparkles-outline" size={26} color={tokens.primary.DEFAULT} />
      </View>
      <Text style={{ color: tokens.text.primary, fontWeight: '900', fontSize: 18, textAlign: 'center' }}>
        No Active Reports
      </Text>
      <Text style={{ color: tokens.text.secondary, fontSize: 13, marginTop: 6, textAlign: 'center', lineHeight: 20 }}>
        The municipal feed is clean. Spotted a civic issue in Pune? Be the first to report it.
      </Text>
      <TouchableOpacity
        activeOpacity={0.85}
        onPress={onReport}
        style={{
          flexDirection: 'row',
          alignItems: 'center',
          gap: 6,
          backgroundColor: tokens.primary.DEFAULT,
          borderRadius: 24,
          paddingVertical: 12,
          paddingHorizontal: 24,
          marginTop: 20,
        }}
      >
        <Ionicons name="camera" size={16} color="#fff" />
        <Text style={{ color: '#fff', fontWeight: '800', fontSize: 14 }}>File a Report</Text>
      </TouchableOpacity>
    </View>
  );
}