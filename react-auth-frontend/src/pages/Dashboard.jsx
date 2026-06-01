import { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { useWebSocket } from '../hooks/useWebSocket';
import { authAPI } from '../features/auth/authAPI';
import Navbar from '../components/Navbar';
import LoadingSpinner from '../components/LoadingSpinner';

const Dashboard = () => {
  const { user, deviceId, platform, accessToken } = useSelector((state) => state.auth);
  const [authData, setAuthData] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useWebSocket();

  useEffect(() => {
    fetchAuthenticatedData();
  }, [accessToken]);

  const fetchAuthenticatedData = async () => {
    try {
      const response = await authAPI.getAuthenticatedUser();
      setAuthData(response);
    } catch (error) {
      console.error('Failed to fetch authenticated data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <>
      <Navbar />
      <div className="container">
        <div className="dashboard">
          <h1>Welcome to your Dashboard</h1>
          
          <div className="dashboard-card">
            <h3>User Information</h3>
            <p><strong>User ID:</strong> {user?.userId}</p>
            <p><strong>Email:</strong> {user?.email}</p>
            <p><strong>User ID (from token):</strong> {user?.id}</p>
          </div>

          <div className="dashboard-card">
            <h3>Session Information</h3>
            <p><strong>Platform:</strong> {platform}</p>
            <p><strong>Device ID:</strong> {deviceId || 'Not available'}</p>
            <p><strong>Access Token Present:</strong> {accessToken ? 'Yes' : 'No'}</p>
          </div>

          {authData && (
            <div className="dashboard-card">
              <h3>Authenticated View Data</h3>
              <p><strong>Message:</strong> {authData.msg}</p>
              <p><strong>Device ID:</strong> {authData.device_id || 'N/A'}</p>
              <p><strong>Platform:</strong> {authData.platform || 'N/A'}</p>
            </div>
          )}

          <div className="dashboard-card">
            <h3>WebSocket Status</h3>
            <p>Connected for real-time notifications</p>
            <p><small>You will receive instant notifications if logged out from other devices</small></p>
          </div>
        </div>
      </div>
    </>
  );
};

export default Dashboard;