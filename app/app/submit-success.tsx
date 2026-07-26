/**
 * Submit Success Screen — CivicConnect
 *
 * PhonePe / payment-receipt style confirmation shown after a
 * successful report submission. Replaces react-native-reanimated
 * with React Native's built-in Animated API.
 */
import { useEffect, useRef } from 'react';
import { Animated, Image, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';

import { tokens } from '@src/constants';
import { ISSUE_CATEGORY_MAP } from '@src/types/reports';

export default function SubmitSuccessScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<Record<string, string>>();

  // ── Entrance animations (React Native built-in Animated) ──────────────────
  const checkScale   = useRef(new Animated.Value(0)).current;
  const cardOpacity  = useRef(new Animated.Value(0)).current;
  const cardTranslateY = useRef(new Animated.Value(30)).current;

  useEffect(() => {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});

    Animated.sequence([
      Animated.spring(checkScale, {
        toValue: 1,
        friction: 5,
        tension:  120,
        useNativeDriver: true,
      }),
    ]).start();

    Animated.sequence([
      Animated.delay(400),
      Animated.parallel([
        Animated.spring(cardOpacity,    { toValue: 1, friction: 8, tension: 60, useNativeDriver: true }),
        Animated.spring(cardTranslateY, { toValue: 0, friction: 10, tension: 80, useNativeDriver: true }),
      ]),
    ]).start();
  }, []);

  const cat     = ISSUE_CATEGORY_MAP[params.category as keyof typeof ISSUE_CATEGORY_MAP];
  const icon    = cat?.icon  ?? 'location';
  const label   = cat?.label ?? params.category ?? 'Report';
  const photoUri = params.photoUri;
  const address  = params.address ?? 'Pune';
  const title    = params.title   ?? 'Your Report';

  // Transaction-style ID from backend UUID
  const txId = params.id
    ? `#${params.id.split('-')[0].toUpperCase()}`
    : `#${Date.now().toString(36).toUpperCase()}`;

  const checkAnimatedStyle = {
    transform: [{ scale: checkScale }],
  };

  const cardAnimatedStyle = {
    opacity:   cardOpacity,
    transform: [{ translateY: cardTranslateY }],
  };

  return (
    <View style={_s.container}>

      {/* ── Hero header ───────────────────────────────────────────────── */}
      <View style={_s.hero}>
        <Animated.View style={[ _s.checkCircle, checkAnimatedStyle ]}>
          <Ionicons name="checkmark" size={48} color="#fff" />
        </Animated.View>
        <Text style={_s.heroTitle}>Report Submitted!</Text>
        <Text style={_s.heroSubtitle}>Your civic voice has been heard.</Text>
      </View>

      {/* ── Receipt card ─────────────────────────────────────────────── */}
      <Animated.View style={[ _s.card, cardAnimatedStyle ]}>

        {/* Confirmation ID */}
        <View style={_s.txRow}>
          <Text style={_s.txLabel}>Confirmation No.</Text>
          <Text style={_s.txId}>{txId}</Text>
        </View>

        <View style={_s.divider} />

        {/* Category */}
        <View style={_s.row}>
          <View style={_s.rowLeft}>
            <View style={[ _s.iconBox, { backgroundColor: `${tokens.primary.DEFAULT}18` }]}>
              <Ionicons name={icon as any} size={15} color={tokens.primary.DEFAULT} />
            </View>
            <Text style={_s.rowLabelText}>Category</Text>
          </View>
          <Text style={_s.rowRight}>{label}</Text>
        </View>

        {/* Location */}
        <View style={_s.row}>
          <View style={_s.rowLeft}>
            <Ionicons name="location-outline" size={15} color={tokens.text.disabled} />
            <Text style={_s.rowLabelText}>Location</Text>
          </View>
          <Text style={[ _s.rowRight, _s.rowRightMultiline ]} numberOfLines={2}>
            {address}
          </Text>
        </View>

        {/* Issue title */}
        <View style={_s.row}>
          <View style={_s.rowLeft}>
            <Ionicons name="document-text-outline" size={15} color={tokens.text.disabled} />
            <Text style={_s.rowLabelText}>Issue</Text>
          </View>
          <Text style={[ _s.rowRight, _s.rowRightMultiline ]} numberOfLines={2}>
            {title}
          </Text>
        </View>

        <View style={_s.divider} />

        {/* 4-step timeline */}
        <View style={_s.timeline}>
          {[
            { icon: 'checkmark-circle',     label: 'Submitted',    active: true  },
            { icon: 'time-outline',         label: 'Under Review',  active: false },
            { icon: 'construct-outline',   label: 'In Progress',  active: false },
            { icon: 'checkmark-circle-outline', label: 'Resolved',  active: false },
          ].map((step, i) => (
            <View key={step.label} style={_s.timelineStep}>
              <View style={[
                _s.timelineDot,
                step.active && { backgroundColor: tokens.primary.DEFAULT },
              ]}>
                <Ionicons
                  name={step.icon as any}
                  size={13}
                  color={step.active ? '#fff' : tokens.text.disabled}
                />
              </View>
              {i < 3 && (
                <View style={[
                  _s.timelineLine,
                  step.active && { backgroundColor: tokens.primary.DEFAULT },
                ]} />
              )}
              <Text style={[
                _s.timelineLabel,
                step.active && { color: tokens.primary.DEFAULT, fontWeight: '800' },
              ]}>
                {step.label}
              </Text>
            </View>
          ))}
        </View>

        <View style={_s.divider} />

        {/* Primary CTA */}
        <TouchableOpacity
          style={_s.primaryBtn}
          activeOpacity={0.75}
          onPress={() => router.push('/(tabs)/reports')}
        >
          <Text style={_s.primaryBtnText}>View My Reports</Text>
        </TouchableOpacity>

        {/* Secondary CTA */}
        <TouchableOpacity
          style={_s.secondaryBtn}
          activeOpacity={0.75}
          onPress={() => router.push('/(tabs)')}
        >
          <Text style={_s.secondaryBtnText}>Back to Home</Text>
        </TouchableOpacity>
      </Animated.View>

      {/* Photo badge */}
      {photoUri ? (
        <View style={_s.photoBadge}>
          <Image source={{ uri: photoUri }} style={_s.photoThumb} />
          <Text style={_s.photoBadgeText}>Photo attached</Text>
        </View>
      ) : null}
    </View>
  );
}

