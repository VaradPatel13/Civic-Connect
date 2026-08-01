/**
 * Submit Success Screen — CivicConnect Mobile
 * Clean, receipt-style confirmation shown after a successful report submission.
 */
import { useEffect, useRef } from 'react';
import { Animated, Image, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';

import { ISSUE_CATEGORY_MAP } from '@src/types/reports';

export default function SubmitSuccessScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const params = useLocalSearchParams<Record<string, string>>();

  const checkScale = useRef(new Animated.Value(0)).current;
  const cardOpacity = useRef(new Animated.Value(0)).current;
  const cardTranslateY = useRef(new Animated.Value(20)).current;

  useEffect(() => {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});

    Animated.sequence([
      Animated.spring(checkScale, {
        toValue: 1,
        friction: 6,
        tension: 120,
        useNativeDriver: true,
      }),
    ]).start();

    Animated.sequence([
      Animated.delay(300),
      Animated.parallel([
        Animated.spring(cardOpacity, { toValue: 1, friction: 8, tension: 60, useNativeDriver: true }),
        Animated.spring(cardTranslateY, { toValue: 0, friction: 10, tension: 80, useNativeDriver: true }),
      ]),
    ]).start();
  }, [cardOpacity, cardTranslateY, checkScale]);

  const cat = ISSUE_CATEGORY_MAP[params.category as keyof typeof ISSUE_CATEGORY_MAP];
  const icon = (cat?.icon ?? 'location-outline') as keyof typeof Ionicons.glyphMap;
  const label = cat?.label ?? params.category ?? 'Report';
  const photoUri = params.photoUri;
  const address = params.address ?? 'Pune';
  const title = params.title ?? 'Your Report';

  const txId = params.id
    ? `#${params.id.split('-')[0].toUpperCase()}`
    : `#${Date.now().toString(36).toUpperCase()}`;

  return (
    <View style={styles.screen}>
      {/* Hero Header */}
      <View style={[styles.hero, { paddingTop: Math.max(insets.top + 16, 50) }]}>
        <Animated.View style={[styles.checkCircle, { transform: [{ scale: checkScale }] }]}>
          <Ionicons name="checkmark" size={38} color="#FFFFFF" />
        </Animated.View>
        <Text style={styles.heroTitle}>Report Submitted!</Text>
        <Text style={styles.heroSubtitle}>Your civic issue has been logged successfully.</Text>
      </View>

      {/* Receipt Card */}
      <Animated.View
        style={[
          styles.card,
          {
            opacity: cardOpacity,
            transform: [{ translateY: cardTranslateY }],
          },
        ]}
      >
        {/* Confirmation ID */}
        <View style={styles.txRow}>
          <Text style={styles.txLabel}>Confirmation No.</Text>
          <Text style={styles.txId}>{txId}</Text>
        </View>

        <View style={styles.divider} />

        {/* Category */}
        <View style={styles.row}>
          <View style={styles.rowLeft}>
            <View style={styles.iconBox}>
              <Ionicons name={icon} size={14} color="#059669" />
            </View>
            <Text style={styles.rowLabelText}>Category</Text>
          </View>
          <Text style={styles.rowRight}>{label}</Text>
        </View>

        {/* Location */}
        <View style={styles.row}>
          <View style={styles.rowLeft}>
            <Ionicons name="location-outline" size={15} color="#64748B" />
            <Text style={styles.rowLabelText}>Location</Text>
          </View>
          <Text style={styles.rowRight} numberOfLines={2}>
            {address}
          </Text>
        </View>

        {/* Issue Title */}
        <View style={styles.row}>
          <View style={styles.rowLeft}>
            <Ionicons name="document-text-outline" size={15} color="#64748B" />
            <Text style={styles.rowLabelText}>Issue</Text>
          </View>
          <Text style={styles.rowRight} numberOfLines={2}>
            {title}
          </Text>
        </View>

        <View style={styles.divider} />

        {/* Timeline */}
        <View style={styles.timeline}>
          {[
            { icon: 'checkmark-circle', label: 'Submitted', active: true },
            { icon: 'time-outline', label: 'Review', active: false },
            { icon: 'construct-outline', label: 'In Progress', active: false },
            { icon: 'checkmark-circle-outline', label: 'Resolved', active: false },
          ].map((step) => (
            <View key={step.label} style={styles.timelineStep}>
              <View style={[styles.timelineDot, step.active && styles.timelineDotActive]}>
                <Ionicons
                  name={step.icon as any}
                  size={12}
                  color={step.active ? '#FFFFFF' : '#94A3B8'}
                />
              </View>
              <Text style={[styles.timelineLabel, step.active && styles.timelineLabelActive]}>
                {step.label}
              </Text>
            </View>
          ))}
        </View>

        <View style={styles.divider} />

        {/* Primary CTA */}
        <TouchableOpacity
          style={styles.primaryBtn}
          activeOpacity={0.8}
          onPress={() => router.push('/(tabs)/reports')}
        >
          <Text style={styles.primaryBtnText}>View My Reports</Text>
        </TouchableOpacity>

        {/* Secondary CTA */}
        <TouchableOpacity
          style={styles.secondaryBtn}
          activeOpacity={0.8}
          onPress={() => router.push('/(tabs)')}
        >
          <Text style={styles.secondaryBtnText}>Back to Home</Text>
        </TouchableOpacity>
      </Animated.View>

      {/* Photo Badge */}
      {photoUri ? (
        <View style={styles.photoBadge}>
          <Image source={{ uri: photoUri }} style={styles.photoThumb} />
          <Text style={styles.photoBadgeText}>Photo attached</Text>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  hero: {
    backgroundColor: '#059669',
    paddingBottom: 40,
    alignItems: 'center',
  },
  checkCircle: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  heroTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: -0.4,
  },
  heroSubtitle: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.85)',
    marginTop: 4,
  },

  card: {
    marginHorizontal: 20,
    marginTop: -16,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    padding: 16,
    gap: 10,
  },

  txRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  txLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: '#64748B',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  txId: {
    fontSize: 14,
    fontWeight: '700',
    color: '#059669',
    letterSpacing: 0.5,
  },
  divider: {
    height: 1,
    backgroundColor: '#F1F5F9',
    marginVertical: 4,
  },

  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  rowLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  iconBox: {
    width: 22,
    height: 22,
    borderRadius: 5,
    backgroundColor: '#ECFDF5',
    alignItems: 'center',
    justifyContent: 'center',
  },
  rowLabelText: {
    fontSize: 12,
    color: '#64748B',
    fontWeight: '500',
  },
  rowRight: {
    fontSize: 13,
    color: '#0F172A',
    fontWeight: '600',
    maxWidth: '55%',
    textAlign: 'right',
  },

  timeline: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
  timelineStep: {
    flex: 1,
    alignItems: 'center',
    gap: 4,
  },
  timelineDot: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#F1F5F9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  timelineDotActive: {
    backgroundColor: '#059669',
  },
  timelineLabel: {
    fontSize: 9,
    color: '#64748B',
    fontWeight: '500',
    textAlign: 'center',
  },
  timelineLabelActive: {
    color: '#059669',
    fontWeight: '700',
  },

  primaryBtn: {
    backgroundColor: '#059669',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
  },
  primaryBtnText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },
  secondaryBtn: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  secondaryBtnText: {
    color: '#0F172A',
    fontWeight: '600',
    fontSize: 14,
  },

  photoBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginHorizontal: 20,
    marginTop: 14,
  },
  photoThumb: {
    width: 32,
    height: 32,
    borderRadius: 6,
  },
  photoBadgeText: {
    fontSize: 12,
    color: '#64748B',
    fontWeight: '500',
  },
});