import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link, useNavigate } from 'react-router-dom';
import { registerSuccess, setLoading, setError, clearMessages } from '../features/auth/authSlice';
import { authAPI } from '../features/auth/authAPI';
import { validateRegistration } from '../utils/validation';

const Register = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { isLoading, error, successMessage } = useSelector((state) => state.auth);
  
  const [formData, setFormData] = useState({
    userId: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  
  const [validationErrors, setValidationErrors] = useState({});

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
    
    const errors = validateRegistration(formData);
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }

    dispatch(setLoading(true));
    dispatch(clearMessages());

    try {
      const response = await authAPI.register({
        user_id: formData.userId,
        email: formData.email,
        password: formData.password,
      });
      
      dispatch(registerSuccess({
        message: response.message || 'Registration successful! Please check your email for verification.',
      }));
      
      setTimeout(() => {
        navigate('/login', { 
          state: { message: 'Registration successful! Please verify your email before logging in.' }
        });
      }, 3000);
      
    } catch (error) {
      const errorMessage = error.response?.data?.errors || 
                          error.response?.data?.message || 
                          'Registration failed. Please try again.';
      dispatch(setError(typeof errorMessage === 'object' ? JSON.stringify(errorMessage) : errorMessage));
    } finally {
      dispatch(setLoading(false));
    }
  };

  return (
    <div className="form-container">
      <h2 className="form-title">Register</h2>
      
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
            name="userId"
            value={formData.userId}
            onChange={handleChange}
            placeholder="Enter user ID (min 4 characters)"
          />
          {validationErrors.userId && (
            <small style={{ color: '#c33' }}>{validationErrors.userId}</small>
          )}
        </div>

        <div className="form-group">
          <label>Email</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="Enter email address"
          />
          {validationErrors.email && (
            <small style={{ color: '#c33' }}>{validationErrors.email}</small>
          )}
        </div>

        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="Enter password (min 6 characters)"
          />
          {validationErrors.password && (
            <small style={{ color: '#c33' }}>{validationErrors.password}</small>
          )}
        </div>

        <div className="form-group">
          <label>Confirm Password</label>
          <input
            type="password"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleChange}
            placeholder="Confirm password"
          />
          {validationErrors.confirmPassword && (
            <small style={{ color: '#c33' }}>{validationErrors.confirmPassword}</small>
          )}
        </div>

        <button type="submit" className="btn" disabled={isLoading}>
          {isLoading ? <span className="spinner"></span> : 'Register'}
        </button>

        <div className="link">
          Already have an account? <Link to="/login">Login</Link>
        </div>
      </form>
    </div>
  );
};

export default Register;