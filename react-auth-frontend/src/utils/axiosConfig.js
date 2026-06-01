import axios from 'axios';
import { store } from '../app/store';
import { logoutSuccess, updateTokens } from '../features/auth/authSlice';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/users';

const axiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important: Send cookies (refresh token) with requests
});

axiosInstance.interceptors.request.use(
  (config) => {
    const state = store.getState();
    const accessToken = state.auth.accessToken;
    
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const state = store.getState();
    const platform = state.auth.platform;

    // If unauthorized, try to refresh using HTTP-only cookie
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Refresh token is automatically sent via cookie because withCredentials: true
        const response = await axios.post(`${API_URL}/token/refresh/`, {
          platform: platform,
        }, {
          withCredentials: true,
        });

        const { access } = response.data;
        
        // Update only access token in Redux and localStorage
        store.dispatch(updateTokens({ access }));
        
        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return axiosInstance(originalRequest);
        
      } catch (refreshError) {
        // Refresh failed, logout user
        store.dispatch(logoutSuccess());
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;