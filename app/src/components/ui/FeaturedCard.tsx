import { useState } from 'react';
import { View, Text, TouchableOpacity, Image } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { tokens } from '@src/constants';
import { CATEGORY_ICON } from '@src/constants/categoryIcons';
import type { Report } from '@src/types';

export interface FeaturedCardProps {
  report: Report;
  onPress: () => void;
}

export function FeaturedCard({ report, onPress }: FeaturedCardProps) {
  const [imgError, setImgError] = useState(false);
  const catIcon = CATEGORY_ICON[report.category] ?? 'location';
  const statusStr = (report.status ?? 'open').toLowerCase();

  const statusColor =
    statusStr === 'resolved' ? tokens.success.DEFAULT
    : statusStr === 'in_progress' || statusStr === 'assigned' || statusStr === 'processing' ? tokens.info.DEFAULT
    : tokens.accent.DEFAULT;

  const statusBg =
    statusStr === 'resolved' ? tokens.success.light
    : statusStr === 'in_progress' || statusStr === 'assigned' || statusStr === 'processing' ? tokens.info.light
    : tokens.accent.light;

  const firstImg = report.images?.[0];
  const imageUrl = typeof firstImg === 'string' ? firstImg : firstImg?.url;

  return (
    <TouchableOpacity activeOpacity={0.85} onPress={onPress} style={{ paddingHorizontal: 20, marginBottom: 12 }}>
      <View style={{
        borderRadius: 18,
        overflow: 'hidden',
        backgroundColor: tokens.surface.card,
        borderWidth: 1,
        borderColor: tokens.surface.border,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.05,
        shadowRadius: 10,
        elevation: 2,
      }}>
        {/* Featured Tag & Image Header */}
        <View style={{ height: 160, backgroundColor: `${tokens.primary.DEFAULT}10`, position: 'relative', overflow: 'hidden' }}>
          {Boolean(imageUrl) && !imgError ? (
            <Image
              source={{ uri: imageUrl }}
              style={{ width: '100%', height: '100%' }}
              onError={() => setImgError(true)}
              resizeMode="cover"
            />
          ) : (
            <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
              <Ionicons name={catIcon as any} size={42} color={tokens.primary.light} />
            </View>
          )}

          {/* Badges Bar */}
          <View style={{ position: 'absolute', top: 12, left: 12, right: 12, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
            <View style={{ backgroundColor: statusBg, borderWidth: 1, borderColor: statusColor, borderRadius: 8, paddingHorizontal: 9, paddingVertical: 4 }}>
              <Text style={{ fontSize: 10, fontWeight: '900', color: statusColor, letterSpacing: 0.5, textTransform: 'uppercase' }}>
                {statusStr.replace('_', ' ')}
              </Text>
            </View>

            <View style={{ backgroundColor: 'rgba(15, 23, 42, 0.85)', borderRadius: 8, paddingHorizontal: 9, paddingVertical: 4 }}>
              <Text style={{ fontSize: 10, fontWeight: '800', color: '#fff', textTransform: 'capitalize' }}>
                FEATURED
              </Text>
            </View>
          </View>
        </View>

        {/* Card Body */}
        <View style={{ padding: 16 }}>
          <Text style={{
            color: tokens.text.primary,
            fontSize: 16,
            fontWeight: '800',
            lineHeight: 22,
            marginBottom: 6,
          }} numberOfLines={2}>
            {report.title}
          </Text>

          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 12 }}>
            <Ionicons name="location-outline" size={13} color={tokens.primary.DEFAULT} />
            <Text style={{ color: tokens.text.secondary, fontSize: 12, fontWeight: '600', flex: 1 }} numberOfLines={1}>
              {report.location?.address ?? 'Pune'}
            </Text>
          </View>

          {/* Bottom Card Footer */}
          <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingTop: 12, borderTopWidth: 1, borderTopColor: tokens.surface.border }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 14 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                <Ionicons name="heart" size={14} color="#ef4444" />
                <Text style={{ fontSize: 12, color: tokens.text.primary, fontWeight: '700' }}>{report.upvotes ?? 0}</Text>
              </View>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                <Ionicons name="chatbubble-outline" size={14} color={tokens.text.secondary} />
                <Text style={{ fontSize: 12, color: tokens.text.secondary, fontWeight: '600' }}>{report.commentCount ?? 0}</Text>
              </View>
            </View>

            <Text style={{ fontSize: 11, color: tokens.primary.DEFAULT, fontWeight: '800' }}>
              View Details →
            </Text>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
}