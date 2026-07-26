import { Platform, View, StyleSheet } from 'react-native';
import { WebView } from 'react-native-webview';

export interface LeafletMapProps {
  latitude: number;
  longitude: number;
  address?: string;
  height?: number;
}

export function LeafletMap({ latitude, longitude, address = 'Report Location', height = 200 }: LeafletMapProps) {
  const safeAddress = address.replace(/'/g, "\\'").replace(/\n/g, ' ');

  const htmlContent = `
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    html, body, #map {
      width: 100%;
      height: 100%;
      margin: 0;
      padding: 0;
      background: #f8fafc;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .leaflet-control-zoom {
      border: 1px solid #e2e8f0 !important;
      border-radius: 8px !important;
      overflow: hidden;
      box-shadow: 0 2px 6px rgba(0,0,0,0.08) !important;
    }
    .pulse-marker {
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .leaflet-popup-content-wrapper {
      border-radius: 10px;
      padding: 4px 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      font-size: 12px;
      font-weight: 600;
      color: #0f172a;
    }
    .leaflet-popup-tip {
      background: #ffffff;
    }
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
    document.addEventListener("DOMContentLoaded", function() {
      var lat = ${latitude};
      var lng = ${longitude};
      var map = L.map('map', {
        center: [lat, lng],
        zoom: 16,
        zoomControl: true,
        attributionControl: false
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19
      }).addTo(map);

      var svgPin = '<svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="18" cy="18" r="16" fill="#059669" fill-opacity="0.25"/><circle cx="18" cy="18" r="10" fill="#059669" stroke="#ffffff" stroke-width="2.5"/><circle cx="18" cy="18" r="4" fill="#ffffff"/></svg>';

      var customIcon = L.divIcon({
        className: 'pulse-marker',
        html: svgPin,
        iconSize: [36, 36],
        iconAnchor: [18, 18]
      });

      var marker = L.marker([lat, lng], { icon: customIcon }).addTo(map);
      marker.bindPopup('<b>Civic Location</b><br/>${safeAddress}').openPopup();
    });
  </script>
</body>
</html>
`;

  if (Platform.OS === 'web') {
    return (
      <View style={[styles.mapContainer, { height }]}>
        <iframe
          title="Leaflet Location Map"
          srcDoc={htmlContent}
          style={{
            width: '100%',
            height: '100%',
            border: 'none',
            borderRadius: 14,
          }}
        />
      </View>
    );
  }

  return (
    <View style={[styles.mapContainer, { height }]}>
      <WebView
        originWhitelist={['*']}
        source={{ html: htmlContent }}
        style={{ flex: 1, backgroundColor: 'transparent' }}
        scrollEnabled={false}
        javaScriptEnabled={true}
        domStorageEnabled={true}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  mapContainer: {
    width: '100%',
    borderRadius: 14,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    backgroundColor: '#f8fafc',
    marginTop: 8,
    marginBottom: 8,
  },
});
