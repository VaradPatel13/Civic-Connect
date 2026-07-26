import { View, Text, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { tokens } from '@src/constants';
import type { TrendingCategory } from '@src/types';

export interface TrendingStripProps {
  trending: TrendingCategory[];
}

export function TrendingStrip({ trending }: TrendingStripProps) {
  if (!trending?.length) return null;

  return (
    <View style={{ paddingLeft: 20, marginBottom: 16 }}>
      <Text style={{ color: tokens.text.disabled, fontSize: 10, fontWeight: '800', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
        TRENDING ISSUES
      </Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        {trending.map((item) => (
          <View key={item.label} style={{
            backgroundColor: tokens.surface.card,
            borderWidth: 1,
            borderColor: tokens.surface.border,
            borderRadius: 24,
            paddingVertical: 6,
            paddingHorizontal: 12,
            marginRight: 8,
            flexDirection: 'row',
            alignItems: 'center',
            gap: 6,
          }}>
            <Ionicons name={item.icon as any} size={13} color={tokens.primary.DEFAULT} />
            <Text style={{ fontSize: 12, color: tokens.text.primary, fontWeight: '700' }}>#{item.label}</Text>
            <View style={{
              backgroundColor: `${tokens.primary.DEFAULT}12`,
              borderRadius: 10,
              paddingHorizontal: 6,
              paddingVertical: 1,
            }}>
              <Text style={{ fontSize: 10, color: tokens.primary.DEFAULT, fontWeight: '800' }}>{item.count}</Text>
            </View>
          </View>
        ))}
      </ScrollView>
    </View>
  );
}