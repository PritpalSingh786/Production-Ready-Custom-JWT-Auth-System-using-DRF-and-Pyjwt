import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import { forgotPasswordSuccess, setLoading, setError, clearMessages } from '../features/auth/authSlice';
import { authAPI } from '../features/auth/authAPI';
import { validateForgotPassword } from '../utils/validation';

const ForgotPassword = () => {
  const dispatch = useDispatch();
  const { isLoading, error, successMessage } = useSelector((state) => state.auth);
  
  const [userId, setUserId] = useState('');
  const [validationError, setValidationError] = useState('');

  useEffect(() => {
    return () => {
      dispatch(clearMessages());
    };
  }, [dispatch]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const errors = validateForgotPassword({ userId });
    if (Object.keys(errors).length > 0) {
      setValidationError(errors.userId);
      return;
    }

    dispatch(setLoading(true));
    dispatch(clearMessages());
    setValidationError('');

    try {
      const response = await authAPI.forgotPassword(userId);
      
      dispatch(forgotPasswordSuccess({
        message: response.message || 'Password reset link sent to your email. Please check your inbox.',
      }));
      
      setUserId('');
      
    } catch (error) {
      const errorMessage = error.response?.data?.message || 
                          error.response?.data?.error || 
                          'Failed to send reset link. Please try again.';
      dispatch(setError(errorMessage));
    } finally {
      dispatch(setLoading(false));
    }
  };

  return (
    <div className="form-container">
      <h2 className="form-title">Forgot Password</h2>
      
      <p style={{ textAlign: 'center', marginBottom: '20px', color: '#666' }}>
        Enter your user ID and we'll send you a link to reset your password.
      </p>
      
      {successMessage && (
        <div className="success-message">
          {successMessage}
        </div>
      )}
      
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>User ID</label>
          <input
            type="text"
            value={userId}
            onChange={(e) => {
              setUserId(e.target.value);
              setValidationError('');
              dispatch(clearMessages());
            }}
            placeholder="Enter your user ID"
            disabled={isLoading}
          />
          {validationError && (
            <small style={{ color: '#c33' }}>{validationError}</small>
          )}
        </div>

        <button type="submit" className="btn" disabled={isLoading || !userId}>
          {isLoading ? <span className="spinner"></span> : 'Send Reset Link'}
        </button>

        <div className="link">
          Remember your password? <Link to="/login">Back to Login</Link>
        </div>
      </form>
    </div>
  );
};

export default ForgotPassword;