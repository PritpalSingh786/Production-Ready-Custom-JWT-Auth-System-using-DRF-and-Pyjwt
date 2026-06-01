import { Link, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { logoutSuccess, setLoading, setError } from '../features/auth/authSlice';
import { authAPI } from '../features/auth/authAPI';
import { webSocketService } from '../app/socket';

const Navbar = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { user, platform, isLoading } = useSelector((state) => state.auth);

  const handleLogout = async () => {
    try {
      dispatch(setLoading(true));
      // Refresh token is automatically sent via cookie
      await authAPI.logout(platform);
      webSocketService.disconnect();
      dispatch(logoutSuccess());
      navigate('/login', { state: { message: 'You have been logged out successfully.' } });
    } catch (error) {
      dispatch(setError(error.response?.data?.message || 'Logout failed'));
      webSocketService.disconnect();
      dispatch(logoutSuccess());
      navigate('/login');
    } finally {
      dispatch(setLoading(false));
    }
  };

  return (
    <nav className="navbar">
      <div className="container">
        <Link to="/dashboard" className="navbar-brand">
          Auth App
        </Link>
        <div className="navbar-menu">
          <Link to="/dashboard">Dashboard</Link>
          <span>Welcome, {user?.userId}</span>
          <button onClick={handleLogout} className="logout-btn" disabled={isLoading}>
            {isLoading ? 'Logging out...' : 'Logout'}
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;