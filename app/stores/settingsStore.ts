import { create } from 'zustand';

interface SettingsState {
  language: 'en' | 'hi' | 'mr';
  theme: 'dark' | 'light' | 'system';
  setLanguage: (lang: 'en' | 'hi' | 'mr') => void;
  setTheme: (theme: 'dark' | 'light' | 'system') => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  language: 'en',
  theme: 'dark',
  setLanguage: (language) => set({ language }),
  setTheme: (theme) => set({ theme }),
}));
