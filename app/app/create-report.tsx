/**
 * Create Report Screen — CivicConnect Mobile
 * Executive incident report creation wizard matching the app design system.
 */
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Image,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';

import { api } from '@src/lib/api';
import { getCurrentLocation } from '@src/lib/location';
import { LeafletMap } from '@src/components/ui/LeafletMap';
import { ISSUE_CATEGORY_SLUGS, type CreateReportPayload, type IssueCategorySlug } from '@src/types/reports';

export default function CreateReportScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const params = useLocalSearchParams<Record<string, string>>();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState<IssueCategorySlug>('roads');
  const [address, setAddress] = useState<string>('Detecting location…');
  const [lat, setLat] = useState<number | null>(null);
  const [lng, setLng] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const photoUri = params.photoUri ?? '';
  const cloudinaryUrl = params.secure_url ?? params.url ?? '';
  const photoMetadataRaw = params.photoMetadata ?? '';

  useEffect(() => {
    getCurrentLocation().then((loc) => {
      setLat(loc.latitude);
      setLng(loc.longitude);
      setAddress(loc.address);
    });
  }, []);

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
      const parsedMetadataList = [];
      if (cloudinaryUrl && photoMetadataRaw) {
        try {
          const parsed = JSON.parse(photoMetadataRaw);
          parsedMetadataList.push({
            url: cloudinaryUrl,
            ...parsed,
          });
        } catch {
          // Ignore error
        }
      }

      const payload: CreateReportPayload = {
        title: title.trim(),
        description: description.trim(),
        issue_category: category,
        latitude: lat ?? 18.5204,
        longitude: lng ?? 73.8567,
        address: address,
        photos: cloudinaryUrl ? [cloudinaryUrl] : [],
        photo_metadata: parsedMetadataList,
        language: 'en',
      };

      const report = await api.post<{ id: string }>('/api/v1/reports/', payload);

      router.replace({
        pathname: '/submit-success',
        params: {
          id: report.id,
          title: title.trim(),
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
      style={styles.screen}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      {/* Header */}
      <View style={[styles.header, { paddingTop: Math.max(insets.top + 6, 40) }]}>
        <TouchableOpacity
          style={styles.backBtn}
          onPress={() => router.back()}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <Ionicons name="chevron-back" size={22} color="#0F172A" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>File Issue Report</Text>
        <View style={styles.stepPill}>
          <Text style={styles.stepPillText}>Step 2 of 2</Text>
        </View>
      </View>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* Photo Preview Section */}
        <View style={styles.photoContainer}>
          {photoUri ? (
            <View style={styles.photoWrapper}>
              <Image source={{ uri: photoUri }} style={styles.photoPreview} />
              <TouchableOpacity
                activeOpacity={0.8}
                style={styles.retakeBtn}
                onPress={() => router.replace('/camera')}
              >
                <Ionicons name="camera" size={13} color="#FFFFFF" />
                <Text style={styles.retakeBtnText}>Retake Photo</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <TouchableOpacity style={styles.photoPlaceholder} onPress={() => router.replace('/camera')}>
              <Ionicons name="camera-outline" size={28} color="#059669" />
              <Text style={styles.photoPlaceholderText}>Tap to capture photo</Text>
            </TouchableOpacity>
          )}
        </View>

        <View style={styles.formContainer}>
          {/* Category Selector */}
          <Text style={styles.sectionKicker}>Category *</Text>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            style={{ marginBottom: 16 }}
            contentContainerStyle={{ gap: 8 }}
          >
            {ISSUE_CATEGORY_SLUGS.map((cat) => {
              const active = category === cat.slug;
              return (
                <TouchableOpacity
                  key={cat.slug}
                  activeOpacity={0.8}
                  onPress={() => { setCategory(cat.slug); Haptics.selectionAsync(); }}
                  style={[
                    styles.categoryChip,
                    active && styles.categoryChipActive,
                  ]}
                >
                  <Ionicons
                    name={cat.icon as any}
                    size={14}
                    color={active ? '#059669' : '#64748B'}
                  />
                  <Text style={[
                    styles.categoryChipText,
                    active && styles.categoryChipTextActive,
                  ]}>
                    {cat.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>

          {/* Location Box & Leaflet Map */}
          <Text style={styles.sectionKicker}>Location (Auto-Detected)</Text>
          <View style={styles.locationBox}>
            <Ionicons name="location" size={16} color="#059669" />
            <Text style={styles.locationText} numberOfLines={2}>{address}</Text>
          </View>

          {Boolean(lat && lng) && (
            <View style={{ marginBottom: 16 }}>
              <LeafletMap
                latitude={lat!}
                longitude={lng!}
                address={address}
                height={160}
              />
            </View>
          )}

          {/* Issue Title */}
          <Text style={styles.sectionKicker}>Issue Title *</Text>
          <TextInput
            placeholder="e.g. Broken streetlight near Wakad Bridge"
            placeholderTextColor="#94A3B8"
            value={title}
            onChangeText={setTitle}
            maxLength={100}
            style={styles.input}
          />
          <Text style={styles.charCount}>{title.length}/100</Text>

          {/* Description */}
          <Text style={styles.sectionKicker}>Detailed Description *</Text>
          <TextInput
            placeholder="Describe the issue, location details, and any immediate safety hazards…"
            placeholderTextColor="#94A3B8"
            value={description}
            onChangeText={setDescription}
            multiline
            numberOfLines={4}
            style={[styles.input, styles.textArea]}
            textAlignVertical="top"
          />

          {/* Upload Status Badge */}
          {cloudinaryUrl ? (
            <View style={styles.uploadSuccess}>
              <Ionicons name="checkmark-circle" size={15} color="#059669" />
              <Text style={styles.uploadSuccessText}>Photo encrypted & attached</Text>
            </View>
          ) : (
            <View style={styles.uploadWarning}>
              <Ionicons name="information-circle-outline" size={15} color="#D97706" />
              <Text style={styles.uploadWarningText}>No photo attached — tap retake to add</Text>
            </View>
          )}
        </View>
      </ScrollView>

      {/* Bottom Submit Bar */}
      <View style={[styles.footer, { paddingBottom: Math.max(insets.bottom + 10, 16) }]}>
        <TouchableOpacity
          style={[styles.submitBtn, submitting && styles.submitBtnDisabled]}
          onPress={handleSubmit}
          disabled={submitting}
          activeOpacity={0.85}
        >
          {submitting ? (
            <View style={styles.btnRow}>
              <ActivityIndicator size="small" color="#FFFFFF" />
              <Text style={styles.submitBtnText}>Submitting Report…</Text>
            </View>
          ) : (
            <View style={styles.btnRow}>
              <Ionicons name="paper-plane" size={16} color="#FFFFFF" />
              <Text style={styles.submitBtnText}>Submit Report</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingBottom: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  backBtn: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: '#F8FAFC',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#0F172A',
  },
  stepPill: {
    backgroundColor: '#ECFDF5',
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderWidth: 1,
    borderColor: '#A7F3D0',
  },
  stepPillText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#059669',
  },

  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 40,
  },
  photoContainer: {
    paddingHorizontal: 20,
    paddingTop: 16,
  },
  photoWrapper: {
    borderRadius: 12,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    position: 'relative',
    height: 170,
  },
  photoPreview: {
    width: '100%',
    height: '100%',
  },
  retakeBtn: {
    position: 'absolute',
    top: 10,
    right: 10,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(15, 23, 42, 0.85)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  retakeBtnText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '700',
  },
  photoPlaceholder: {
    height: 130,
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderStyle: 'dashed',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  photoPlaceholderText: {
    fontSize: 12,
    color: '#64748B',
    fontWeight: '500',
  },

  formContainer: {
    paddingHorizontal: 20,
    paddingTop: 16,
    gap: 8,
  },
  sectionKicker: {
    fontSize: 10,
    fontWeight: '700',
    color: '#64748B',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 8,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  categoryChipActive: {
    backgroundColor: '#ECFDF5',
    borderColor: '#059669',
  },
  categoryChipText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#334155',
  },
  categoryChipTextActive: {
    color: '#059669',
    fontWeight: '700',
  },

  locationBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  locationText: {
    flex: 1,
    fontSize: 13,
    fontWeight: '500',
    color: '#0F172A',
  },

  input: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: '#0F172A',
  },
  textArea: {
    minHeight: 90,
    paddingTop: 10,
  },
  charCount: {
    fontSize: 10,
    fontWeight: '500',
    color: '#94A3B8',
    textAlign: 'right',
    marginTop: -4,
    marginBottom: 4,
  },

  uploadSuccess: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#ECFDF5',
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#A7F3D0',
    paddingHorizontal: 10,
    paddingVertical: 6,
    alignSelf: 'flex-start',
  },
  uploadSuccessText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#059669',
  },
  uploadWarning: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#FEF3C7',
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#FDE68A',
    paddingHorizontal: 10,
    paddingVertical: 6,
    alignSelf: 'flex-start',
  },
  uploadWarningText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#D97706',
  },

  footer: {
    paddingHorizontal: 20,
    paddingTop: 10,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
  },
  submitBtn: {
    backgroundColor: '#059669',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  submitBtnDisabled: {
    opacity: 0.6,
  },
  btnRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  submitBtnText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
});