import { View, Text, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { tokens } from '@src/constants';

export interface ErrorStateProps {
  message: string;
  onRetry: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 40 }}>
      <Ionicons name="cloud-offline-outline" size={48} color={tokens.error.DEFAULT} />
      <Text style={{ color: tokens.text.primary, fontWeight: '700', fontSize: 18, marginTop: 16, textAlign: 'center' }}>
        Couldn't load dashboard
      </Text>
      <Text style={{ color: tokens.text.secondary, fontSize: 13, marginTop: 6, textAlign: 'center', lineHeight: 20 }}>
        {message}
      </Text>
      <TouchableOpacity onPress={onRetry} style={{
        backgroundColor: tokens.primary.DEFAULT,
        borderRadius: 24,
        paddingVertical:   12,
        paddingHorizontal: 28,
        marginTop: 22,
      }}>
        <Text style={{ color: '#fff', fontWeight: '700', fontSize: 14 }}>Try again</Text>
      </TouchableOpacity>
    </View>
  );
}