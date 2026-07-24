import React from 'react';
import { StyleSheet, Text, View, ScrollView, Image, ActivityIndicator } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { reportService } from '../services';
import { MapPin, Calendar, ShieldCheck } from 'lucide-react-native';
import { PhotoItem, StatusLogItem } from '../types/domain';

const MapPinIcon = MapPin as any;
const CalendarIcon = Calendar as any;
const ShieldCheckIcon = ShieldCheck as any;

export default function ReportDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();

  const { data: report, isLoading } = useQuery({
    queryKey: ['report', id],
    queryFn: () => reportService.getReport(id!),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#38bdf8" />
      </View>
    );
  }

  if (!report) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Report not found.</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Card style={styles.headerCard}>
        <View style={styles.rowBetween}>
          <Badge label={report.issue_category} status="in_progress" />
          <Badge label={report.status} status={report.status} />
        </View>
        <Text style={styles.title}>{report.title}</Text>
        <Text style={styles.desc}>{report.description}</Text>
      </Card>

      {/* AI Multi-Agent Triage Insights */}
      {report.ai_summary && (
        <Card style={styles.aiCard}>
          <View style={styles.aiHeader}>
            <ShieldCheckIcon color="#38bdf8" size={22} />
            <Text style={styles.aiTitle}>AI Multi-Agent Triage Summary</Text>
          </View>
          <Text style={styles.aiSummary}>{report.ai_summary}</Text>
          {report.ai_priority_score && (
            <Text style={styles.aiScore}>Calculated Priority Score: {report.ai_priority_score}/100</Text>
          )}
        </Card>
      )}

      {/* Location Card */}
      {report.address && (
        <Card style={styles.card}>
          <View style={styles.row}>
            <MapPinIcon color="#f43f5e" size={20} />
            <Text style={styles.sectionLabel}>Location & Ward</Text>
          </View>
          <Text style={styles.infoText}>{report.address}</Text>
          {report.latitude && report.longitude && (
            <Text style={styles.geoText}>
              Coordinates: {report.latitude}, {report.longitude}
            </Text>
          )}
        </Card>
      )}

      {/* Photo Gallery */}
      {report.photos && report.photos.length > 0 && (
        <Card style={styles.card}>
          <Text style={styles.sectionLabel}>Attached Photos ({report.photos.length})</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.photoRow}>
            {report.photos.map((photo: PhotoItem) => (
              <Image
                key={photo.id}
                source={{ uri: photo.cloudinary_url }}
                style={styles.photo}
                resizeMode="cover"
              />
            ))}
          </ScrollView>
        </Card>
      )}

      {/* Status History Logs */}
      {report.status_logs && report.status_logs.length > 0 && (
        <Card style={styles.card}>
          <View style={styles.row}>
            <CalendarIcon color="#60a5fa" size={20} />
            <Text style={styles.sectionLabel}>Resolution Timeline</Text>
          </View>

          {report.status_logs.map((log: StatusLogItem) => (
            <View key={log.id} style={styles.timelineItem}>
              <View style={styles.timelineDot} />
              <View style={styles.timelineContent}>
                <Text style={styles.timelineStatus}>Status: {log.to_status.toUpperCase()}</Text>
                {log.reason && <Text style={styles.timelineReason}>{log.reason}</Text>}
                <Text style={styles.timelineTime}>{new Date(log.created_at).toLocaleString()}</Text>
              </View>
            </View>
          ))}
        </Card>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  content: {
    padding: 16,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0f172a',
  },
  errorText: {
    color: '#ef4444',
    fontSize: 16,
  },
  headerCard: {
    marginBottom: 12,
  },
  rowBetween: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  title: {
    fontSize: 22,
    fontWeight: '800',
    color: '#f8fafc',
    marginBottom: 8,
  },
  desc: {
    fontSize: 15,
    color: '#cbd5e1',
    lineHeight: 22,
  },
  aiCard: {
    backgroundColor: '#0c4a6e',
    borderColor: '#0284c7',
    marginBottom: 12,
  },
  aiHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  aiTitle: {
    color: '#38bdf8',
    fontSize: 15,
    fontWeight: '700',
    marginLeft: 8,
  },
  aiSummary: {
    color: '#e0f2fe',
    fontSize: 14,
    lineHeight: 20,
  },
  aiScore: {
    color: '#38bdf8',
    fontSize: 12,
    fontWeight: '600',
    marginTop: 8,
  },
  card: {
    marginBottom: 12,
  },
  sectionLabel: {
    fontSize: 15,
    fontWeight: '700',
    color: '#f8fafc',
    marginLeft: 6,
  },
  infoText: {
    color: '#cbd5e1',
    fontSize: 14,
    marginTop: 4,
  },
  geoText: {
    color: '#64748b',
    fontSize: 12,
    marginTop: 4,
  },
  photoRow: {
    flexDirection: 'row',
    marginTop: 10,
  },
  photo: {
    width: 140,
    height: 100,
    borderRadius: 10,
    marginRight: 10,
    backgroundColor: '#334155',
  },
  timelineItem: {
    flexDirection: 'row',
    marginTop: 12,
  },
  timelineDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#38bdf8',
    marginTop: 4,
    marginRight: 12,
  },
  timelineContent: {
    flex: 1,
  },
  timelineStatus: {
    color: '#f8fafc',
    fontWeight: '700',
    fontSize: 13,
  },
  timelineReason: {
    color: '#cbd5e1',
    fontSize: 13,
    marginTop: 2,
  },
  timelineTime: {
    color: '#64748b',
    fontSize: 11,
    marginTop: 4,
  },
});
