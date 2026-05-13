// pages/Login.js
import React, { useState } from 'react';
import API from '../api/axios';
import { useDispatch } from 'react-redux';
import { setToken, setUser } from '../features/auth/authSlice';
import { Link } from 'react-router-dom';

const Login = () => {
    const [form, setForm] = useState({ username: '', password: '' });
    const dispatch = useDispatch();

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const res = await API.post('login/', { ...form, platform: 'web' });
            dispatch(setToken(res.data.access));
            dispatch(setUser(res.data.user));  // ✅ Store user info
        } catch (err) { 
            alert("Login Failed: " + (err.response?.data?.non_field_errors || "Invalid credentials")); 
        }
    };

    return (
        <div className="container">
            <h2>Login</h2>
            <form onSubmit={handleSubmit}>
                <input 
                    type="text" 
                    placeholder="Username" 
                    onChange={e => setForm({...form, username: e.target.value})} 
                    required
                />
                <input 
                    type="password" 
                    placeholder="Password" 
                    onChange={e => setForm({...form, password: e.target.value})} 
                    required
                />
                <button type="submit">Login</button>
            </form>
            <Link to="/forgot-password">Forgot Password?</Link>
        </div>
    );
};

export default Login;