import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link, useNavigate } from 'react-router-dom';
import {
  registerSuccess,
  setLoading,
  setError,
  clearMessages,
} from '../features/auth/authSlice';
import { authAPI } from '../features/auth/authAPI';
import { validateRegistration } from '../utils/validation';

const Register = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const { isLoading, error, successMessage } = useSelector(
    (state) => state.auth
  );

  const [formData, setFormData] = useState({
    userId: '',
    email: '',
    password: '',
    confirmPassword: '',
  });

  const [validationErrors, setValidationErrors] = useState({});
  const [backendErrors, setBackendErrors] = useState({});

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  useEffect(() => {
    return () => {
      dispatch(clearMessages());
    };
  }, [dispatch]);

  const handleChange = (e) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    if (validationErrors[name]) {
      setValidationErrors((prev) => ({
        ...prev,
        [name]: '',
      }));
    }

    if (backendErrors[name]) {
      setBackendErrors((prev) => ({
        ...prev,
        [name]: '',
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    dispatch(clearMessages());
    setBackendErrors({});

    const errors = validateRegistration(formData);

    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }

    dispatch(setLoading(true));

    try {
      const response = await authAPI.register({
        user_id: formData.userId,
        email: formData.email,
        password: formData.password,
      });

      dispatch(
        registerSuccess({
          message:
            response.message ||
            'Registration successful! Please check your email.',
        })
      );

      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err) {
      const responseErrors = err.response?.data?.errors;

      if (responseErrors) {
        const formattedErrors = {};

        Object.keys(responseErrors).forEach((key) => {
          formattedErrors[key] = Array.isArray(responseErrors[key])
            ? responseErrors[key][0]
            : responseErrors[key];
        });

        setBackendErrors({
          userId: formattedErrors.user_id || '',
          email: formattedErrors.email || '',
          password: formattedErrors.password || '',
        });
      } else {
        dispatch(
          setError(
            err.response?.data?.message ||
              'Registration failed. Please try again.'
          )
        );
      }
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

      {typeof error === 'string' && error && (
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
            placeholder="Enter User ID"
          />

          {validationErrors.userId && (
            <small style={{ color: 'red' }}>
              {validationErrors.userId}
            </small>
          )}

          {backendErrors.userId && (
            <small style={{ color: 'red', display: 'block' }}>
              {backendErrors.userId}
            </small>
          )}
        </div>

        <div className="form-group">
          <label>Email</label>

          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="Enter Email"
          />

          {validationErrors.email && (
            <small style={{ color: 'red' }}>
              {validationErrors.email}
            </small>
          )}

          {backendErrors.email && (
            <small style={{ color: 'red', display: 'block' }}>
              {backendErrors.email}
            </small>
          )}
        </div>

        <div className="form-group">
          <label>Password</label>

          <div style={{ position: 'relative' }}>
            <input
              type={showPassword ? 'text' : 'password'}
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Enter Password"
              style={{ paddingRight: '45px' }}
            />

            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              style={{
                position: 'absolute',
                right: '10px',
                top: '50%',
                transform: 'translateY(-50%)',
                border: 'none',
                background: 'none',
                cursor: 'pointer',
              }}
            >
              {showPassword ? '🙈' : '👁️'}
            </button>
          </div>

          {validationErrors.password && (
            <small style={{ color: 'red' }}>
              {validationErrors.password}
            </small>
          )}

          {backendErrors.password && (
            <small style={{ color: 'red', display: 'block' }}>
              {backendErrors.password}
            </small>
          )}
        </div>

        <div className="form-group">
          <label>Confirm Password</label>

          <div style={{ position: 'relative' }}>
            <input
              type={showConfirmPassword ? 'text' : 'password'}
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder="Confirm Password"
              style={{ paddingRight: '45px' }}
            />

            <button
              type="button"
              onClick={() =>
                setShowConfirmPassword(!showConfirmPassword)
              }
              style={{
                position: 'absolute',
                right: '10px',
                top: '50%',
                transform: 'translateY(-50%)',
                border: 'none',
                background: 'none',
                cursor: 'pointer',
              }}
            >
              {showConfirmPassword ? '🙈' : '👁️'}
            </button>
          </div>

          {validationErrors.confirmPassword && (
            <small style={{ color: 'red' }}>
              {validationErrors.confirmPassword}
            </small>
          )}
        </div>

        <button
          type="submit"
          className="btn"
          disabled={isLoading}
        >
          {isLoading ? 'Registering...' : 'Register'}
        </button>

        <div className="link">
          Already have an account? <Link to="/login">Login</Link>
        </div>
      </form>
    </div>
  );
};

export default Register;