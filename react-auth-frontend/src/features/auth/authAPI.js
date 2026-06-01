import axiosInstance from '../../utils/axiosConfig';

export const authAPI = {
  register: async (userData) => {
    const response = await axiosInstance.post('/register/', userData);
    return response.data;
  },

  login: async (credentials) => {
    const response = await axiosInstance.post('/login/', credentials);
    return response.data;
  },

  logout: async (platform) => {
    // Refresh token is automatically sent via cookie
    const response = await axiosInstance.post('/logout/', { platform });
    return response.data;
  },

  getAuthenticatedUser: async () => {
    const response = await axiosInstance.get('/authenticated/');
    return response.data;
  },

  forgotPassword: async (userId) => {
    const response = await axiosInstance.post('/forgot-password/', { userId });
    return response.data;
  },
};