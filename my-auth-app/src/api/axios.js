// api/axios.js
import axios from 'axios';
import { store } from '../app/store';
import { setToken, logout } from '../features/auth/authSlice';

const API = axios.create({
    baseURL: 'http://127.0.0.1:8000/api/users/',
    withCredentials: true,
});

API.interceptors.request.use((config) => {
    const token = store.getState().auth.access;
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

API.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        if (error.response?.status === 401 && !originalRequest._retry &&
            !originalRequest.url.includes("token/refresh")) {
            originalRequest._retry = true;
            try {
                // ✅ Fixed: removed trailing slash issue
                const res = await axios.post(
                    'http://127.0.0.1:8000/api/users/token/refresh/', 
                    { platform: 'web' }, 
                    { withCredentials: true }
                );
                if (res.data.access) {
                    store.dispatch(setToken(res.data.access));
                    originalRequest.headers.Authorization = `Bearer ${res.data.access}`;
                    return API(originalRequest);
                }
            } catch (err) {
                store.dispatch(logout());
                return Promise.reject(err);
            }
        }
        return Promise.reject(error);
    }
);

export default API;