// ── Styles (inline to avoid extra import) ─────────────────────────────────────
const _s = StyleSheet.create({
  container:    { flex: 1, backgroundColor: tokens.surface.bg },
  hero: {
    backgroundColor: tokens.primary.DEFAULT,
    paddingTop:    80,
    paddingBottom: 44,
    alignItems:   'center',
  },
  checkCircle: {
    width: 80, height: 80, borderRadius: 40,
    backgroundColor: 'rgba(255,255,255,0.22)',
    alignItems:    'center',
    justifyContent: 'center',
    marginBottom:  18,
  },
  heroTitle:    { fontSize: 26, fontWeight: '800', color: '#fff', letterSpacing: -0.5 },
  heroSubtitle: { fontSize: 14, color: 'rgba(255,255,255,0.85)', marginTop: 5 },

  card: {
    marginHorizontal: 16,
    marginTop:   -18,
    backgroundColor: '#fff',
    borderRadius: 18,
    padding:      20,
    shadowColor:  '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.09,
    shadowRadius: 14,
    elevation:    4,
  },

  txRow:     { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  txLabel:   { fontSize: 11, fontWeight: '700', color: tokens.text.disabled, textTransform: 'uppercase', letterSpacing: 0.8 },
  txId:      { fontSize: 15, fontWeight: '800', color: tokens.primary.DEFAULT, letterSpacing: 1 },
  divider:   { height: 1, backgroundColor: tokens.surface.border, marginVertical: 14 },

  row:        { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 },
  rowLeft:    { flexDirection: 'row', alignItems: 'center', gap: 7 },
  iconBox:    { width: 24, height: 24, borderRadius: 6, alignItems: 'center', justifyContent: 'center' },
  rowLabelText:{ fontSize: 12, color: tokens.text.disabled, fontWeight: '600' },
  rowRight:   { fontSize: 13, color: tokens.text.primary, fontWeight: '600', maxWidth: '58%', textAlign: 'right' },
  rowRightMultiline: { fontSize: 12, fontWeight: '500', lineHeight: 16 },

  timeline:   { flexDirection: 'row', justifyContent: 'space-between', marginVertical: 2 },
  timelineStep:{ flex: 1, alignItems: 'center' },
  timelineDot:{
    width: 28, height: 28, borderRadius: 14,
    backgroundColor: tokens.surface.border,
    alignItems: 'center', justifyContent: 'center',
  },
  timelineLine:{
    height: 2, width: '100%', backgroundColor: tokens.surface.border, marginVertical: 3,
  },
  timelineLabel:{ fontSize: 9, color: tokens.text.disabled, marginTop: 4, fontWeight: '600', textAlign: 'center' },

  primaryBtn:   {
    backgroundColor: tokens.primary.DEFAULT, borderRadius: 12,
    paddingVertical: 14, alignItems: 'center', marginBottom: 10,
  },
  primaryBtnText: { color: '#fff', fontWeight: '800', fontSize: 15 },
  secondaryBtn: {
    backgroundColor: tokens.surface.bg, borderRadius: 12,
    paddingVertical: 14, alignItems: 'center',
    borderWidth: 1, borderColor: tokens.surface.border,
  },
  secondaryBtnText:{ color: tokens.text.primary, fontWeight: '700', fontSize: 15 },

  photoBadge:   { flexDirection: 'row', alignItems: 'center', gap: 7, marginHorizontal: 20, marginTop: 16 },
  photoThumb:   { width: 32, height: 32, borderRadius: 6 },
  photoBadgeText:{ fontSize: 12, color: tokens.text.disabled },
});