import { useState } from 'react';
import { View, Text, TouchableOpacity, Image } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { tokens } from '@src/constants';
import { CATEGORY_ICON } from '@src/constants/categoryIcons';
import type { Report } from '@src/types';

export interface ReportRowProps {
  report: Report;
  onPress: () => void;
}

export function ReportRow({ report, onPress }: ReportRowProps) {
  const [imgError, setImgError] = useState(false);
  const catIcon = CATEGORY_ICON[report.category] ?? 'location';
  const statusStr = (report.status ?? 'open').toLowerCase();

  const statusColor =
    statusStr === 'resolved' ? tokens.success.DEFAULT
    : statusStr === 'in_progress' || statusStr === 'assigned' || statusStr === 'processing' ? tokens.info.DEFAULT
    : tokens.accent.DEFAULT;

  const firstImg = report.images?.[0];
  const imageUrl = typeof firstImg === 'string' ? firstImg : firstImg?.url;

  return (
    <TouchableOpacity activeOpacity={0.82} onPress={onPress} style={{ paddingHorizontal: 20, marginBottom: 8 }}>
      <View style={{
        flexDirection: 'row',
        alignItems: 'center',
        gap: 12,
        backgroundColor: tokens.surface.card,
        borderWidth: 1,
        borderColor: tokens.surface.border,
        borderRadius: 14,
        padding: 12,
      }}>
        {/* Thumbnail Box */}
        <View style={{
          width: 68,
          height: 68,
          borderRadius: 10,
          overflow: 'hidden',
          backgroundColor: `${tokens.primary.DEFAULT}0d`,
          flexShrink: 0,
        }}>
          {Boolean(imageUrl) && !imgError ? (
            <Image
              source={{ uri: imageUrl }}
              style={{ width: '100%', height: '100%' }}
              onError={() => setImgError(true)}
              resizeMode="cover"
            />
          ) : (
            <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
              <Ionicons name={catIcon as any} size={24} color={tokens.primary.light} />
            </View>
          )}
        </View>

        {/* Content Section */}
        <View style={{ flex: 1, justifyContent: 'center' }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 4 }}>
            <View style={{ width: 6, height: 6, borderRadius: 3, backgroundColor: statusColor }} />
            <Text style={{ fontSize: 10, fontWeight: '800', color: statusColor, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              {statusStr.replace('_', ' ')}
            </Text>
            <Text style={{ fontSize: 10, color: tokens.text.disabled }}>·</Text>
            <Text style={{ fontSize: 10, color: tokens.text.secondary, textTransform: 'capitalize' }}>
              {report.category}
            </Text>
          </View>

          <Text style={{
            fontSize: 14,
            fontWeight: '700',
            color: tokens.text.primary,
            lineHeight: 18,
            marginBottom: 4,
          }} numberOfLines={1}>
            {report.title}
          </Text>

          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
            <Text style={{ fontSize: 11, color: tokens.text.secondary }} numberOfLines={1}>
              📍 {report.location?.address ?? 'Pune'}
            </Text>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 3 }}>
              <Ionicons name="heart" size={11} color="#ef4444" />
              <Text style={{ fontSize: 11, color: tokens.text.primary, fontWeight: '700' }}>{report.upvotes ?? 0}</Text>
            </View>
          </View>
        </View>

        <Ionicons name="chevron-forward" size={18} color={tokens.text.disabled} />
      </View>
    </TouchableOpacity>
  );
}