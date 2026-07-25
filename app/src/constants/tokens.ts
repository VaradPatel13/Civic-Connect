// ─── CivicConnect Color Tokens ───────────────────────────────────────────────
// All UI components reference these tokens. Never hardcode hex values in components.
// Palette rationale:
/*
  PRIMARY: Deep emerald green (#065f46) — civic authority, progress, civic pride.
    Used for: headers, primary CTAs, active states, the pulse bar.
  ACCENT / URGENCY: Amber (#d97706) — open reports, warnings, pending actions.
    Used for: "Open" status, CTA banners (tinted bg), urgency warnings.
  SUCCESS: Emerald (#059669) — resolved, positive, official trust.
    Used for: "Resolved" status, success messages, confirmed actions.
  LIGHT TINTS: For colored backgrounds and chips — suffixed with _light.
*/

export const tokens = {
  // Brand Primary
  primary: {
    DEFAULT:  '#065f46',  // deep green: headers, nav, primary buttons
    light:    '#0d9488',  // teal: interactive links, active tab icons
    xlight:  '#ccfbf1',  // mint: tinted backgrounds, chips on dark
    onPrimary:'#ffffff',  // white text on dark green backgrounds
  },

  // Amber / Urgency
  accent: {
    DEFAULT:  '#d97706',  // amber: open/warning
    light:    '#fef3c7',  // tinted bg for amber chips
    onAccent: '#ffffff',
  },

  // Semantic
  success: {
    DEFAULT: '#059669',  // emerald: resolved
    light:   '#d1fae5',  // tinted
  },
  error: {
    DEFAULT: '#dc2626',
    light:   '#fee2e2',
  },
  info: {
    DEFAULT: '#2563eb',
    light:   '#dbeafe',
  },

  // Text
  text: {
    primary:   '#111827',  // headings, main body
    secondary: '#6b7280',  // labels, captions
    disabled:  '#9ca3af',  // placeholders, inactive
    onPrimary: '#ffffff',  // text on primary-colored surfaces
    xlight:    '#6ee7b7',  // text on very dark backgrounds (subtle)
  },

  // Surfaces
  surface: {
    bg:     '#f9fafb',  // page background
    card:   '#ffffff',  // card/list item
    border: '#e5e7eb',  // dividers, outlines
  },
} as const;