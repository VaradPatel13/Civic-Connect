import { useState } from 'react';
import { View, Text, TouchableOpacity, Image, StyleSheet } from 'react-native';
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
    statusStr === 'resolved' ? '#059669'
    : statusStr === 'in_progress' || statusStr === 'assigned' || statusStr === 'processing' ? '#0284C7'
    : '#D97706';

  const statusBg =
    statusStr === 'resolved' ? '#ECFDF5'
    : statusStr === 'in_progress' || statusStr === 'assigned' || statusStr === 'processing' ? '#F0F9FF'
    : '#FEF3C7';

  const firstImg = report.images?.[0];
  const imageUrl = typeof firstImg === 'string' ? firstImg : firstImg?.url;

  return (
    <TouchableOpacity activeOpacity={0.85} onPress={onPress} style={styles.container}>
      <View style={styles.card}>
        {/* Featured Tag & Image Header */}
        <View style={styles.imageHeader}>
          {Boolean(imageUrl) && !imgError ? (
            <Image
              source={{ uri: imageUrl }}
              style={styles.image}
              onError={() => setImgError(true)}
              resizeMode="cover"
            />
          ) : (
            <View style={styles.imagePlaceholder}>
              <Ionicons name={catIcon as any} size={38} color="#059669" />
            </View>
          )}

          {/* Badges Bar */}
          <View style={styles.badgeBar}>
            <View style={[styles.statusBadge, { backgroundColor: statusBg, borderColor: statusColor }]}>
              <Text style={[styles.statusText, { color: statusColor }]}>
                {statusStr.replace('_', ' ')}
              </Text>
            </View>

            <View style={styles.featuredBadge}>
              <Text style={styles.featuredBadgeText}>FEATURED</Text>
            </View>
          </View>
        </View>

        {/* Card Body */}
        <View style={styles.cardBody}>
          <Text style={styles.title} numberOfLines={2}>
            {report.title}
          </Text>

          <View style={styles.locationRow}>
            <Ionicons name="location-outline" size={14} color="#059669" />
            <Text style={styles.locationText} numberOfLines={1}>
              {report.location?.address ?? 'Pune'}
            </Text>
          </View>

          {/* Bottom Card Footer */}
          <View style={styles.footerRow}>
            <View style={styles.metricsRow}>
              <View style={styles.metricItem}>
                <Ionicons name="heart" size={13} color="#EF4444" />
                <Text style={styles.metricText}>{report.upvotes ?? 0}</Text>
              </View>
              <View style={styles.metricItem}>
                <Ionicons name="chatbubble-outline" size={13} color="#64748B" />
                <Text style={styles.metricText}>{report.commentCount ?? 0}</Text>
              </View>
            </View>

            <Text style={styles.actionText}>View Details →</Text>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 8,
  },
  card: {
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  imageHeader: {
    height: 150,
    backgroundColor: '#ECFDF5',
    position: 'relative',
    overflow: 'hidden',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  imagePlaceholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  badgeBar: {
    position: 'absolute',
    top: 10,
    left: 10,
    right: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  statusBadge: {
    borderWidth: 1,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  statusText: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.3,
    textTransform: 'uppercase',
  },
  featuredBadge: {
    backgroundColor: 'rgba(15, 23, 42, 0.85)',
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  featuredBadgeText: {
    fontSize: 9,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 0.5,
  },
  cardBody: {
    padding: 14,
  },
  title: {
    color: '#0F172A',
    fontSize: 15,
    fontWeight: '700',
    lineHeight: 20,
    marginBottom: 6,
  },
  locationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 10,
  },
  locationText: {
    color: '#475569',
    fontSize: 12,
    fontWeight: '500',
    flex: 1,
  },
  footerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
  },
  metricsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  metricItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metricText: {
    fontSize: 12,
    color: '#334155',
    fontWeight: '600',
  },
  actionText: {
    fontSize: 12,
    color: '#059669',
    fontWeight: '700',
  },
});