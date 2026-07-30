/**
 * Create Report Screen — CivicConnect
 *
 * Step 2 of 2 (after camera).
 * Arrives from camera.tsx with:
 *   - photoUri:          local URI of the captured photo
 *   - secure_url (etc):  Cloudinary response fields
 *
 * Auto-detects location, collects title + category + description,
 * then submits to POST /api/v1/reports and navigates to submit-success.
 */
import { useEffect, useState } from 'react';
import {
  ActivityIndicator, Alert, Image, KeyboardAvoidingView,
  Platform, ScrollView, StyleSheet, Text, TextInput,
  TouchableOpacity, View,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';

import { tokens }       from '@src/constants';
import { api }          from '@src/lib/api';
import { getCurrentLocation } from '@src/lib/location';
import { LeafletMap }   from '@src/components/ui/LeafletMap';
import { ISSUE_CATEGORY_SLUGS, type CreateReportPayload, type IssueCategorySlug } from '@src/types/reports';

export default function CreateReportScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const params = useLocalSearchParams<Record<string, string>>();

  // ── Form state ───────────────────────────────────────────────────────────────
  const [title,       setTitle]       = useState('');
  const [description, setDescription] = useState('');
  const [category,    setCategory]    = useState<IssueCategorySlug>('roads');
  const [address,     setAddress]     = useState<string>('Detecting location…');
  const [lat,         setLat]         = useState<number | null>(null);
  const [lng,         setLng]         = useState<number | null>(null);
  const [submitting,  setSubmitting]  = useState(false);
  const [step]        = useState(2);

  // Pre-filled from camera screen
  const photoUri      = params.photoUri    ?? '';
  const cloudinaryUrl = params.secure_url ?? params.url ?? '';
  const photoMetadataRaw = params.photoMetadata ?? '';

  // ── Auto-detect location on mount ────────────────────────────────────────────
  useEffect(() => {
    getCurrentLocation().then(loc => {
      setLat(loc.latitude);
      setLng(loc.longitude);
      setAddress(loc.address);
    });
  }, []);

  // ── Submit ────────────────────────────────────────────────────────────────────
  async function handleSubmit() {
    if (submitting) return;

    if (!title.trim()) {
      Alert.alert('Title Required', 'Please add a short title for your report.');
      return;
    }
    if (title.trim().length < 3) {
      Alert.alert('Title Too Short', 'Title must be at least 3 characters.');
      return;
    }
    if (!description.trim() || description.trim().length < 10) {
      Alert.alert('Description Required', 'Please describe the issue in at least 10 characters.');
      return;
    }

    setSubmitting(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      let parsedMetadataList = [];
      if (cloudinaryUrl && photoMetadataRaw) {
        try {
          const parsed = JSON.parse(photoMetadataRaw);
          parsedMetadataList.push({
            url: cloudinaryUrl,
            ...parsed,
          });
        } catch {
          // Ignore JSON parse error if raw metadata is invalid
        }
      }

      const payload: CreateReportPayload = {
        title:          title.trim(),
        description:    description.trim(),
        issue_category: category,
        latitude:       lat ?? 18.5204,
        longitude:      lng ?? 73.8567,
        address:        address,
        photos:         cloudinaryUrl ? [cloudinaryUrl] : [],
        photo_metadata: parsedMetadataList,
        language:       'en',
      };

      const report = await api.post<{ id: string }>('/api/v1/reports/', payload);

      router.replace({
        pathname: '/submit-success',
        params: {
          id:       report.id,
          title:    title.trim(),
          category,
          address,
          photoUri,
        },
      });

    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Submission failed';
      Alert.alert('Submission Failed', msg, [
        { text: 'Retry', onPress: handleSubmit },
        { text: 'Cancel', style: 'cancel' },
      ]);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: tokens.surface.bg }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      {/* Safe Header */}
      <View style={[styles.header, { paddingTop: Math.max(insets.top + 8, 44) }]}>
        <TouchableOpacity
          style={styles.backBtn}
          onPress={() => router.back()}
          hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
        >
          <Ionicons name="chevron-back" size={24} color={tokens.text.primary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>File Report</Text>
        <View style={styles.stepPill}>
          <Text style={styles.stepPillText}>Step {step} of 2</Text>
        </View>
      </View>

      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={{ paddingBottom: 100 }}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* ── Photo Preview Header ────────────────────────────────────────── */}
        <View style={styles.photoContainer}>
          {photoUri ? (
            <View style={styles.photoWrapper}>
              <Image source={{ uri: photoUri }} style={styles.photoPreview} />
              <TouchableOpacity
                activeOpacity={0.8}
                style={styles.floatingRetakeBtn}
                onPress={() => router.replace('/camera')}
              >
                <Ionicons name="camera" size={14} color="#fff" />
                <Text style={styles.floatingRetakeText}>Retake</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <TouchableOpacity style={styles.photoPlaceholder} onPress={() => router.replace('/camera')}>
              <Ionicons name="camera-outline" size={32} color={tokens.primary.DEFAULT} />
              <Text style={styles.photoPlaceholderText}>Tap to capture live photo</Text>
            </TouchableOpacity>
          )}
        </View>

        <View style={styles.formContainer}>
          {/* ── Category Selector ─────────────────────────────────────────── */}
          <Text style={styles.sectionLabel}>Category *</Text>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            style={{ marginBottom: 20 }}
            contentContainerStyle={{ gap: 8, paddingRight: 16 }}
          >
            {ISSUE_CATEGORY_SLUGS.map(cat => {
              const active = category === cat.slug;
              return (
                <TouchableOpacity
                  key={cat.slug}
                  activeOpacity={0.8}
                  onPress={() => { setCategory(cat.slug); Haptics.selectionAsync(); }}
                  style={[
                    styles.categoryChip,
                    active ? styles.categoryChipActive : styles.categoryChipInactive,
                  ]}
                >
                  <Ionicons
                    name={cat.icon as any}
                    size={14}
                    color={active ? '#fff' : tokens.text.secondary}
                  />
                  <Text style={[
                    styles.categoryChipText,
                    active ? styles.categoryChipTextActive : styles.categoryChipTextInactive,
                  ]}>
                    {cat.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>

          {/* ── Auto-detected Location & Leaflet Map ───────────────────────── */}
          <Text style={styles.sectionLabel}>Location (auto-detected)</Text>
          <View style={styles.locationBox}>
            <Ionicons name="location" size={16} color={tokens.primary.DEFAULT} />
            <Text style={styles.locationText} numberOfLines={2}>{address}</Text>
            <TouchableOpacity onPress={() => router.replace('/camera')}>
              <Ionicons name="refresh-outline" size={18} color={tokens.text.disabled} />
            </TouchableOpacity>
          </View>

          {Boolean(lat && lng) && (
            <View style={{ marginBottom: 18 }}>
              <LeafletMap
                latitude={lat!}
                longitude={lng!}
                address={address}
                height={190}
              />
              <Text style={styles.coordText}>
                GPS Coordinates: {lat!.toFixed(5)}° N, {lng!.toFixed(5)}° E
              </Text>
            </View>
          )}

          {/* ── Issue Title ─────────────────────────────────────────────────── */}
          <Text style={styles.sectionLabel}>Issue Title *</Text>
          <TextInput
            placeholder="e.g. Broken streetlight near Wakad Bridge"
            placeholderTextColor={tokens.text.disabled}
            value={title}
            onChangeText={setTitle}
            maxLength={100}
            style={styles.input}
          />
          <Text style={styles.charCount}>{title.length}/100</Text>

          {/* ── Description ───────────────────────────────────────────────── */}
          <Text style={styles.sectionLabel}>Detailed Description *</Text>
          <TextInput
            placeholder="Describe the issue, location details, and any immediate safety hazards…"
            placeholderTextColor={tokens.text.disabled}
            value={description}
            onChangeText={setDescription}
            multiline
            numberOfLines={4}
            style={[styles.input, styles.textArea]}
            textAlignVertical="top"
          />

          {/* ── Upload Status Badge ────────────────────────────────────────── */}
          {cloudinaryUrl ? (
            <View style={styles.uploadChipSuccess}>
              <Ionicons name="checkmark-circle" size={16} color={tokens.success.DEFAULT} />
              <Text style={styles.uploadChipSuccessText}>Photo encrypted & attached</Text>
            </View>
          ) : (
            <View style={styles.uploadChipWarning}>
              <Ionicons name="information-circle-outline" size={16} color={tokens.accent.DEFAULT} />
              <Text style={styles.uploadChipWarningText}>No photo attached — tap retake to add one</Text>
            </View>
          )}
        </View>
      </ScrollView>

      {/* ── Bottom Submit Bar ───────────────────────────────────────────────── */}
      <View style={[styles.footer, { paddingBottom: Math.max(insets.bottom + 12, 20) }]}>
        <TouchableOpacity
          style={[styles.submitBtn, submitting && styles.submitBtnDisabled]}
          onPress={handleSubmit}
          disabled={submitting}
          activeOpacity={0.85}
        >
          {submitting ? (
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
              <ActivityIndicator size="small" color="#fff" />
              <Text style={styles.submitBtnText}>Submitting Report…</Text>
            </View>
          ) : (
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <Ionicons name="paper-plane" size={18} color="#fff" />
              <Text style={styles.submitBtnText}>Submit Report</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 18,
    paddingBottom: 14,
    backgroundColor: tokens.surface.card,
    borderBottomWidth: 1,
    borderBottomColor: tokens.surface.border,
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: `${tokens.primary.DEFAULT}0a`,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '900',
    color: tokens.text.primary,
    letterSpacing: -0.3,
  },
  stepPill: {
    backgroundColor: `${tokens.primary.DEFAULT}12`,
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  stepPillText: {
    fontSize: 11,
    fontWeight: '800',
    color: tokens.primary.DEFAULT,
  },

  photoContainer: {
    paddingHorizontal: 18,
    paddingTop: 16,
  },
  photoWrapper: {
    borderRadius: 16,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: tokens.surface.border,
    position: 'relative',
    height: 190,
  },
  photoPreview: {
    width: '100%',
    height: '100%',
  },
  floatingRetakeBtn: {
    position: 'absolute',
    top: 12,
    right: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(15, 23, 42, 0.8)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  floatingRetakeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '700',
  },
  photoPlaceholder: {
    height: 150,
    borderRadius: 16,
    backgroundColor: tokens.surface.card,
    borderWidth: 1.5,
    borderColor: tokens.surface.border,
    borderStyle: 'dashed',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  photoPlaceholderText: {
    fontSize: 13,
    color: tokens.text.secondary,
    fontWeight: '600',
  },

  formContainer: {
    paddingHorizontal: 18,
    paddingTop: 18,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '900',
    color: tokens.text.disabled,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: 14,
    borderWidth: 1,
  },
  categoryChipActive: {
    backgroundColor: tokens.primary.DEFAULT,
    borderColor: tokens.primary.DEFAULT,
  },
  categoryChipInactive: {
    backgroundColor: tokens.surface.card,
    borderColor: tokens.surface.border,
  },
  categoryChipText: {
    fontSize: 13,
    fontWeight: '700',
  },
  categoryChipTextActive: {
    color: '#fff',
  },
  categoryChipTextInactive: {
    color: tokens.text.primary,
  },

  locationBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: tokens.surface.card,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: tokens.surface.border,
    paddingHorizontal: 14,
    paddingVertical: 12,
    marginBottom: 4,
  },
  locationText: {
    flex: 1,
    fontSize: 13,
    fontWeight: '600',
    color: tokens.text.primary,
  },
  coordText: {
    fontSize: 11,
    fontWeight: '600',
    color: tokens.text.disabled,
    marginTop: 4,
  },

  input: {
    backgroundColor: tokens.surface.card,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: tokens.surface.border,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 14,
    fontWeight: '500',
    color: tokens.text.primary,
    marginBottom: 4,
  },
  textArea: {
    minHeight: 100,
    paddingTop: 12,
  },
  charCount: {
    fontSize: 10,
    fontWeight: '600',
    color: tokens.text.disabled,
    textAlign: 'right',
    marginBottom: 16,
  },

  uploadChipSuccess: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: tokens.success.light,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
    alignSelf: 'flex-start',
    marginTop: 4,
  },
  uploadChipSuccessText: {
    fontSize: 12,
    fontWeight: '800',
    color: tokens.success.DEFAULT,
  },
  uploadChipWarning: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: tokens.accent.light,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
    alignSelf: 'flex-start',
    marginTop: 4,
  },
  uploadChipWarningText: {
    fontSize: 12,
    fontWeight: '700',
    color: tokens.accent.DEFAULT,
  },

  footer: {
    paddingHorizontal: 18,
    paddingTop: 12,
    backgroundColor: tokens.surface.card,
    borderTopWidth: 1,
    borderTopColor: tokens.surface.border,
  },
  submitBtn: {
    backgroundColor: tokens.primary.DEFAULT,
    borderRadius: 16,
    paddingVertical: 15,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: tokens.primary.DEFAULT,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 4,
  },
  submitBtnDisabled: { opacity: 0.6 },
  submitBtnText: { color: '#fff', fontSize: 16, fontWeight: '900', letterSpacing: 0.3 },
});