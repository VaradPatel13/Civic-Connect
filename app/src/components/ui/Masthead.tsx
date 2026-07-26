import { View, Text } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { tokens } from '@src/constants';
import type { DashboardStats } from '@src/types';

export interface MastheadProps {
  stats: DashboardStats | null;
}

export function Masthead({ stats }: MastheadProps) {
  return (
    <View style={{ paddingHorizontal: 20, paddingTop: 48, paddingBottom: 16 }}>
      {/* Top Header Pill Ticker */}
      <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
        <View style={{
          flexDirection: 'row',
          alignItems: 'center',
          gap: 6,
          backgroundColor: `${tokens.primary.DEFAULT}0d`,
          borderWidth: 1,
          borderColor: `${tokens.primary.DEFAULT}20`,
          paddingVertical: 5,
          paddingHorizontal: 10,
          borderRadius: 20,
        }}>
          <View style={{ width: 6, height: 6, borderRadius: 3, backgroundColor: tokens.success.DEFAULT }} />
          <Text style={{ color: tokens.primary.DEFAULT, fontSize: 11, fontWeight: '800', letterSpacing: 0.8, textTransform: 'uppercase' }}>
            PUNE MUNICIPALITY
          </Text>
        </View>

        <Text style={{ color: tokens.text.disabled, fontSize: 11, fontWeight: '600' }}>
          {stats ? `${stats.totalReports} Total Reports` : 'Syncing...'}
        </Text>
      </View>

      {/* Gen Z Hero Typography */}
      <View style={{ marginBottom: 20 }}>
        <Text style={{ color: tokens.text.primary, fontSize: 32, fontWeight: '900', lineHeight: 36, letterSpacing: -1 }}>
          Civic Pulse.
        </Text>
        <Text style={{
          color: tokens.primary.DEFAULT,
          fontSize: 32,
          fontWeight: '900',
          lineHeight: 36,
          letterSpacing: -1,
          marginTop: -2,
        }}>
          Real Impact.
        </Text>
      </View>

      {/* Bento Metric Cards */}
      {stats ? (
        <View style={{ flexDirection: 'row', gap: 10 }}>
          {/* Card 1: Open Issues */}
          <View style={{
            flex: 1,
            backgroundColor: tokens.surface.card,
            borderWidth: 1,
            borderColor: tokens.surface.border,
            borderRadius: 16,
            padding: 14,
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 1 },
            shadowOpacity: 0.04,
            shadowRadius: 4,
            elevation: 1,
          }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <Text style={{ color: tokens.text.disabled, fontSize: 10, fontWeight: '800', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                ACTIVE
              </Text>
              <Ionicons name="time-outline" size={14} color={tokens.accent.DEFAULT} />
            </View>
            <Text style={{ color: tokens.text.primary, fontSize: 30, fontWeight: '900', lineHeight: 32, letterSpacing: -1 }}>
              {stats.openReports}
            </Text>
            <Text style={{ color: tokens.text.secondary, fontSize: 11, fontWeight: '600', marginTop: 2 }}>
              Open Issues
            </Text>
          </View>

          {/* Card 2: Resolved */}
          <View style={{
            flex: 1,
            backgroundColor: tokens.surface.card,
            borderWidth: 1,
            borderColor: tokens.surface.border,
            borderRadius: 16,
            padding: 14,
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 1 },
            shadowOpacity: 0.04,
            shadowRadius: 4,
            elevation: 1,
          }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <Text style={{ color: tokens.text.disabled, fontSize: 10, fontWeight: '800', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                THIS MONTH
              </Text>
              <Ionicons name="checkmark-done-circle-outline" size={16} color={tokens.success.DEFAULT} />
            </View>
            <Text style={{ color: tokens.primary.DEFAULT, fontSize: 30, fontWeight: '900', lineHeight: 32, letterSpacing: -1 }}>
              {stats.resolvedThisMonth}
            </Text>
            <Text style={{ color: tokens.text.secondary, fontSize: 11, fontWeight: '600', marginTop: 2 }}>
              Resolved
            </Text>
          </View>
        </View>
      ) : (
        <View style={{ flexDirection: 'row', gap: 10 }}>
          {[1, 2].map((k) => (
            <View key={k} style={{
              flex: 1,
              height: 90,
              backgroundColor: tokens.surface.border,
              borderRadius: 16,
              opacity: 0.5,
            }} />
          ))}
        </View>
      )}
    </View>
  );
}