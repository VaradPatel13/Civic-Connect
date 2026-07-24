import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

interface BadgeProps {
  label: string;
  status?: string;
}

export const Badge: React.FC<BadgeProps> = ({ label, status = 'default' }) => {
  const getBadgeColors = () => {
    switch (status.toLowerCase()) {
      case 'resolved':
      case 'success':
        return { bg: '#064e3b', text: '#34d399' };
      case 'in_progress':
      case 'assigned':
        return { bg: '#1e3a8a', text: '#60a5fa' };
      case 'pending':
      case 'triaged':
        return { bg: '#78350f', text: '#fbbf24' };
      case 'rejected':
      case 'high':
      case 'critical':
        return { bg: '#7f1d1d', text: '#f87171' };
      default:
        return { bg: '#334155', text: '#94a3b8' };
    }
  };

  const colors = getBadgeColors();

  return (
    <View style={[styles.badge, { backgroundColor: colors.bg }]}>
      <Text style={[styles.text, { color: colors.text }]}>{label.toUpperCase()}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  text: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
});
