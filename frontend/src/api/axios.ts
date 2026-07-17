import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const axiosInstance: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor
axiosInstance.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    if (error.code === 'ECONNABORTED') {
      return Promise.reject(new Error('Request timeout. Please try again.'));
    }
    
    if (error.response) {
      const status = error.response.status;
      
      switch (status) {
        case 400:
          return Promise.reject(new Error('Bad request. Please check your input.'));
        case 404:
          return Promise.reject(new Error('Resource not found.'));
        case 500:
          return Promise.reject(new Error('Server error. Please try again later.'));
        case 502:
          return Promise.reject(new Error('Service unavailable. Please try again later.'));
        default:
          return Promise.reject(new Error(`An error occurred: ${status}`));
      }
    }
    
    if (error.request) {
      return Promise.reject(new Error('Network error. Please check your connection.'));
    }
    
    return Promise.reject(new Error('An unexpected error occurred.'));
  }
);

export default axiosInstance;
