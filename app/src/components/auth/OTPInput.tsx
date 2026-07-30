import { useRef, useState } from 'react';
import {
  NativeSyntheticEvent,
  StyleSheet,
  TextInput,
  TextInputKeyPressEventData,
  View,
} from 'react-native';

interface OTPInputProps {
  length?: number;
  value: string;
  onChange: (code: string) => void;
  onComplete?: (code: string) => void;
}

export function OTPInput({
  length = 6,
  value,
  onChange,
  onComplete,
}: OTPInputProps) {
  const inputsRef = useRef<(TextInput | null)[]>([]);
  const [focusedIndex, setFocusedIndex] = useState<number>(0);

  const digits = Array.from({ length }, (_, i) => value[i] || '');

  function handleChangeText(text: string, index: number) {
    const cleanText = text.replace(/\D/g, '');

    // Handle full paste
    if (cleanText.length > 1) {
      const pastedCode = cleanText.slice(0, length);
      onChange(pastedCode);
      if (pastedCode.length === length) {
        inputsRef.current[length - 1]?.blur();
        if (onComplete) onComplete(pastedCode);
      }
      return;
    }

    const newDigits = [...digits];
    newDigits[index] = cleanText;
    const newCode = newDigits.join('');

    onChange(newCode);

    if (cleanText && index < length - 1) {
      inputsRef.current[index + 1]?.focus();
    }

    if (newCode.length === length && onComplete) {
      onComplete(newCode);
    }
  }

  function handleKeyPress(e: NativeSyntheticEvent<TextInputKeyPressEventData>, index: number) {
    if (e.nativeEvent.key === 'Backspace') {
      if (!digits[index] && index > 0) {
        const newDigits = [...digits];
        newDigits[index - 1] = '';
        onChange(newDigits.join(''));
        inputsRef.current[index - 1]?.focus();
      }
    }
  }

  return (
    <View style={styles.container}>
      {Array.from({ length }).map((_, index) => {
        const isFocused = focusedIndex === index;
        const hasValue = Boolean(digits[index]);

        return (
          <TextInput
            key={index}
            ref={(ref) => { inputsRef.current[index] = ref; }}
            style={[
              styles.digitBox,
              isFocused && styles.digitBoxFocused,
              hasValue && styles.digitBoxFilled,
            ]}
            keyboardType="number-pad"
            maxLength={index === 0 ? length : 1}
            value={digits[index]}
            onChangeText={(text) => handleChangeText(text, index)}
            onKeyPress={(e) => handleKeyPress(e, index)}
            onFocus={() => setFocusedIndex(index)}
            onBlur={() => setFocusedIndex(-1)}
            autoFocus={index === 0}
            selectTextOnFocus
            accessibilityLabel={`OTP digit ${index + 1} of ${length}`}
          />
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 8,
    width: '100%',
    marginVertical: 12,
  },
  digitBox: {
    flex: 1,
    height: 52,
    maxWidth: 52,
    backgroundColor: '#FAFAFA',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 8,
    textAlign: 'center',
    fontSize: 20,
    fontWeight: '700',
    color: '#0F172A',
  },
  digitBoxFocused: {
    borderColor: '#059669',
    backgroundColor: '#FFFFFF',
  },
  digitBoxFilled: {
    borderColor: '#94A3B8',
  },
});
