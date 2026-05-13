import React, { useState } from 'react';
import API from '../api/axios';
import { useParams, useNavigate } from 'react-router-dom';

// 1. Password Reset Request Page (Email mangne ke liye)
export const ForgotPassword = () => {
    const [email, setEmail] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await API.post('request-password-reset/', { email });
            alert("If an account exists with this email, a reset link has been sent.");
        } catch (err) {
            alert("Error sending reset link. Please try again.");
        }
    };

    return (
        <div className="container">
            <h2>Reset Password</h2>
            <p>Enter your email to receive a password reset link.</p>
            <form onSubmit={handleSubmit}>
                <input 
                    type="email" 
                    placeholder="Enter your email" 
                    value={email}
                    onChange={e => setEmail(e.target.value)} 
                    required 
                />
                <button type="submit">Send Reset Link</button>
            </form>
        </div>
    );
};

// 2. Set New Password Page (Naya password set karne ke liye)
export const ResetPassword = () => {
    const [password, setPassword] = useState('');
    const { uidb64, token } = useParams(); // URL se uid aur token uthayega
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            // Aapke backend ki SetNewPasswordView yahi data expect kar rahi hai
            await API.post('reset-password/', { 
                password: password, 
                uidb64: uidb64, 
                token: token 
            });
            alert("Password changed successfully! You can now login.");
            navigate('/login');
        } catch (err) {
            const errorMsg = err.response?.data?.detail || "Invalid or expired link.";
            alert("Error: " + errorMsg);
        }
    };

    return (
        <div className="container">
            <h2>Set New Password</h2>
            <form onSubmit={handleSubmit}>
                <input 
                    type="password" 
                    placeholder="Enter new password" 
                    value={password}
                    onChange={e => setPassword(e.target.value)} 
                    required 
                />
                <button type="submit">Update Password</button>
            </form>
        </div>
    );
};