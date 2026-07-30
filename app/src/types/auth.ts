/**
 * Authentication domain types for CivicConnect Mobile.
 */

export interface CitizenProfile {
  id: string;
  phone: string;
  display_name: string;
  email?: string | null;
  preferred_language: string;
  role: string;
  is_verified: boolean;
  trust_score?: number;
  points?: number;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: CitizenProfile;
}

export interface LoginPayload {
  phone: string;
  password?: string;
}

export interface RegisterPayload {
  display_name: string;
  phone: string;
  email?: string;
  password?: string;
  preferred_language?: string;
}

export interface OTPVerifyPayload {
  phone: string;
  code: string;
  purpose?: string;
}
