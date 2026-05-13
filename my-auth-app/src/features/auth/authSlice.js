// features/auth/authSlice.js
import { createSlice } from '@reduxjs/toolkit';

const authSlice = createSlice({
    name: 'auth',
    initialState: { 
        access: null, 
        isAuthenticated: false, 
        userEmail: null,
        user: null  // ✅ Added user object
    },
    reducers: {
        setToken: (state, action) => {
            state.access = action.payload;
            state.isAuthenticated = true;
        },
        setUser: (state, action) => { 
            state.userEmail = action.payload;
            state.user = action.payload;  // ✅ Store full user
        },
        setAuthData: (state, action) => {
            state.access = action.payload.access;
            state.user = action.payload.user;
            state.userEmail = action.payload.user?.email;
            state.isAuthenticated = true;
        },
        logout: (state) => {
            state.access = null;
            state.isAuthenticated = false;
            state.userEmail = null;
            state.user = null;  // ✅ Clear user
        },
    },
});

export const { setToken, setUser, logout, setAuthData } = authSlice.actions;
export default authSlice.reducer;