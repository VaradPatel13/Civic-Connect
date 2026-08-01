import { useEffect, useRef, useState } from 'react';
import {
  Animated,
  Image,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { Report } from '@src/types';

const CATEGORY_ICON: Record<string, keyof typeof Ionicons.glyphMap> = {
  roads: 'alert-circle-outline',
  pothole: 'construct-outline',
  street_lighting: 'flash-outline',
  streetlight: 'flash-outline',
  drainage: 'water-outline',
  water_supply: 'water-outline',
  waste_management: 'trash-bin-outline',
  sanitation: 'trash-bin-outline',
  traffic: 'navigate-outline',
  noise: 'volume-high-outline',
  other: 'location-outline',
};

export function timeAgo(iso?: string): string {
  if (!iso) return 'Recently';
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export function getStatusDetails(statusRaw?: string) {
  const s = (statusRaw || 'pending').toLowerCase();

  if (s === 'resolved') {
    return {
      group: 'Resolved',
      label: 'RESOLVED',
      bg: '#ECFDF5',
      color: '#059669',
      border: '#A7F3D0',
    };
  }

  if (s === 'in_progress' || s === 'assigned') {
    return {
      group: 'In Progress',
      label: 'IN PROGRESS',
      bg: '#F0F9FF',
      color: '#0284C7',
      border: '#BAE6FD',
    };
  }

  if (s === 'processing' || s === 'review' || s === 'under_review' || s === 'pending' || s === 'open') {
    return {
      group: 'Open',
      label: 'UNDER REVIEW',
      bg: '#FEF3C7',
      color: '#D97706',
      border: '#FDE68A',
    };
  }

  if (s === 'verified') {
    return {
      group: 'Open',
      label: 'VERIFIED',
      bg: '#ECFDF5',
      color: '#059669',
      border: '#A7F3D0',
    };
  }

  if (s === 'rejected' || s === 'cancelled' || s === 'duplicate') {
    return {
      group: 'Closed',
      label: s.toUpperCase(),
      bg: '#FEF2F2',
      color: '#DC2626',
      border: '#FCA5A5',
    };
  }

  return {
    group: 'Open',
    label: 'OPEN',
    bg: '#FEF3C7',
    color: '#D97706',
    border: '#FDE68A',
  };
}

function useItemEntrance(index: number) {
  const opacity = useRef(new Animated.Value(1)).current;
  const translateY = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(opacity, {
      toValue: 1,
      duration: 150,
      useNativeDriver: true,
    }).start();
  }, [index, opacity]);

  return { opacity, translateY };
}

export interface ExecutiveReportCardProps {
  report: Report;
  index: number;
  onPress: () => void;
}

export function ExecutiveReportCard({
  report,
  index,
  onPress,
}: ExecutiveReportCardProps) {
  const { opacity, translateY } = useItemEntrance(index);
  const [imgError, setImgError] = useState(false);

  const rawCat = report.category || (report as any).issue_category || 'other';
  const catKey = String(rawCat).toLowerCase();
  const iconName = CATEGORY_ICON[catKey] ?? 'location-outline';

  const statusInfo = getStatusDetails(report.status);

  const photosList = (report as any).photos ?? report.images ?? [];
  const firstImg = photosList[0];
  const imageUrl = typeof firstImg === 'string'
    ? firstImg
    : firstImg?.cloudinary_url || firstImg?.secure_url || firstImg?.url || null;

  const displayAddress = report.location?.address ?? (report as any).address ?? 'Shivajinagar, Ward 12';
  const displayTime = report.createdAt ?? (report as any).created_at;

  return (
    <Animated.View style={{ opacity, transform: [{ translateY }] }}>
      <TouchableOpacity
        activeOpacity={0.85}
        style={styles.cardContainer}
        onPress={onPress}
      >
        {/* Card Media Area */}
        <View style={styles.cardMediaArea}>
          {Boolean(imageUrl) && !imgError ? (
            <Image
              source={{ uri: imageUrl }}
              style={styles.cardImage}
              onError={() => setImgError(true)}
              resizeMode="cover"
            />
          ) : (
            <View style={styles.cardPlaceholderIcon}>
              <Ionicons name={iconName} size={32} color="#059669" />
            </View>
          )}

          <View style={[styles.statusBadge, { backgroundColor: statusInfo.bg, borderColor: statusInfo.border }]}>
            <Text style={[styles.statusBadgeText, { color: statusInfo.color }]}>{statusInfo.label}</Text>
          </View>
        </View>

        {/* Content Details */}
        <View style={styles.cardContent}>
          <Text style={styles.reportTitle} numberOfLines={2}>
            {report.title}
          </Text>

          <View style={styles.metaRow}>
            <Ionicons name="location-outline" size={13} color="#059669" />
            <Text style={styles.locationText} numberOfLines={1}>
              {displayAddress}
            </Text>
            <Text style={styles.dotSep}>•</Text>
            <Text style={styles.timeText}>{timeAgo(displayTime)}</Text>
          </View>


          <View style={styles.divider} />

          <View style={styles.cardFooter}>
            <View style={styles.counterWrap}>
              <View style={styles.counterItem}>
                <Ionicons name="heart" size={13} color="#EF4444" />
                <Text style={styles.counterText}>{report.upvotes ?? 0}</Text>
              </View>
              <View style={styles.counterItem}>
                <Ionicons name="chatbubble-outline" size={13} color="#64748B" />
                <Text style={styles.counterText}>{report.commentCount ?? 0}</Text>
              </View>
            </View>

            <Text style={styles.viewDetailsText}>View Details →</Text>
          </View>
        </View>
      </TouchableOpacity>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  cardContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    overflow: 'hidden',
  },
  cardMediaArea: {
    height: 120,
    backgroundColor: '#ECFDF5',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  cardImage: {
    width: '100%',
    height: '100%',
  },
  cardPlaceholderIcon: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  statusBadge: {
    position: 'absolute',
    top: 10,
    right: 10,
    borderRadius: 6,
    borderWidth: 1,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  statusBadgeText: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  cardContent: {
    padding: 14,
    gap: 8,
  },
  reportTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
    lineHeight: 20,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  locationText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#475569',
    flex: 1,
  },
  dotSep: {
    fontSize: 10,
    color: '#CBD5E1',
  },
  timeText: {
    fontSize: 11,
    color: '#64748B',
    fontWeight: '500',
  },
  divider: {
    height: 1,
    backgroundColor: '#F1F5F9',
    marginVertical: 2,
  },
  cardFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  counterWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  counterItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  counterText: {
    fontSize: 12,
    color: '#334155',
    fontWeight: '600',
  },
  viewDetailsText: {
    fontSize: 12,
    color: '#059669',
    fontWeight: '700',
  },
});
