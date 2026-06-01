export const validateRegistration = (data) => {
  const errors = {};

  if (!data.userId || data.userId.length < 4) {
    errors.userId = 'User ID must be at least 4 characters';
  } else if (!/^[a-zA-Z0-9_]+$/.test(data.userId)) {
    errors.userId = 'User ID can only contain letters, numbers, and underscore';
  }

  if (!data.email) {
    errors.email = 'Email is required';
  } else if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(data.email)) {
    errors.email = 'Enter a valid email address';
  }

  if (!data.password) {
    errors.password = 'Password is required';
  } else if (data.password.length < 6) {
    errors.password = 'Password must be at least 6 characters';
  }

  if (data.password !== data.confirmPassword) {
    errors.confirmPassword = 'Passwords do not match';
  }

  return errors;
};

export const validateLogin = (data) => {
  const errors = {};

  if (!data.userId) {
    errors.userId = 'User ID is required';
  }

  if (!data.password) {
    errors.password = 'Password is required';
  }

  if (!data.platform) {
    errors.platform = 'Platform is required';
  }

  return errors;
};

export const validateForgotPassword = (data) => {
  const errors = {};

  if (!data.userId) {
    errors.userId = 'User ID is required';
  }

  return errors;
};

export const validatePasswordChange = (data) => {
  const errors = {};

  if (!data.new_password || data.new_password.length < 8) {
    errors.new_password = 'Password must be at least 8 characters';
  }

  if (data.new_password !== data.confirm_password) {
    errors.confirm_password = 'Passwords do not match';
  }

  return errors;
};