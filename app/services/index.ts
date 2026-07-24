import axios from 'axios';
import { CitizenUser, ReportItem, NotificationItem, RewardsSummary, DepartmentItem } from '../types/domain';
import { useAuthStore } from '../stores/authStore';

export const API_BASE_URL = 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = useAuthStore.getState().refreshToken;
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const { access_token } = res.data;
          useAuthStore.getState().setAccessToken(access_token);
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return axios(originalRequest);
        } catch {
          useAuthStore.getState().logout();
        }
      } else {
        useAuthStore.getState().logout();
      }
    }
    return Promise.reject(error);
  }
);

export const authService = {
  async register(data: {
    display_name: string;
    phone: string;
    password: string;
    email?: string;
    preferred_language?: string;
  }) {
    const res = await apiClient.post('/auth/register', data);
    return res.data;
  },

  async login(data: { phone: string; password: string }) {
    const res = await apiClient.post('/auth/login', data);
    return res.data;
  },

  async getMe(): Promise<CitizenUser> {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },

  async logout() {
    const res = await apiClient.post('/auth/logout');
    return res.data;
  },
};

export const reportService = {
  async listReports(params?: { category?: string; status?: string }): Promise<ReportItem[]> {
    const res = await apiClient.get('/reports/', { params });
    return res.data;
  },

  async getReport(id: string): Promise<ReportItem> {
    const res = await apiClient.get(`/reports/${id}`);
    return res.data;
  },

  async createReport(data: {
    title: string;
    description: string;
    issue_category: string;
    urgency?: string;
    latitude?: number;
    longitude?: number;
    address?: string;
    photos?: string[];
  }): Promise<ReportItem> {
    const res = await apiClient.post('/reports/', data);
    return res.data;
  },
};

export const departmentService = {
  async listDepartments(): Promise<DepartmentItem[]> {
    const res = await apiClient.get('/departments/');
    return res.data;
  },
};

export const notificationService = {
  async listNotifications(): Promise<NotificationItem[]> {
    const res = await apiClient.get('/notifications/');
    return res.data;
  },
};

export const rewardService = {
  async getSummary(): Promise<RewardsSummary> {
    const res = await apiClient.get('/rewards/summary');
    return res.data;
  },
};
