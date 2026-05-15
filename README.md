# 🚀 Custom JWT Authentication System with Django REST Framework, Redis, and React

A full-stack authentication system built using React and Django REST Framework, implementing JWT authentication, Redis-based token management, refresh token rotation, and real-time session handling using WebSockets.

This project demonstrates backend authentication workflows commonly used in modern web applications, including multi-device session management, Redis-backed token/session storage, and WebSocket-based session invalidation.

---

# 🔥 Project Overview

This system provides a secure authentication workflow with frontend and backend integration, using Redis for token/session management and Celery for asynchronous email handling.

---

# ✨ Features

* JWT Authentication (Access + Refresh Tokens)
* Refresh Token Rotation
* Redis-based Token Blacklisting
* Multi-device Session Management
* Real-time Session Handling using WebSockets
* Email Verification & Password Reset
* Background Email Processing using Celery
* Automatic Token Expiry using Redis TTL
* Protected API Routes
* Device-based Session Tracking

---

# 🔐 Authentication & Security Features

* Access and Refresh Token workflow
* Refresh token rotation
* Redis-backed token/session management
* Token blacklisting on logout
* HttpOnly cookie support for refresh tokens
* Rate limiting on authentication endpoints
* Email verification before login
* Secure password reset workflow
* Device-level session management
* JWT issuer (`iss`) and audience (`aud`) validation
* Secure algorithm enforcement using `HS256`

---

# 📡 Session Management

* Maximum 5 active sessions per user
* Automatic oldest-session logout when session limit exceeds
* Real-time session invalidation using WebSockets
* Device-based session tracking using `device_id`
* Redis-based channel layer for WebSocket communication
* Automatic token expiration using Redis TTL

---

# 🗄️ Redis Token Architecture

| Key Pattern           | Purpose               |
| --------------------- | --------------------- |
| `rt:<jti>`            | Refresh token data    |
| `bl:<jti>`            | Blacklisted tokens    |
| `user:<id>:tokens`    | User token references |
| `device:<uuid>:token` | Device-token mapping  |

---

# ⚡ Redis Usage Benefits

* Centralized token and session management
* Automatic expiry handling using Redis TTL
* Simplified blacklist workflows
* Better support for real-time session handling
* Reduced dependency on scheduled cleanup jobs

---

# 📧 Email & Background Jobs

* Email verification workflow
* Password reset emails
* Session activity notifications
* Asynchronous email handling using Celery

---

# 🎨 Frontend Features

* React-based UI
* Redux Toolkit state management
* Redux Persist integration
* Protected routes
* Axios interceptors for token refresh
* WebSocket connection handling
* Token expiry detection
* Responsive frontend design

---

# ⚙️ Backend Features

* Django REST Framework APIs
* Custom PyJWT authentication implementation
* Redis-based token/session workflows
* WebSocket support using Django Channels
* Real-time communication using Redis channel layers
* Device tracking and session handling

---

# 🧠 System Architecture

```txt
React Frontend
      │
      │ HTTP + WebSocket
      ▼
Django REST API + Channels
      │
      │ JWT + Redis Session Management
      ▼
┌──────────────────────────────────┐
│              Redis               │
│  • Refresh Tokens               │
│  • Blacklisted Tokens           │
│  • User Sessions                │
│  • Device Mappings              │
│  • TTL-based Expiry             │
└──────────────────────────────────┘
      │
      ▼
Database (User Data)
      │
      ▼
Celery (Async Emails)
```

---

# 🔄 Authentication Flow

```txt
User Login
      │
      ▼
JWT Issued (Access + Refresh)
      │
      ▼
Refresh Token Stored in Redis
      │
      ▼
WebSocket Connection Established
      │
      ▼
Session Limit Validation
      │
      ▼
Session Events Sent to Frontend
      │
      ▼
Frontend Handles Auto Logout
```

---

# 🔐 Token Workflow

## Access Token

* Short-lived token for API authentication
* Stored on frontend state

## Refresh Token

* Used to generate new access tokens
* Stored in HttpOnly cookie (web)
* Stored in Redis with automatic expiry

---

# 🔁 Refresh Token Rotation

Each refresh request:

1. Generates a new access token
2. Issues a new refresh token
3. Blacklists previous refresh token
4. Updates Redis token references

---

# 🚫 Token Blacklisting

* Tokens are blacklisted on logout
* Blacklisted token references are stored in Redis
* Redis TTL automatically removes expired entries

---

# 📱 Device-Based Session Handling

Each token is associated with a `device_id`.

This enables:

* Device tracking
* Session management
* Targeted logout workflows
* Multi-device authentication support

---

# 🔌 API Endpoints

| Method | Endpoint                             | Description            |
| ------ | ------------------------------------ | ---------------------- |
| POST   | `/api/users/register/`               | Register user          |
| POST   | `/api/users/login/`                  | User login             |
| POST   | `/api/users/token/refresh/`          | Refresh token          |
| POST   | `/api/users/logout/`                 | Logout                 |
| GET    | `/api/users/profile/`                | User profile           |
| POST   | `/api/users/change-password/`        | Change password        |
| POST   | `/api/users/request-password-reset/` | Request password reset |
| POST   | `/api/users/reset-password/`         | Reset password         |
| GET    | `/api/users/devices/`                | List active devices    |
| GET    | `/api/users/sessions/`               | Active sessions        |
| WS     | `/ws/auth/?token=<token>`            | WebSocket connection   |

---

# 🛠️ Technology Stack

## Backend

* Django
* Django REST Framework
* PyJWT
* Redis
* Django Channels
* Celery
* SQLite / PostgreSQL

## Frontend

* React
* Redux Toolkit
* Redux Persist
* Axios
* React Router

---

# 🎯 Use Cases

* Authentication systems for web applications
* Multi-device login workflows
* JWT + Redis learning projects
* Real-time session handling examples
* Backend authentication architecture practice

---

# 🚀 Future Improvements

* OAuth Integration (Google/GitHub)
* Role-Based Access Control (RBAC)
* Docker Deployment
* Kubernetes Support
* Two-Factor Authentication (2FA)
* Admin Session Dashboard

---

# 🧠 What This Project Demonstrates

* Custom JWT authentication workflows
* Refresh token rotation and blacklisting
* Redis-based token/session management
* WebSocket-based real-time communication
* Multi-device session handling
* Celery-based asynchronous tasks
* Full-stack integration using React and Django

---

# 👨‍💻 Author

**Pritpal Singh**

🔗 [GitHub Profile](https://github.com/PritpalSingh786?utm_source=chatgpt.com)

🔗 [Project Repository](https://github.com/PritpalSingh786/Production-Ready-Custom-JWT-Auth-System-using-DRF-and-Pyjwt?utm_source=chatgpt.com)
