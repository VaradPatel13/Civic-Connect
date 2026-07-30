/**
 * Secure Storage Utility for CivicConnect Mobile.
 * Uses `expo-secure-store` on native iOS/Android (hardware encrypted)
 * and falls back to window.localStorage on Web environments.
 */
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const ACCESS_TOKEN_KEY = 'civic_connect_access_token';
const REFRESH_TOKEN_KEY = 'civic_connect_refresh_token';

const isWeb = Platform.OS === 'web';

export const storage = {
  async setAccessToken(token: string): Promise<void> {
    try {
      if (isWeb) {
        if (typeof window !== 'undefined' && window.localStorage) {
          if (token) window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
          else window.localStorage.removeItem(ACCESS_TOKEN_KEY);
        }
      } else {
        if (token) {
          await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, token);
        } else {
          await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY);
        }
      }
    } catch (e) {
      console.warn('[Storage] Error setting access token:', e);
    }
  },

  async getAccessToken(): Promise<string | null> {
    try {
      if (isWeb) {
        if (typeof window !== 'undefined' && window.localStorage) {
          return window.localStorage.getItem(ACCESS_TOKEN_KEY);
        }
        return null;
      }
      return await SecureStore.getItemAsync(ACCESS_TOKEN_KEY);
    } catch (e) {
      console.warn('[Storage] Error getting access token:', e);
      return null;
    }
  },

  async setRefreshToken(token: string): Promise<void> {
    try {
      if (isWeb) {
        if (typeof window !== 'undefined' && window.localStorage) {
          if (token) window.localStorage.setItem(REFRESH_TOKEN_KEY, token);
          else window.localStorage.removeItem(REFRESH_TOKEN_KEY);
        }
      } else {
        if (token) {
          await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, token);
        } else {
          await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
        }
      }
    } catch (e) {
      console.warn('[Storage] Error setting refresh token:', e);
    }
  },

  async getRefreshToken(): Promise<string | null> {
    try {
      if (isWeb) {
        if (typeof window !== 'undefined' && window.localStorage) {
          return window.localStorage.getItem(REFRESH_TOKEN_KEY);
        }
        return null;
      }
      return await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
    } catch (e) {
      console.warn('[Storage] Error getting refresh token:', e);
      return null;
    }
  },

  async clearAllTokens(): Promise<void> {
    await this.setAccessToken('');
    await this.setRefreshToken('');
  },
};
