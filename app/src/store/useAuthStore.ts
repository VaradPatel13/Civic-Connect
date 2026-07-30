/**
 * Auth Zustand Store — CivicConnect Mobile
 * Manages user session, JWT token state, secure storage, and auth API calls.
 */
import { create } from 'zustand';
import { api, setAuthToken, getAuthToken, initializeAuthTokens, setOnUnauthorizedListener, ApiError } from '@src/lib/api';
import { storage } from '@src/utils/storage';
import type {
  CitizenProfile,
  TokenResponse,
  LoginPayload,
  RegisterPayload,
  OTPVerifyPayload,
} from '@src/types/auth';

interface AuthState {
  user: CitizenProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitialized: boolean;
  error: string | null;

  initializeAuth: () => Promise<void>;
  login: (payload: LoginPayload) => Promise<TokenResponse>;
  register: (payload: RegisterPayload) => Promise<TokenResponse>;
  verifyOTP: (payload: OTPVerifyPayload) => Promise<TokenResponse>;
  fetchCurrentUser: () => Promise<CitizenProfile | null>;
  logout: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => {
  // Register callback for when api client triggers unauthentication due to refresh failure
  setOnUnauthorizedListener(() => {
    set({ user: null, token: null, isAuthenticated: false, isLoading: false });
  });

  return {
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: false,
    isInitialized: false,
    error: null,

    clearError: () => set({ error: null }),

    initializeAuth: async () => {
      set({ isLoading: true });
      try {
        const storedToken = await initializeAuthTokens();
        const refreshToken = await storage.getRefreshToken();

        if (storedToken || refreshToken) {
          const user = await get().fetchCurrentUser();
          if (user) {
            set({
              user,
              token: getAuthToken(),
              isAuthenticated: true,
              isInitialized: true,
              isLoading: false,
            });
            return;
          }
        }
      } catch (err) {
        console.warn('[AuthStore] Initialization failed:', err);
      }
      set({
        user: null,
        token: null,
        isAuthenticated: false,
        isInitialized: true,
        isLoading: false,
      });
    },

    login: async (payload: LoginPayload) => {
      set({ isLoading: true, error: null });
      try {
        const res = await api.post<TokenResponse>('/api/v1/auth/login', payload);
        setAuthToken(res.access_token, res.refresh_token);
        set({
          user: res.user,
          token: res.access_token,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });
        return res;
      } catch (err) {
        const message =
          err instanceof ApiError && err.body && typeof err.body === 'object' && 'detail' in err.body
            ? (err.body as { detail: string }).detail
            : err instanceof Error
            ? err.message
            : 'Login failed. Please check your credentials.';
        set({ isLoading: false, error: message });
        throw new Error(message);
      }
    },

    register: async (payload: RegisterPayload) => {
      set({ isLoading: true, error: null });
      try {
        const res = await api.post<TokenResponse>('/api/v1/auth/register', payload);
        setAuthToken(res.access_token, res.refresh_token);
        set({
          user: res.user,
          token: res.access_token,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });
        return res;
      } catch (err) {
        const message =
          err instanceof ApiError && err.body && typeof err.body === 'object' && 'detail' in err.body
            ? (err.body as { detail: string }).detail
            : err instanceof Error
            ? err.message
            : 'Registration failed. Please try again.';
        set({ isLoading: false, error: message });
        throw new Error(message);
      }
    },

    verifyOTP: async (payload: OTPVerifyPayload) => {
      set({ isLoading: true, error: null });
      try {
        const res = await api.post<any>('/api/v1/auth/verify-otp', {
          ...payload,
          purpose: payload.purpose ?? 'register',
        });
        if (res && res.access_token) {
          setAuthToken(res.access_token, res.refresh_token);
          set({
            user: res.user,
            token: res.access_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } else {
          set((state) => ({
            user: state.user ? { ...state.user, is_verified: true } : state.user,
            isLoading: false,
            error: null,
          }));
        }
        return res;
      } catch (err) {
        const message =
          err instanceof ApiError && err.body && typeof err.body === 'object' && 'detail' in err.body
            ? (err.body as { detail: string }).detail
            : err instanceof Error
            ? err.message
            : 'OTP verification failed.';
        set({ isLoading: false, error: message });
        throw new Error(message);
      }
    },

    fetchCurrentUser: async () => {
      try {
        const user = await api.get<CitizenProfile>('/api/v1/auth/me');
        set({ user, token: getAuthToken(), isAuthenticated: true });
        return user;
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          await storage.clearAllTokens();
          setAuthToken(null, null);
          set({ user: null, token: null, isAuthenticated: false });
        }
        return null;
      }
    },

    logout: async () => {
      try {
        const refreshToken = await storage.getRefreshToken();
        await api.post('/api/v1/auth/logout', { refresh_token: refreshToken });
      } catch {
        // Ignore network errors during logout
      } finally {
        await storage.clearAllTokens();
        setAuthToken(null, null);
        set({ user: null, token: null, isAuthenticated: false, error: null });
      }
    },
  };
});
