import { ReactNode } from 'react';
import {
  Keyboard,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  TouchableWithoutFeedback,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

interface AuthScreenProps {
  children: ReactNode;
  showBackHeader?: boolean;
  headerTitle?: string;
}

export function AuthScreen({ children, showBackHeader = false, headerTitle }: AuthScreenProps) {
  const router = useRouter();
  const insets = useSafeAreaInsets();

  return (
    <TouchableWithoutFeedback onPress={Keyboard.dismiss} accessible={false}>
      <KeyboardAvoidingView
        style={styles.root}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        {showBackHeader ? (
          <View style={[styles.header, { paddingTop: Math.max(insets.top + 8, 44) }]}>
            <TouchableOpacity
              style={styles.backBtn}
              onPress={() => router.back()}
              accessibilityLabel="Go back"
            >
              <Ionicons name="arrow-back" size={20} color="#0F172A" />
            </TouchableOpacity>
            {headerTitle ? <Text style={styles.headerTitle}>{headerTitle}</Text> : <View style={{ flex: 1 }} />}
            <View style={{ width: 36 }} />
          </View>
        ) : null}

        <ScrollView
          style={styles.scroll}
          contentContainerStyle={[
            styles.container,
            {
              paddingTop: showBackHeader ? 24 : Math.max(insets.top + 24, 48),
              paddingBottom: Math.max(insets.bottom + 24, 32),
            },
          ]}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {children}
        </ScrollView>
      </KeyboardAvoidingView>
    </TouchableWithoutFeedback>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
    backgroundColor: '#FFFFFF',
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 8,
    backgroundColor: '#F8FAFC',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  headerTitle: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600',
    color: '#0F172A',
    textAlign: 'center',
  },
  scroll: {
    flex: 1,
  },
  container: {
    paddingHorizontal: 24,
    maxWidth: 440,
    width: '100%',
    alignSelf: 'center',
  },
});
