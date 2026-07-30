import { ActivityIndicator, StyleSheet, Text, TouchableOpacity } from 'react-native';

interface PrimaryButtonProps {
  title: string;
  onPress: () => void;
  isLoading?: boolean;
  disabled?: boolean;
  accessibilityLabel?: string;
}

export function PrimaryButton({
  title,
  onPress,
  isLoading = false,
  disabled = false,
  accessibilityLabel,
}: PrimaryButtonProps) {
  const isInteractionDisabled = isLoading || disabled;

  return (
    <TouchableOpacity
      style={[styles.button, isInteractionDisabled && styles.buttonDisabled]}
      onPress={onPress}
      disabled={isInteractionDisabled}
      activeOpacity={0.8}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel || title}
    >
      {isLoading ? (
        <ActivityIndicator color="#FFFFFF" size="small" />
      ) : (
        <Text style={styles.text}>{title}</Text>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    height: 48,
    backgroundColor: '#059669',
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 8,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  text: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
    letterSpacing: -0.2,
  },
});
