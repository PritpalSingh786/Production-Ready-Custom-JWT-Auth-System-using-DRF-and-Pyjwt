import { createSlice } from '@reduxjs/toolkit';

// Load only access token from localStorage
const loadFromLocalStorage = () => {
  try {
    const accessToken = localStorage.getItem('access_token');
    const user = localStorage.getItem('user');
    const platform = localStorage.getItem('platform');
    
    if (accessToken && user) {
      return {
        user: JSON.parse(user),
        accessToken: accessToken,
        refreshToken: null, // Refresh token NOT stored - it's in HTTP-only cookie
        platform: platform || 'web',
        isAuthenticated: true,
        isLoading: false,
        error: null,
        successMessage: null,
        deviceId: localStorage.getItem('deviceId'),
        webSocket: null,
      };
    }
  } catch (error) {
    console.error('Error loading from localStorage:', error);
  }
  
  return {
    user: null,
    accessToken: null,
    refreshToken: null,
    platform: 'web',
    isAuthenticated: false,
    isLoading: false,
    error: null,
    successMessage: null,
    deviceId: null,
    webSocket: null,
  };
};

const initialState = loadFromLocalStorage();

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setLoading: (state, action) => {
      state.isLoading = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
      state.successMessage = null;
    },
    setSuccess: (state, action) => {
      state.successMessage = action.payload;
      state.error = null;
    },
    clearMessages: (state) => {
      state.error = null;
      state.successMessage = null;
    },
    registerSuccess: (state, action) => {
      state.successMessage = action.payload.message;
      state.isLoading = false;
      state.error = null;
    },
    loginSuccess: (state, action) => {
      const { access, user } = action.payload;
      state.user = user;
      state.accessToken = access;
      state.refreshToken = null; // Never store refresh token
      state.isAuthenticated = true;
      state.isLoading = false;
      state.error = null;
      
      // Store ONLY access token in localStorage
      localStorage.setItem('access_token', access);
      localStorage.setItem('user', JSON.stringify(user));
      localStorage.setItem('platform', state.platform);
      if (state.deviceId) {
        localStorage.setItem('deviceId', state.deviceId);
      }
    },
    logoutSuccess: (state) => {
      state.user = null;
      state.accessToken = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      state.isLoading = false;
      state.deviceId = null;
      state.webSocket = null;
      
      // Clear localStorage (only access token and user data)
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      localStorage.removeItem('platform');
      localStorage.removeItem('deviceId');
    },
    setDeviceId: (state, action) => {
      state.deviceId = action.payload;
      if (state.isAuthenticated) {
        localStorage.setItem('deviceId', action.payload);
      }
    },
    setWebSocket: (state, action) => {
      state.webSocket = action.payload;
    },
    forgotPasswordSuccess: (state, action) => {
      state.successMessage = action.payload.message;
      state.isLoading = false;
    },
    passwordChangeSuccess: (state, action) => {
      state.successMessage = action.payload.message;
      state.isLoading = false;
    },
    updateTokens: (state, action) => {
      // Only update access token, refresh token is handled by backend cookie
      state.accessToken = action.payload.access;
      localStorage.setItem('access_token', action.payload.access);
    },
  },
});

export const {
  setLoading,
  setError,
  setSuccess,
  clearMessages,
  registerSuccess,
  loginSuccess,
  logoutSuccess,
  setDeviceId,
  setWebSocket,
  forgotPasswordSuccess,
  passwordChangeSuccess,
  updateTokens,
} = authSlice.actions;

export default authSlice.reducer;