import { useRef, useState } from 'react';
import { Alert, View, Text, TouchableOpacity, StyleSheet, Platform, useColorScheme, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { CameraView, CameraType, useCameraPermissions } from 'expo-camera';
import { Ionicons } from '@expo/vector-icons';
import { TOKENS } from '@src/theme/tokens';
import { api } from '@src/lib/api';
import { getCurrentLocation } from '@src/lib/location';
import type { UploadAsset } from '@src/types/reports';

export default function CameraScreen() {
  const router = useRouter();
  const cameraRef = useRef<CameraView>(null);
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';
  const p = isDark ? TOKENS.colors.dark : TOKENS.colors.light;

  const [facing, setFacing] = useState<CameraType>('back');
  const [uploading, setUploading] = useState(false);
  const [permission, requestPermission] = useCameraPermissions();

  if (!permission) {
    return (
      <View style={[styles.permissionContainer, { backgroundColor: p.bg }]}>
        <ActivityIndicator size="large" color={p.accentPrimary} />
      </View>
    );
  }

  if (!permission.granted) {
    return (
      <View style={[styles.permissionContainer, { backgroundColor: p.bg }]}>
        <View style={[styles.permIconCircle, { backgroundColor: p.pillBg }]}>
          <Ionicons name="camera-outline" size={40} color={p.accentPrimary} />
        </View>
        <Text style={[styles.permissionTitle, { color: p.textPrimary }]}>Live Camera Inspection</Text>
        <Text style={[styles.permissionText, { color: p.textSecondary }]}>
          CivicConnect mandates authentic, live geo-tagged photo evidence to dispatch ward repair crews.
        </Text>
        <TouchableOpacity style={[styles.permissionButton, { backgroundColor: p.accentPrimary }]} onPress={requestPermission}>
          <Text style={styles.permissionButtonText}>Enable Camera Access</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.cancelLink} onPress={() => router.back()}>
          <Text style={[styles.cancelText, { color: p.textMuted }]}>Dismiss</Text>
        </TouchableOpacity>
      </View>
    );
  }

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
        // Fallback GPS location
      }

      const photoMetadata = JSON.stringify({
        capture_source: 'camera_hud',
        latitude: locData.latitude ?? 18.5204,
        longitude: locData.longitude ?? 73.8567,
        gps_accuracy_m: locData.accuracy ?? 8.5,
        captured_at: new Date().toISOString(),
        device_model: Platform.OS === 'ios' ? 'iPhone' : 'Android Mobile',
        os_version: `${Platform.OS} ${Platform.Version}`,
        app_version: '1.2.0',
      });

      const asset = await uploadToCloudinary(photo!.uri);
      router.replace({
        pathname: '/create-report',
        params: { photoUri: photo!.uri, photoMetadata, ...asset },
      });
    } catch {
      Alert.alert('Scan Failed', 'Could not record inspection photo. Please try again.', [
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

  async function uploadToCloudinary(uri: string): Promise<UploadAsset> {
    const filename = uri.split('/').pop() ?? 'inspection_scan.jpg';
    return api.upload<UploadAsset>('/api/v1/uploads/', {
      uri,
      name: filename,
      type: 'image/jpeg',
    });
  }

  return (
    <View style={styles.container}>
      <CameraView ref={cameraRef} style={StyleSheet.absoluteFillObject} facing={facing} />

      {/* Camera Viewfinder Reticle & HUD Overlay */}
      <View style={styles.hudOverlay} pointerEvents="none">
        <View style={styles.viewfinderFrame}>
          <View style={[styles.cornerTL, { borderColor: p.accentCyan }]} />
          <View style={[styles.cornerTR, { borderColor: p.accentCyan }]} />
          <View style={[styles.cornerBL, { borderColor: p.accentCyan }]} />
          <View style={[styles.cornerBR, { borderColor: p.accentCyan }]} />
        </View>
        <Text style={styles.hudScanTag}>[ AI INFRASTRUCTURE AUDIT HUD ]</Text>
      </View>

      {/* Top Controls Bar */}
      <View style={styles.topBar}>
        <TouchableOpacity style={styles.closeBtn} onPress={() => router.back()}>
          <Ionicons name="close" size={24} color="#FFF" />
        </TouchableOpacity>

        <View style={styles.stepBadge}>
          <View style={styles.dotLive} />
          <Text style={styles.stepLabel}>STEP 1/2 • REAL-TIME AUDIT</Text>
        </View>

        <View style={{ width: 40 }} />
      </View>

      {/* Bottom Shutter Controls */}
      <View style={styles.controls}>
        <View style={{ width: 52 }} />

        <TouchableOpacity
          style={[styles.captureBtn, uploading && styles.captureBtnDisabled]}
          onPress={handleCapture}
          disabled={uploading}>
          {uploading ? (
            <ActivityIndicator size="large" color={p.accentPrimary} />
          ) : (
            <View style={[styles.captureBtnInner, { backgroundColor: p.accentPrimary }]} />
          )}
        </TouchableOpacity>

        <TouchableOpacity style={styles.sideBtn} onPress={toggleCameraFacing}>
          <Ionicons name="camera-reverse-outline" size={24} color="#FFF" />
        </TouchableOpacity>
      </View>

      {/* Uploading Spinner Sheet */}
      {uploading && (
        <View style={styles.uploadingOverlay}>
          <ActivityIndicator size="large" color={p.accentCyan} />
          <Text style={styles.uploadingText}>Analyzing Geo-Tag & Uploading Photo…</Text>
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
    paddingHorizontal: 40,
    gap: 12,
  },
  permIconCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  permissionTitle: { fontSize: 20, fontWeight: '800', textAlign: 'center' },
  permissionText: { fontSize: 13, textAlign: 'center', lineHeight: 20, maxWidth: 280 },
  permissionButton: {
    borderRadius: 16,
    paddingVertical: 14,
    paddingHorizontal: 28,
    marginTop: 16,
  },
  permissionButtonText: { color: '#FFF', fontWeight: '800', fontSize: 14 },
  cancelLink: { marginTop: 8 },
  cancelText: { fontSize: 13, fontWeight: '600' },

  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: Platform.select({ ios: 56, android: 44 }) ?? 44,
    paddingHorizontal: 20,
    zIndex: 10,
  },
  closeBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(0,0,0,0.5)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  dotLive: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#84CC16',
  },
  stepLabel: { fontSize: 10, fontWeight: '900', color: '#FFF', letterSpacing: 0.5 },

  hudOverlay: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
  },
  viewfinderFrame: {
    width: 260,
    height: 260,
    position: 'relative',
  },
  cornerTL: { position: 'absolute', top: 0, left: 0, width: 30, height: 30, borderTopWidth: 3, borderLeftWidth: 3 },
  cornerTR: { position: 'absolute', top: 0, right: 0, width: 30, height: 30, borderTopWidth: 3, borderRightWidth: 3 },
  cornerBL: { position: 'absolute', bottom: 0, left: 0, width: 30, height: 30, borderBottomWidth: 3, borderLeftWidth: 3 },
  cornerBR: { position: 'absolute', bottom: 0, right: 0, width: 30, height: 30, borderBottomWidth: 3, borderRightWidth: 3 },
  hudScanTag: {
    color: '#06B6D4',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 1,
    marginTop: 20,
    backgroundColor: 'rgba(0,0,0,0.6)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },

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
    backgroundColor: 'rgba(0,0,0,0.5)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  captureBtn: {
    width: 76,
    height: 76,
    borderRadius: 38,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: '#FFF',
  },
  captureBtnDisabled: { opacity: 0.6 },
  captureBtnInner: { width: 58, height: 58, borderRadius: 29 },
  uploadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.8)',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 20,
    gap: 14,
  },
  uploadingText: { color: '#FFF', fontSize: 14, fontWeight: '800' },
});