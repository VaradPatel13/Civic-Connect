import { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  Image,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Share,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { tokens } from '@src/constants';
import { CATEGORY_ICON } from '@src/constants/categoryIcons';
import { api } from '@src/lib/api';
import { useDashboardStore } from '@src/store';

export default function ReportDetailsScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const dashboardReports = useDashboardStore((s) => s.reports);

  // Find report from store as initial fallback
  const initialReport = dashboardReports.find((r) => r.id === id);

  const [report, setReport] = useState<any>(initialReport ?? null);
  const [loading, setLoading] = useState(!initialReport);
  const [refreshing, setRefreshing] = useState(false);
  const [imgError, setImgError] = useState(false);
  const [upvoted, setUpvoted] = useState(false);
  const [upvoteCount, setUpvoteCount] = useState(initialReport?.upvotes ?? 0);

  const fetchDetails = async () => {
    if (!id) return;
    try {
      const data = await api.get<any>(`/api/v1/reports/${id}`);
      setReport(data);
      if (data.upvotes !== undefined) setUpvoteCount(data.upvotes);
    } catch {
      // Keep existing report if network call fails or unauthenticated
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDetails();
  }, [id]);

  const handleShare = async () => {
    if (!report) return;
    try {
      await Share.share({
        message: `CivicConnect Report: ${report.title}\nStatus: ${report.status}\nLocation: ${report.address || report.location?.address || 'Pune'}`,
      });
    } catch {
      // Ignored
    }
  };

  const handleUpvote = () => {
    setUpvoted(!upvoted);
    setUpvoteCount((prev) => (upvoted ? prev - 1 : prev + 1));
  };

  if (loading && !report) {
    return (
      <View style={{ flex: 1, backgroundColor: tokens.surface.bg, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color={tokens.primary.DEFAULT} />
        <Text style={{ marginTop: 12, color: tokens.text.secondary, fontSize: 14 }}>Loading report details...</Text>
      </View>
    );
  }

  if (!report) {
    return (
      <View style={{ flex: 1, backgroundColor: tokens.surface.bg, justifyContent: 'center', alignItems: 'center', padding: 20 }}>
        <Ionicons name="alert-circle-outline" size={48} color={tokens.text.disabled} />
        <Text style={{ fontSize: 18, fontWeight: '700', color: tokens.text.primary, marginTop: 12 }}>Report Not Found</Text>
        <TouchableOpacity
          onPress={() => router.back()}
          style={{ marginTop: 20, backgroundColor: tokens.primary.DEFAULT, paddingHorizontal: 20, paddingVertical: 10, borderRadius: 8 }}
        >
          <Text style={{ color: '#fff', fontWeight: '700' }}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Format images
  const photosList = report.photos ?? report.images ?? [];
  const firstPhoto = photosList[0];
  const mainImageUrl = typeof firstPhoto === 'string'
    ? firstPhoto
    : firstPhoto?.cloudinary_url || firstPhoto?.secure_url || firstPhoto?.url;

  const categoryKey = report.issue_category ?? report.category ?? 'other';
  const catIcon = CATEGORY_ICON[categoryKey as keyof typeof CATEGORY_ICON] ?? 'location';
  const statusStr = (report.status ?? 'open').toLowerCase();
  const statusColor =
    statusStr === 'resolved' ? tokens.success.DEFAULT
    : statusStr === 'in_progress' || statusStr === 'assigned' || statusStr === 'processing' ? tokens.info.DEFAULT
    : tokens.accent.DEFAULT;

  return (
    <View style={{ flex: 1, backgroundColor: tokens.surface.bg }}>
      {/* Top Header Navigation */}
      <View style={{
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingHorizontal: 16,
        paddingTop: 48,
        paddingBottom: 12,
        backgroundColor: tokens.surface.card,
        borderBottomWidth: 1,
        borderBottomColor: tokens.surface.border,
        zIndex: 10,
      }}>
        <TouchableOpacity onPress={() => router.back()} style={{ padding: 4 }}>
          <Ionicons name="arrow-back" size={24} color={tokens.text.primary} />
        </TouchableOpacity>
        <Text style={{ fontSize: 16, fontWeight: '700', color: tokens.text.primary }}>Report Details</Text>
        <TouchableOpacity onPress={handleShare} style={{ padding: 4 }}>
          <Ionicons name="share-outline" size={22} color={tokens.text.primary} />
        </TouchableOpacity>
      </View>

      <ScrollView
        style={{ flex: 1 }}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => { setRefreshing(true); fetchDetails(); }}
            tintColor={tokens.primary.DEFAULT}
          />
        }
      >
        {/* Media Hero Section */}
        <View style={{ height: 240, backgroundColor: `${tokens.primary.DEFAULT}12`, position: 'relative' }}>
          {mainImageUrl && !imgError ? (
            <Image
              source={{ uri: mainImageUrl }}
              style={{ width: '100%', height: '100%' }}
              onError={() => setImgError(true)}
              resizeMode="cover"
            />
          ) : (
            <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
              <Ionicons name={catIcon as any} size={64} color={tokens.primary.light} />
              <Text style={{ color: tokens.text.disabled, marginTop: 8, fontSize: 13 }}>No Photo Available</Text>
            </View>
          )}

          {/* Badges Overlay */}
          <View style={{ position: 'absolute', bottom: 12, left: 16, right: 16, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
            <View style={{ backgroundColor: statusColor, borderRadius: 6, paddingHorizontal: 10, paddingVertical: 4 }}>
              <Text style={{ fontSize: 11, fontWeight: '800', color: '#fff', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                {statusStr.replace('_', ' ')}
              </Text>
            </View>

            <View style={{ backgroundColor: 'rgba(0,0,0,0.65)', borderRadius: 6, paddingHorizontal: 10, paddingVertical: 4 }}>
              <Text style={{ fontSize: 11, fontWeight: '700', color: '#fff', textTransform: 'capitalize' }}>
                {categoryKey.replace('_', ' ')}
              </Text>
            </View>
          </View>
        </View>

        {/* Content Body */}
        <View style={{ padding: 20 }}>
          {/* Title & Date */}
          <Text style={{ fontSize: 20, fontWeight: '800', color: tokens.text.primary, lineHeight: 26, marginBottom: 8 }}>
            {report.title}
          </Text>

          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
              <Ionicons name="time-outline" size={14} color={tokens.text.disabled} />
              <Text style={{ fontSize: 12, color: tokens.text.secondary }}>
                {report.created_at ? new Date(report.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : 'Recently'}
              </Text>
            </View>
            {report.urgency && (
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                <Ionicons name="flame-outline" size={14} color={tokens.accent.DEFAULT} />
                <Text style={{ fontSize: 12, color: tokens.accent.DEFAULT, fontWeight: '700', textTransform: 'uppercase' }}>
                  {report.urgency} Urgency
                </Text>
              </View>
            )}
          </View>

          {/* Description */}
          <View style={{ backgroundColor: tokens.surface.card, borderRadius: 12, padding: 16, marginBottom: 16, borderWidth: 1, borderColor: tokens.surface.border }}>
            <Text style={{ fontSize: 12, fontWeight: '700', color: tokens.text.disabled, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 6 }}>
              Description
            </Text>
            <Text style={{ fontSize: 14, color: tokens.text.primary, lineHeight: 22 }}>
              {report.description || 'No detailed description provided.'}
            </Text>

            {report.summary && (
              <View style={{ marginTop: 12, paddingTop: 12, borderTopWidth: 1, borderTopColor: tokens.surface.border }}>
                <Text style={{ fontSize: 11, fontWeight: '700', color: tokens.primary.DEFAULT, marginBottom: 4 }}>
                  ✨ AI Summary
                </Text>
                <Text style={{ fontSize: 13, color: tokens.text.secondary, lineHeight: 19 }}>
                  {report.summary}
                </Text>
              </View>
            )}
          </View>

          {/* Location & Ward */}
          <View style={{ backgroundColor: tokens.surface.card, borderRadius: 12, padding: 16, marginBottom: 16, borderWidth: 1, borderColor: tokens.surface.border }}>
            <Text style={{ fontSize: 12, fontWeight: '700', color: tokens.text.disabled, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 8 }}>
              Location & Jurisdiction
            </Text>

            <View style={{ flexDirection: 'row', alignItems: 'flex-start', gap: 10 }}>
              <Ionicons name="location" size={20} color={tokens.primary.DEFAULT} style={{ marginTop: 2 }} />
              <View style={{ flex: 1 }}>
                <Text style={{ fontSize: 14, fontWeight: '600', color: tokens.text.primary, marginBottom: 2 }}>
                  {report.address || report.location?.address || 'Pune Municipal Corporation'}
                </Text>
                {(report.latitude || report.location?.lat) && (
                  <Text style={{ fontSize: 12, color: tokens.text.disabled }}>
                    GPS: {(report.latitude ?? report.location?.lat)?.toFixed(4)}, {(report.longitude ?? report.location?.lng)?.toFixed(4)}
                  </Text>
                )}
                {report.ward && (
                  <Text style={{ fontSize: 12, color: tokens.text.secondary, marginTop: 4 }}>
                    Ward: {report.ward} {report.zone ? `(${report.zone})` : ''}
                  </Text>
                )}
              </View>
            </View>
          </View>

          {/* AI Inspection & Authenticity */}
          {(report.classification_confidence !== undefined || report.photos?.[0]?.is_authentic !== undefined) && (
            <View style={{ backgroundColor: `${tokens.primary.DEFAULT}08`, borderRadius: 12, padding: 16, marginBottom: 16, borderWidth: 1, borderColor: `${tokens.primary.DEFAULT}20` }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                <Ionicons name="shield-checkmark" size={18} color={tokens.primary.DEFAULT} />
                <Text style={{ fontSize: 13, fontWeight: '700', color: tokens.primary.DEFAULT }}>
                  AI Verification & Media Integrity
                </Text>
              </View>
              {report.classification_confidence && (
                <Text style={{ fontSize: 12, color: tokens.text.secondary, marginBottom: 2 }}>
                  Categorization Confidence: {(report.classification_confidence * 100).toFixed(0)}%
                </Text>
              )}
              {report.photos?.[0]?.is_authentic !== undefined && (
                <Text style={{ fontSize: 12, color: tokens.text.secondary }}>
                  Image Authenticity: {report.photos[0].is_authentic ? 'Authentic (No AI Deepfake Detected)' : 'Pending Review'}
                </Text>
              )}
            </View>
          )}

          {/* ── Multi-Agent AI Pipeline Audit Trail ───────────────────── */}
          {((report.agent_executions && report.agent_executions.length > 0) ||
            (report.agentExecutions && report.agentExecutions.length > 0)) && (
            <View style={{
              backgroundColor: tokens.surface.card,
              borderRadius: 16,
              padding: 16,
              marginBottom: 16,
              borderWidth: 1,
              borderColor: tokens.surface.border,
            }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                  <View style={{
                    width: 28,
                    height: 28,
                    borderRadius: 14,
                    backgroundColor: `${tokens.primary.DEFAULT}15`,
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    <Ionicons name="hardware-chip-outline" size={16} color={tokens.primary.DEFAULT} />
                  </View>
                  <Text style={{ fontSize: 14, fontWeight: '800', color: tokens.text.primary }}>
                    AI Multi-Agent Audit Trail
                  </Text>
                </View>
                <View style={{
                  backgroundColor: `${tokens.success.DEFAULT}18`,
                  paddingHorizontal: 8,
                  paddingVertical: 3,
                  borderRadius: 6,
                }}>
                  <Text style={{ fontSize: 10, fontWeight: '800', color: tokens.success.DEFAULT, textTransform: 'uppercase' }}>
                    Automated Audit
                  </Text>
                </View>
              </View>

              {(report.agent_executions || report.agentExecutions || []).map((exec: any, idx: number) => {
                const name = exec.agent_name || exec.agentName || 'Agent';
                const status = (exec.status || 'completed').toLowerCase();
                const isSuccess = status === 'completed';
                const confidence = exec.confidence != null ? `${(exec.confidence * 100).toFixed(0)}%` : null;
                const ms = exec.execution_ms ? `${exec.execution_ms}ms` : null;
                const model = exec.model_used || exec.modelUsed;

                const iconName: any =
                  name.toLowerCase().includes('forensic') ? 'scan-outline'
                  : name.toLowerCase().includes('classif') ? 'pricetag-outline'
                  : name.toLowerCase().includes('moderat') ? 'shield-checkmark-outline'
                  : name.toLowerCase().includes('enhanc') ? 'sparkles-outline'
                  : name.toLowerCase().includes('rout') ? 'navigate-outline'
                  : 'notifications-outline';

                return (
                  <View
                    key={exec.id || idx}
                    style={{
                      backgroundColor: tokens.surface.bg,
                      borderRadius: 12,
                      padding: 12,
                      marginBottom: idx === (report.agent_executions || report.agentExecutions).length - 1 ? 0 : 10,
                      borderWidth: 1,
                      borderColor: tokens.surface.border,
                    }}
                  >
                    <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
                      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, flex: 1 }}>
                        <Ionicons name={iconName} size={18} color={tokens.primary.DEFAULT} />
                        <Text style={{ fontSize: 13, fontWeight: '700', color: tokens.text.primary }}>
                          {name.replace(/_/g, ' ').toUpperCase()}
                        </Text>
                      </View>
                      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                        {confidence && (
                          <View style={{ backgroundColor: `${tokens.primary.DEFAULT}12`, paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 }}>
                            <Text style={{ fontSize: 10, fontWeight: '700', color: tokens.primary.DEFAULT }}>
                              {confidence}
                            </Text>
                          </View>
                        )}
                        <Ionicons
                          name={isSuccess ? 'checkmark-circle' : 'alert-circle'}
                          size={16}
                          color={isSuccess ? tokens.success.DEFAULT : tokens.accent.DEFAULT}
                        />
                      </View>
                    </View>

                    {(model || ms) && (
                      <Text style={{ fontSize: 11, color: tokens.text.disabled, marginTop: 4 }}>
                        {[model, ms].filter(Boolean).join(' • ')}
                      </Text>
                    )}

                    {exec.output_snapshot && typeof exec.output_snapshot === 'object' && (
                      <View style={{ marginTop: 6, paddingTop: 6, borderTopWidth: 1, borderTopColor: tokens.surface.border }}>
                        <Text style={{ fontSize: 11, color: tokens.text.secondary, lineHeight: 16 }}>
                          {exec.output_snapshot.reasoning ||
                           exec.output_snapshot.summary ||
                           exec.output_snapshot.details ||
                           (exec.output_snapshot.category ? `Categorized as: ${exec.output_snapshot.category}` : null) ||
                           JSON.stringify(exec.output_snapshot).slice(0, 120)}
                        </Text>
                      </View>
                    )}
                  </View>
                );
              })}
            </View>
          )}

          {/* Status Timeline */}
          <View style={{ backgroundColor: tokens.surface.card, borderRadius: 12, padding: 16, marginBottom: 20, borderWidth: 1, borderColor: tokens.surface.border }}>
            <Text style={{ fontSize: 12, fontWeight: '700', color: tokens.text.disabled, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 12 }}>
              Status Timeline
            </Text>

            {['submitted', 'verified', 'assigned', 'in_progress', 'resolved'].map((step, index) => {
              const stepActive =
                statusStr === step ||
                (statusStr === 'resolved' && true) ||
                (statusStr === 'in_progress' && ['submitted', 'verified', 'assigned', 'in_progress'].includes(step)) ||
                (statusStr === 'assigned' && ['submitted', 'verified', 'assigned'].includes(step)) ||
                (statusStr === 'open' || statusStr === 'pending' ? step === 'submitted' : false);

              return (
                <View key={step} style={{ flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: index === 4 ? 0 : 12 }}>
                  <View style={{
                    width: 20,
                    height: 20,
                    borderRadius: 10,
                    backgroundColor: stepActive ? tokens.primary.DEFAULT : tokens.surface.border,
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    {stepActive && <Ionicons name="checkmark" size={12} color="#fff" />}
                  </View>
                  <Text style={{
                    fontSize: 13,
                    fontWeight: stepActive ? '700' : '500',
                    color: stepActive ? tokens.text.primary : tokens.text.disabled,
                    textTransform: 'capitalize',
                  }}>
                    {step.replace('_', ' ')}
                  </Text>
                </View>
              );
            })}
          </View>

          {/* Upvote & Action Bar */}
          <TouchableOpacity
            onPress={handleUpvote}
            activeOpacity={0.8}
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              backgroundColor: upvoted ? '#fee2e2' : tokens.surface.card,
              borderWidth: 1,
              borderColor: upvoted ? '#ef4444' : tokens.surface.border,
              paddingVertical: 14,
              borderRadius: 12,
              marginBottom: 40,
            }}
          >
            <Ionicons name={upvoted ? "heart" : "heart-outline"} size={20} color={upvoted ? "#ef4444" : tokens.text.secondary} />
            <Text style={{ fontSize: 14, fontWeight: '700', color: upvoted ? '#ef4444' : tokens.text.primary }}>
              {upvoted ? 'Upvoted' : 'Upvote Report'} ({upvoteCount})
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
}
