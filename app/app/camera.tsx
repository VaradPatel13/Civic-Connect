/**
 * Camera Capture Screen — CivicConnect
 *
 * Full-screen camera that opens immediately on FAB tap.
 * User takes ONE live photo → uploads to backend/Cloudinary → advances to create-report.
 * Note: Gallery uploads are strictly disabled to enforce authentic civic reporting.
 */
import { useRef, useState } from 'react';
import { Alert, View, Text, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { CameraView, CameraType, useCameraPermissions } from 'expo-camera';
import { Ionicons } from '@expo/vector-icons';
import { tokens } from '@src/constants';
import { api } from '@src/lib/api';
import { getCurrentLocation } from '@src/lib/location';
import type { UploadAsset } from '@src/types/reports';

export default function CameraScreen() {
  const router = useRouter();
  const cameraRef = useRef<CameraView>(null);
  const [facing, setFacing] = useState<CameraType>('back');
  const [uploading, setUploading] = useState(false);
  const [permission, requestPermission] = useCameraPermissions();

  // ── Permission loading ───────────────────────────────────────────────────
  if (!permission) {
    return (
      <View style={styles.permissionContainer}>
        <Text style={styles.permissionText}>Loading camera…</Text>
      </View>
    );
  }

  // ── Permission denied ────────────────────────────────────────────────────
  if (!permission.granted) {
    return (
      <View style={styles.permissionContainer}>
        <Ionicons name="camera-outline" size={52} color={tokens.text.disabled} />
        <Text style={styles.permissionTitle}>Camera Access Needed</Text>
        <Text style={styles.permissionText}>
          CivicConnect requires live camera access to photograph civic issues in real-time.
        </Text>
        <TouchableOpacity style={styles.permissionButton} onPress={requestPermission}>
          <Text style={styles.permissionButtonText}>Grant Permission</Text>
        </TouchableOpacity>
        <TouchableOpacity style={{ marginTop: 16 }} onPress={() => router.back()}>
          <Text style={{ color: tokens.text.secondary, fontSize: 14, fontWeight: '600' }}>Cancel</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // ── Capture photo → upload → navigate ────────────────────────────────────
  async function handleCapture() {
    if (!cameraRef.current || uploading) return;

    setUploading(true);
    try {
      const photo = await cameraRef.current.takePictureAsync({ quality: 0.8 });
      let locData: { latitude?: number; longitude?: number; accuracy?: number } = {};
      try {
        const loc = await getCurrentLocation();
        locData = { latitude: loc.latitude, longitude: loc.longitude, accuracy: loc.accuracy };
      } catch {
        // Fallback location if permission or GPS read fails
      }
      

      const photoMetadata = JSON.stringify({
        capture_source: 'camera',
        latitude: locData.latitude ?? 18.5204,
        longitude: locData.longitude ?? 73.8567,
        gps_accuracy_m: locData.accuracy ?? 10.0,
        captured_at: new Date().toISOString(),
        device_model: Platform.OS === 'ios' ? 'iOS Device' : 'Android Device',
        os_version: `${Platform.OS} ${Platform.Version}`,
        app_version: '1.0.0',
      });

      const asset = await uploadToCloudinary(photo!.uri);
      router.replace({
        pathname: '/create-report',
        params: { photoUri: photo!.uri, photoMetadata, ...asset },
      });
    } catch {
      Alert.alert('Capture Failed', 'Could not capture photo. Please try again.', [
        { text: 'Retry', onPress: handleCapture },
        { text: 'Cancel', style: 'cancel' },
      ]);
    } finally {
      setUploading(false);
    }
  }

  function toggleCameraFacing() {
    setFacing((current) => (current === 'back' ? 'front' : 'back'));
  }

  // ── Upload to backend which pushes to Cloudinary ──────────────────────────
  async function uploadToCloudinary(uri: string): Promise<UploadAsset> {
    const filename = uri.split('/').pop() ?? 'photo.jpg';
    return api.upload<UploadAsset>('/api/v1/uploads/', {
      uri,
      name: filename,
      type: 'image/jpeg',
    });
  }

  return (
    <View style={styles.container}>
      <CameraView
        ref={cameraRef}
        style={StyleSheet.absoluteFillObject}
        facing={facing}
      />

      {/* Top bar */}
      <View style={styles.topBar}>
        <TouchableOpacity
          style={styles.closeBtn}
          onPress={() => router.back()}
        >
          <Ionicons name="close" size={26} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.stepLabel}>Step 1 of 2 · Live Camera</Text>
        <View style={{ width: 40 }} />
      </View>

      {/* Bottom controls */}
      <View style={styles.controls}>
        {/* Spacer */}
        <View style={{ width: 52 }} />

        {/* Capture button */}
        <TouchableOpacity
          style={[styles.captureBtn, uploading && styles.captureBtnDisabled]}
          onPress={handleCapture}
          disabled={uploading}
        >
          {uploading ? (
            <Ionicons name="cloud-upload-outline" size={36} color="#fff" />
          ) : (
            <View style={styles.captureBtnInner} />
          )}
        </TouchableOpacity>

        {/* Flip camera */}
        <TouchableOpacity style={styles.sideBtn} onPress={toggleCameraFacing}>
          <Ionicons name="camera-reverse-outline" size={26} color="#fff" />
        </TouchableOpacity>
      </View>

      {/* Upload progress overlay */}
      {uploading && (
        <View style={styles.uploadingOverlay}>
          <Ionicons name="cloud-upload-outline" size={40} color="#fff" />
          <Text style={styles.uploadingText}>Uploading photo…</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  permissionContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: tokens.surface.bg,
    paddingHorizontal: 40,
  },
  permissionTitle: { fontSize: 20, fontWeight: '800', color: tokens.text.primary, marginTop: 16, textAlign: 'center' },
  permissionText: { fontSize: 14, color: tokens.text.secondary, marginTop: 8, textAlign: 'center', lineHeight: 22 },
  permissionButton: {
    backgroundColor: tokens.primary.DEFAULT,
    borderRadius: 24,
    paddingVertical: 13,
    paddingHorizontal: 28,
    marginTop: 28,
  },
  permissionButtonText: { color: '#fff', fontWeight: '800', fontSize: 15 },

  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 56,
    paddingHorizontal: 20,
    zIndex: 10,
  },
  closeBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(0,0,0,0.4)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepLabel: { fontSize: 12, fontWeight: '700', color: '#fff', letterSpacing: 1 },
  controls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    position: 'absolute',
    bottom: 48,
    left: 0,
    right: 0,
    zIndex: 10,
  },
  sideBtn: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: 'rgba(0,0,0,0.4)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  captureBtn: {
    width: 76,
    height: 76,
    borderRadius: 38,
    backgroundColor: 'rgba(255,255,255,0.3)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: '#fff',
  },
  captureBtnDisabled: { opacity: 0.6 },
  captureBtnInner: { width: 56, height: 56, borderRadius: 28, backgroundColor: '#fff' },
  uploadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.65)',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 20,
  },
  uploadingText: { color: '#fff', fontSize: 16, fontWeight: '700', marginTop: 12 },
});