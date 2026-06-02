import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { logoutSuccess, setLoading, setError, clearMessages } from '../features/auth/authSlice';
import { validatePasswordChange } from '../utils/validation';
import axios from 'axios';
import { webSocketService } from '../app/socket';

const PasswordChange = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { user_id, token } = useParams();
  const { isLoading, error, successMessage } = useSelector((state) => state.auth);
  
  const [formData, setFormData] = useState({
    new_password: '',
    confirm_password: '',
  });
  
  const [validationErrors, setValidationErrors] = useState({});
  const [tokenValid, setTokenValid] = useState(true);
  
  // Password show/hide states
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  useEffect(() => {
    return () => {
      dispatch(clearMessages());
    };
  }, [dispatch]);

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
    
    const errors = validatePasswordChange(formData);
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }

    dispatch(setLoading(true));
    dispatch(clearMessages());

    try {
      const API_URL = process.env.REACT_APP_API_URL;
      const response = await axios.post(`${API_URL}/secure-password-change/`, {
        user_id: user_id,
        token: token,
        current_password: formData.new_password,
        new_password: formData.new_password,
        confirm_password: formData.confirm_password,
      });
      
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      localStorage.removeItem('platform');
      localStorage.removeItem('deviceId');
      
      webSocketService.disconnect();
      dispatch(logoutSuccess());
      
      setTimeout(() => {
        navigate('/login', { 
          state: { message: response.data.message || 'Password changed successfully! Please login with your new password.' }
        });
      }, 2000);
      
    } catch (error) {
      const errorMessage = error.response?.data?.message || 
                          error.response?.data?.error || 
                          'Password change failed. Link may have expired.';
      dispatch(setError(errorMessage));
      setTokenValid(false);
    } finally {
      dispatch(setLoading(false));
    }
  };

  if (!tokenValid && error) {
    return (
      <div className="form-container">
        <h2 className="form-title">Password Reset Link Expired</h2>
        <div className="error-message">
          {error}
        </div>
        <div className="link">
          <Link to="/forgot-password">Request a new password reset link</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="form-container">
      <h2 className="form-title">Reset Password</h2>
      
      {successMessage && (
        <div className="success-message">
          {successMessage}
        </div>
      )}
      
      {error && !successMessage && (
        <div className="error-message">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>New Password</label>
          <div style={{ position: 'relative' }}>
            <input
              type={showNewPassword ? "text" : "password"}
              name="new_password"
              value={formData.new_password}
              onChange={handleChange}
              placeholder="Enter new password (min 8 characters)"
              style={{ paddingRight: '40px' }}
              disabled={isLoading}
            />
            <button
              type="button"
              onClick={() => setShowNewPassword(!showNewPassword)}
              style={{
                position: 'absolute',
                right: '10px',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                fontSize: '16px'
              }}
              disabled={isLoading}
            >
              {showNewPassword ? '🙈' : '👁️'}
            </button>
          </div>
          {validationErrors.new_password && (
            <small style={{ color: '#c33' }}>{validationErrors.new_password}</small>
          )}
        </div>

        <div className="form-group">
          <label>Confirm Password</label>
          <div style={{ position: 'relative' }}>
            <input
              type={showConfirmPassword ? "text" : "password"}
              name="confirm_password"
              value={formData.confirm_password}
              onChange={handleChange}
              placeholder="Confirm new password"
              style={{ paddingRight: '40px' }}
              disabled={isLoading}
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              style={{
                position: 'absolute',
                right: '10px',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                fontSize: '16px'
              }}
              disabled={isLoading}
            >
              {showConfirmPassword ? '🙈' : '👁️'}
            </button>
          </div>
          {validationErrors.confirm_password && (
            <small style={{ color: '#c33' }}>{validationErrors.confirm_password}</small>
          )}
        </div>

        <button type="submit" className="btn" disabled={isLoading}>
          {isLoading ? <span className="spinner"></span> : 'Reset Password'}
        </button>

        <div className="link">
          <Link to="/login">Back to Login</Link>
        </div>
      </form>
    </div>
  );
};

export default PasswordChange;