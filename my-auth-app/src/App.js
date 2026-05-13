import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { useEffect } from 'react';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import { ForgotPassword, ResetPassword } from './pages/ForgotPassword';
import VerifyEmailPage from "./pages/VerifyEmailPage";
import { connectSocket, disconnectSocket } from './socket/socket';
import { isTokenExpired } from './utils/token';
import { logout } from './features/auth/authSlice';
import './App.css';

function App() {
    const dispatch = useDispatch();
    const token = useSelector(state => state.auth.access);
    const isAuth = useSelector(state => state.auth.isAuthenticated);

    // 🔥 SOCKET CONNECT - FIXED DEPENDENCY
    useEffect(() => {
        if (token) {
            connectSocket(token, dispatch);
        }

        return () => {
            disconnectSocket();
        };
    }, [token, dispatch]);  // ✅ Added dispatch here

    // 🔥 TOKEN EXPIRY CHECK
    useEffect(() => {
        if (token && isTokenExpired(token)) {
            dispatch(logout());
        }
    }, [token, dispatch]);  // ✅ Added dispatch here

    return (
        <Router>
            <Navbar />
            <Routes>
                <Route path="/login" element={!isAuth ? <Login /> : <Navigate to="/dashboard" />} />
                <Route path="/register" element={<Register />} />
                <Route path="/verify-email/:uid/:token" element={<VerifyEmailPage />} />
                <Route path="/forgot-password" element={<ForgotPassword />} />
                <Route path="/reset-password/:uidb64/:token" element={<ResetPassword />} />
                <Route path="/dashboard" element={isAuth ? <Dashboard /> : <Navigate to="/login" />} />
                <Route path="*" element={<Navigate to="/login" />} />
            </Routes>
        </Router>
    );
}

export default App;