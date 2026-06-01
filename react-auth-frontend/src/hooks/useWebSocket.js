// src/hooks/useWebSocket.js
import { useEffect, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { webSocketService } from '../app/socket';
import { logoutSuccess, setWebSocket } from '../features/auth/authSlice';
import { useNavigate } from 'react-router-dom';

export const useWebSocket = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { accessToken, user, deviceId, isAuthenticated } = useSelector((state) => state.auth);
  const isConnected = useRef(false);
  const retryCount = useRef(0);

  useEffect(() => {
    // Only connect if authenticated, has token, user, deviceId, and not already connected
    if (isAuthenticated && accessToken && user && deviceId && !isConnected.current) {
      console.log('🔄 Initializing WebSocket connection...');
      console.log('Token:', accessToken.substring(0, 50) + '...');
      console.log('User ID:', user.id);
      console.log('Device ID:', deviceId);
      
      const handleLogout = (data) => {
        console.log('🚪 Logout notification received, logging out...');
        
        // Clear storage
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        localStorage.removeItem('platform');
        localStorage.removeItem('deviceId');
        
        // Dispatch logout
        dispatch(logoutSuccess());
        
        // Disconnect WebSocket
        webSocketService.disconnect();
        isConnected.current = false;
        
        // Redirect to login
        navigate('/login', { 
          state: { message: data.message || 'You have been logged out from all devices' } 
        });
      };

      // Connect WebSocket
      webSocketService.connect(accessToken, user.id, deviceId, handleLogout);
      dispatch(setWebSocket(webSocketService));
      isConnected.current = true;
      retryCount.current = 0;

      // Cleanup on unmount
      return () => {
        console.log('🧹 Cleaning up WebSocket connection...');
        webSocketService.disconnect();
        isConnected.current = false;
        dispatch(setWebSocket(null));
      };
    }
  }, [isAuthenticated, accessToken, user, deviceId, dispatch, navigate]);

  return { 
    isConnected: webSocketService.isConnected(),
    wsService: webSocketService 
  };
};