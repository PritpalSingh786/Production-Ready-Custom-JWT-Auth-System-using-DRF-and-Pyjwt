import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { loginSuccess, setLoading, setError, clearMessages, setSuccess, setDeviceId } from '../features/auth/authSlice';
import { authAPI } from '../features/auth/authAPI';
import { validateLogin } from '../utils/validation';

const Login = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const { isLoading, error, isAuthenticated, successMessage } = useSelector((state) => state.auth);
  
  const [formData, setFormData] = useState({
    userId: '',
    password: '',
    platform: 'web',
  });
  
  const [validationErrors, setValidationErrors] = useState({});

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
    
    if (location.state?.message) {
      dispatch(setSuccess(location.state.message));
    }
    
    return () => {
      dispatch(clearMessages());
    };
  }, [isAuthenticated, navigate, dispatch, location]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    if (validationErrors[e.target.name]) {
      setValidationErrors({
        ...validationErrors,
        [e.target.name]: '',
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const errors = validateLogin(formData);
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }

    dispatch(setLoading(true));
    dispatch(clearMessages());

    try {
      const response = await authAPI.login(formData);
      
      const deviceId = crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36);
      dispatch(setDeviceId(deviceId));
      
      // Store only access token and user data (refresh token is in HTTP-only cookie)
      dispatch(loginSuccess({
        access: response.access,
        user: response.user,
      }));
      
      navigate('/dashboard');
      
    } catch (error) {
      const errorMessage = error.response?.data?.message || 
                          error.response?.data?.error || 
                          'Login failed. Please check your credentials.';
      dispatch(setError(errorMessage));
    } finally {
      dispatch(setLoading(false));
    }
  };

  return (
    <div className="form-container">
      <h2 className="form-title">Login</h2>
      
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
      
      {successMessage && (
        <div className="success-message">
          {successMessage}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>User ID</label>
          <input
            type="text"
            name="userId"
            value={formData.userId}
            onChange={handleChange}
            placeholder="Enter your user ID"
          />
          {validationErrors.userId && (
            <small style={{ color: '#c33' }}>{validationErrors.userId}</small>
          )}
        </div>

        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="Enter your password"
          />
          {validationErrors.password && (
            <small style={{ color: '#c33' }}>{validationErrors.password}</small>
          )}
        </div>

        <div className="form-group">
          <label>Platform</label>
          <select
            name="platform"
            value={formData.platform}
            onChange={handleChange}
          >
            <option value="web">Web</option>
            <option value="mobile">Mobile</option>
          </select>
          {validationErrors.platform && (
            <small style={{ color: '#c33' }}>{validationErrors.platform}</small>
          )}
        </div>

        <button type="submit" className="btn" disabled={isLoading}>
          {isLoading ? <span className="spinner"></span> : 'Login'}
        </button>

        <div className="link">
          <Link to="/forgot-password">Forgot Password?</Link>
        </div>
        
        <div className="link">
          Don't have an account? <Link to="/register">Register</Link>
        </div>
      </form>
    </div>
  );
};

export default Login;