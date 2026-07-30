/**
 * Auth Zustand Store — CivicConnect Mobile
 * Manages user session, JWT token state, and auth API calls.
 */
import { create } from 'zustand';
import { api, setAuthToken, getAuthToken, ApiError } from '@src/lib/api';
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
  error: string | null;

  login: (payload: LoginPayload) => Promise<TokenResponse>;
  register: (payload: RegisterPayload) => Promise<TokenResponse>;
  verifyOTP: (payload: OTPVerifyPayload) => Promise<TokenResponse>;
  fetchCurrentUser: () => Promise<CitizenProfile | null>;
  logout: () => Promise<void>;
  clearError: () => void;
}

const initialToken = getAuthToken() || null;

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: initialToken,
  isAuthenticated: Boolean(initialToken),
  isLoading: false,
  error: null,

  clearError: () => set({ error: null }),

  login: async (payload: LoginPayload) => {
    set({ isLoading: true, error: null });
    try {
      const res = await api.post<TokenResponse>('/api/v1/auth/login', payload);
      setAuthToken(res.access_token);
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
      setAuthToken(res.access_token);
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
        setAuthToken(res.access_token);
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
    if (!get().token) return null;
    try {
      const user = await api.get<CitizenProfile>('/api/v1/auth/me');
      set({ user, isAuthenticated: true });
      return user;
    } catch (err) {
      // Only clear auth on 401 Unauthorized — NOT on 500s or network errors.
      // A server-side crash should not log the user out.
      if (err instanceof ApiError && err.status === 401) {
        set({ user: null, token: null, isAuthenticated: false });
        setAuthToken('');
      }
      return null;
    }
  },

  logout: async () => {
    try {
      if (get().token) {
        await api.post('/api/v1/auth/logout', {});
      }
    } catch {
      // Ignore logout errors
    } finally {
      setAuthToken('');
      set({ user: null, token: null, isAuthenticated: false, error: null });
    }
  },
}));
