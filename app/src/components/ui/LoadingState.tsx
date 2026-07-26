import { View, Text, ActivityIndicator } from 'react-native';
import { tokens } from '@src/constants';

export function LoadingState() {
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', paddingTop: 60 }}>
      <ActivityIndicator size="large" color={tokens.primary.DEFAULT} />
      <Text style={{ color: tokens.text.secondary, fontSize: 13, marginTop: 14 }}>Loading…</Text>
    </View>
  );
}