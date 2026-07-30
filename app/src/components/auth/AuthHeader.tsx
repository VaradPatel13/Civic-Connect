import { Image, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface AuthHeaderProps {
  title: string;
  subtitle: string;
  showLogoBadge?: boolean;
  iconName?: keyof typeof Ionicons.glyphMap;
}

export function AuthHeader({
  title,
  subtitle,
  showLogoBadge = true,
  iconName,
}: AuthHeaderProps) {
  return (
    <View style={styles.root}>
      {showLogoBadge ? (
        <View style={styles.brandRow}>
          <View style={styles.logoBadge}>
            {iconName ? (
              <Ionicons name={iconName} size={20} color="#059669" />
            ) : (
              <Image
                source={require('../../../assets/images/civic_logo.png')}
                style={{ width: 28, height: 28, borderRadius: 6 }}
                resizeMode="contain"
              />
            )}
          </View>
          <Text style={styles.brandName}>CivicConnect</Text>
        </View>
      ) : null}

      <Text style={styles.title}>{title}</Text>
      <Text style={styles.subtitle}>{subtitle}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    marginBottom: 28,
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    gap: 10,
  },
  logoBadge: {
    width: 36,
    height: 36,
    borderRadius: 8,
    backgroundColor: '#ECFDF5',
    borderWidth: 1,
    borderColor: '#A7F3D0',
    alignItems: 'center',
    justifyContent: 'center',
  },
  brandName: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0F172A',
    letterSpacing: -0.3,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#0F172A',
    letterSpacing: -0.4,
    marginBottom: 6,
  },
  subtitle: {
    fontSize: 14,
    color: '#475569',
    lineHeight: 20,
  },
});
