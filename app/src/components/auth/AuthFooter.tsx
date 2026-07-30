import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';

interface AuthFooterProps {
  text: string;
  linkText: string;
  onPressLink: () => void;
}

export function AuthFooter({ text, linkText, onPressLink }: AuthFooterProps) {
  return (
    <View style={styles.footerContainer}>
      <Text style={styles.footerText}>{text} </Text>
      <TouchableOpacity onPress={onPressLink} activeOpacity={0.7}>
        <Text style={styles.footerLink}>{linkText}</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  footerContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 32,
  },
  footerText: {
    fontSize: 14,
    color: '#64748B',
  },
  footerLink: {
    fontSize: 14,
    fontWeight: '600',
    color: '#059669',
  },
});
