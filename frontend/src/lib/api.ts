import axios from 'axios';

// Определяем API URL в зависимости от окружения
const getApiBaseUrl = () => {
  // В production используем текущий домен
  if (import.meta.env.PROD) {
    // Если мы на том же домене, что и API
    const protocol = window.location.protocol;
    const host = window.location.host;
    return `${protocol}//${host}/api`;
  }
  // В development используем переменную окружения или localhost
  return import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
};

const API_BASE_URL = getApiBaseUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor для добавления токена
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor для обновления токена при 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          });
          
          const { access } = response.data;
          localStorage.setItem('access_token', access);
          
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: async (data: { first_name: string; email: string; password: string }) => {
    const response = await api.post('/auth/register/', data);
    return response.data;
  },
  
  login: async (data: { email: string; password: string }) => {
    const response = await api.post('/auth/login/', data);
    return response.data;
  },
  
  logout: async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      await api.post('/auth/logout/', { refresh: refreshToken });
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
};

// Profile API
export const profileAPI = {
  get: async () => {
    const response = await api.get('/profile/');
    return response.data;
  },
  
  update: async (data: { first_name?: string; email?: string }) => {
    const response = await api.patch('/profile/', data);
    return response.data;
  },
  
  changePassword: async (data: { old_password: string; new_password: string }) => {
    const response = await api.post('/profile/change-password/', data);
    return response.data;
  },
};

// Days API
export const daysAPI = {
  get: async (date: string) => {
    const response = await api.get(`/days/${date}/`);
    return response.data;
  },
};

// Goals API
export const goalsAPI = {
  get: async (date: string) => {
    try {
      const response = await api.get(`/goals/${date}/`);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },
  
  create: async (date: string, data: {
    calories: number;
    proteins: number;
    fats: number;
    carbohydrates: number;
  }) => {
    const response = await api.post(`/goals/${date}/`, data);
    return response.data;
  },
  
  calculate: async (date: string, data: {
    age: number;
    gender: 'male' | 'female';
    weight: number;
    height: number;
    activity_level: 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active';
  }) => {
    const response = await api.post('/goals/auto-calculate/', {
      ...data,
      date: date,
    });
    return response.data;
  },
};

// Dishes API
export const dishesAPI = {
  get: async (date?: string) => {
    const params = date ? { date } : {};
    const response = await api.get('/dishes/', { params });
    return response.data;
  },
  
  getById: async (id: number) => {
    const response = await api.get(`/dishes/${id}/`);
    return response.data;
  },
  
  create: async (data: {
    name: string;
    date: string;
    meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
    weight?: number;
    calories?: number;
    proteins?: number;
    fats?: number;
    carbohydrates?: number;
  }) => {
    const response = await api.post('/dishes/', data);
    return response.data;
  },
  
  update: async (id: number, data: Partial<{
    name: string;
    weight: number;
    calories: number;
    proteins: number;
    fats: number;
    carbohydrates: number;
    meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
    date: string;
  }>) => {
    const response = await api.patch(`/dishes/${id}/`, data);
    return response.data;
  },
  
  delete: async (id: number) => {
    await api.delete(`/dishes/${id}/`);
  },
  
  recognize: async (data: {
    image_base64: string;
    date?: string;
    meal_type?: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  }) => {
    const response = await api.post('/dishes/recognize/', data);
    return response.data;
  },
  
  searchNutrition: async (foodName: string, weight: number = 100) => {
    const response = await api.post('/dishes/search-nutrition/', {
      food_name: foodName,
      weight: weight,
    });
    return response.data;
  },
};

// Subscription API
export const subscriptionAPI = {
  get: async () => {
    const response = await api.get('/subscription/');
    return response.data;
  },
  
  payMonthly: async (planId?: number) => {
    const response = await api.post('/subscription/pay-monthly/', { plan_id: planId });
    return response.data;
  },
  
  payYearly: async (planId?: number) => {
    const response = await api.post('/subscription/pay-yearly/', { plan_id: planId });
    return response.data;
  },
  
  disableAutoRenew: async () => {
    const response = await api.post('/subscription/disable-auto-renew/');
    return response.data;
  },
  
  enableAutoRenew: async () => {
    const response = await api.post('/subscription/enable-auto-renew/');
    return response.data;
  },
  
  getPayments: async () => {
    const response = await api.get('/subscription/payments/');
    return response.data;
  },
};

export default api;

