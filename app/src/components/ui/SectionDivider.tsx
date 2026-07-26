import { View, Text } from 'react-native';
import { tokens } from '@src/constants';

export interface SectionDividerProps {
  label: string;
}

export function SectionDivider({ label }: SectionDividerProps) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, marginBottom: 10, marginTop: 4 }}>
      <View style={{ width: 4, height: 12, borderRadius: 2, backgroundColor: tokens.primary.DEFAULT, marginRight: 8 }} />
      <Text style={{ color: tokens.text.primary, fontSize: 12, fontWeight: '900', textTransform: 'uppercase', letterSpacing: 0.8 }}>
        {label}
      </Text>
      <View style={{ flex: 1, height: 1, backgroundColor: tokens.surface.border, marginLeft: 10 }} />
    </View>
  );
}