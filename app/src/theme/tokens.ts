/**
 * CivicConnect Design Token System
 * Production Design System featuring bespoke color palettes, spacing tokens,
 * typography hierarchy, and elevation values for Dark & Light modes.
 */
export const TOKENS = {
  colors: {
    dark: {
      bg: '#090A0F',
      surface: '#12141F',
      surfaceHover: '#1B1E2E',
      surfaceElevated: '#222638',
      border: 'rgba(255, 255, 255, 0.08)',
      borderStrong: 'rgba(255, 255, 255, 0.16)',
      textPrimary: '#F8FAFC',
      textSecondary: '#94A3B8',
      textMuted: '#64748B',
      accentPrimary: '#10B981', // Vibrant Emerald Mint
      accentCyan: '#06B6D4',    // Bright Cyan
      accentLime: '#84CC16',    // Fresh Lime
      accentRose: '#F43F5E',    // Vivid Rose
      accentAmber: '#F59E0B',   // Warm Amber
      pillBg: '#1A1D2D',
      heroGradientBg: '#1A132B',
      inputBg: '#151724',
    },
    light: {
      bg: '#F8FAFC',
      surface: '#FFFFFF',
      surfaceHover: '#F1F5F9',
      surfaceElevated: '#E2E8F0',
      border: 'rgba(0, 0, 0, 0.08)',
      borderStrong: 'rgba(0, 0, 0, 0.16)',
      textPrimary: '#0F172A',
      textSecondary: '#475569',
      textMuted: '#94A3B8',
      accentPrimary: '#059669', // Emerald Civic Green
      accentCyan: '#0891B2',
      accentLime: '#65A30D',
      accentRose: '#E11D48',
      accentAmber: '#D97706',
      pillBg: '#F1F5F9',
      heroGradientBg: '#ECFDF5',
      inputBg: '#F1F5F9',
    },
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 12,
    lg: 16,
    xl: 20,
    xxl: 24,
    huge: 32,
  },
  radius: {
    sm: 8,
    md: 12,
    lg: 16,
    xl: 20,
    full: 9999,
  },
  typography: {
    h1: { fontSize: 28, fontWeight: '800' as const, letterSpacing: -0.8 },
    h2: { fontSize: 22, fontWeight: '800' as const, letterSpacing: -0.5 },
    h3: { fontSize: 18, fontWeight: '800' as const, letterSpacing: -0.3 },
    subtitle: { fontSize: 14, fontWeight: '600' as const },
    body: { fontSize: 14, fontWeight: '400' as const, lineHeight: 20 },
    caption: { fontSize: 12, fontWeight: '500' as const },
    badge: { fontSize: 10, fontWeight: '800' as const, letterSpacing: 0.5 },
  },
};
