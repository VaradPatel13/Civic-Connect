/**
 * Status Badge UI component — extracted from FeaturedCard / ReportRow.
 * Renders an inline coloured chip for any report status.
 */
import { View, Text } from 'react-native';
import { tokens } from '@src/constants';
import type { ReportStatus } from '@src/types';

const STATUS_CONFIG: Record<string, { bg: string; text: string; label: string }> = {
  open:         { bg: tokens.accent.light,  text: tokens.accent.DEFAULT,  label: 'Open'       },
  pending:      { bg: tokens.accent.light,  text: tokens.accent.DEFAULT,  label: 'Pending'    },
  in_progress:   { bg: tokens.info.light,    text: tokens.info.DEFAULT,    label: 'In Progress' },
  processing:   { bg: tokens.info.light,    text: tokens.info.DEFAULT,    label: 'Processing' },
  verified:     { bg: tokens.info.light,    text: tokens.info.DEFAULT,    label: 'Verified'   },
  assigned:     { bg: tokens.info.light,    text: tokens.info.DEFAULT,    label: 'Assigned'   },
  resolved:     { bg: tokens.success.light, text: tokens.success.DEFAULT, label: 'Resolved'   },
  rejected:     { bg: tokens.error.light,   text: tokens.error.DEFAULT,   label: 'Rejected'   },
  duplicate:    { bg: tokens.error.light,   text: tokens.error.DEFAULT,   label: 'Duplicate'  },
  cancelled:   { bg: tokens.error.light,   text: tokens.error.DEFAULT,   label: 'Cancelled'  },
  critical:    { bg: tokens.error.light,   text: tokens.error.DEFAULT,   label: 'Critical'   },
};

export interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

export function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status.toLowerCase()] ?? {
    bg: tokens.surface.border, text: tokens.text.disabled, label: status,
  };

  return (
    <View style={{
      backgroundColor: config.bg,
      borderRadius:    size === 'sm' ? 4 : 6,
      paddingHorizontal: size === 'sm' ? 5 : 7,
      paddingVertical:  size === 'sm' ? 1 : 2,
      alignSelf:        'flex-start',
    }}>
      <Text style={{
        fontSize:         size === 'sm' ? 8  : 10,
        fontWeight:       '800',
        color:            config.text,
        textTransform:    'uppercase',
        letterSpacing:    0.3,
      }}>
        {config.label}
      </Text>
    </View>
  );
}