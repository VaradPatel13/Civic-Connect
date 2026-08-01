import { useState } from 'react';
import { View, Text, TouchableOpacity, Image, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
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
    statusStr === 'resolved' ? '#059669'
    : statusStr === 'in_progress' || statusStr === 'assigned' || statusStr === 'processing' ? '#0284C7'
    : '#D97706';

  const photosList = (report as any).photos ?? report.images ?? [];
  const firstImg = photosList[0];
  const imageUrl = typeof firstImg === 'string'
    ? firstImg
    : firstImg?.cloudinary_url || firstImg?.secure_url || firstImg?.url || null;

  return (
    <TouchableOpacity activeOpacity={0.82} onPress={onPress} style={styles.container}>
      <View style={styles.card}>
        {/* Thumbnail Box */}
        <View style={styles.thumbnailBox}>
          {Boolean(imageUrl) && !imgError ? (
            <Image
              source={{ uri: imageUrl }}
              style={styles.thumbnailImage}
              onError={() => setImgError(true)}
              resizeMode="cover"
            />
          ) : (
            <View style={styles.thumbnailPlaceholder}>
              <Ionicons name={catIcon as any} size={22} color="#059669" />
            </View>
          )}
        </View>

        {/* Content Section */}
        <View style={styles.contentSection}>
          <View style={styles.headerRow}>
            <View style={[styles.statusDot, { backgroundColor: statusColor }]} />
            <Text style={[styles.statusText, { color: statusColor }]}>
              {statusStr.replace('_', ' ')}
            </Text>
            <Text style={styles.dotSeparator}>·</Text>
            <Text style={styles.categoryText} numberOfLines={1}>
              {report.category}
            </Text>
          </View>

          <Text style={styles.title} numberOfLines={1}>
            {report.title}
          </Text>

          <View style={styles.metaRow}>
            <Text style={styles.locationText} numberOfLines={1}>
              📍 {report.location?.address ?? 'Pune'}
            </Text>
            <View style={styles.upvoteRow}>
              <Ionicons name="heart" size={11} color="#EF4444" />
              <Text style={styles.upvoteText}>{report.upvotes ?? 0}</Text>
            </View>
          </View>
        </View>

        <Ionicons name="chevron-forward" size={16} color="#94A3B8" />
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 4,
  },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 10,
    padding: 10,
  },
  thumbnailBox: {
    width: 60,
    height: 60,
    borderRadius: 8,
    overflow: 'hidden',
    backgroundColor: '#ECFDF5',
    flexShrink: 0,
  },
  thumbnailImage: {
    width: '100%',
    height: '100%',
  },
  thumbnailPlaceholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  contentSection: {
    flex: 1,
    justifyContent: 'center',
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 3,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  statusText: {
    fontSize: 10,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.3,
  },
  dotSeparator: {
    fontSize: 10,
    color: '#CBD5E1',
  },
  categoryText: {
    fontSize: 10,
    color: '#64748B',
    fontWeight: '500',
    textTransform: 'capitalize',
    flexShrink: 1,
  },
  title: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
    lineHeight: 18,
    marginBottom: 4,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
  },
  locationText: {
    fontSize: 11,
    color: '#64748B',
    flex: 1,
  },
  upvoteRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
  },
  upvoteText: {
    fontSize: 11,
    color: '#0F172A',
    fontWeight: '700',
  },
});