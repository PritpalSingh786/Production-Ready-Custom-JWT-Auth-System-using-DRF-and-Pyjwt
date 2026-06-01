# 🚀 Custom JWT Authentication System with Django REST Framework, Redis, and React

A production-ready, full-stack authentication system built with **React** and **Django REST Framework**, implementing **JWT authentication**, **Redis-based token management**, **refresh token rotation**, and **real-time session handling** using WebSockets.

This project demonstrates enterprise-grade authentication workflows including multi-device session management, Redis-backed token storage, automatic token refresh, and WebSocket-based real-time session invalidation.

![Django](https://img.shields.io/badge/Django-5.2-green)
![React](https://img.shields.io/badge/React-18.2-blue)
![Redis](https://img.shields.io/badge/Redis-7.0-red)
![JWT](https://img.shields.io/badge/JWT-PyJWT-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Authentication Flow](#-authentication-flow)
- [JWT Security Implementation](#-jwt-security-implementation)
- [Refresh Token Rotation](#-refresh-token-rotation)
- [Token Blacklisting](#-token-blacklisting)
- [Advanced JWT Security Practices](#-advanced-jwt-security-practices)
- [Device-Based Session Handling](#-device-based-session-handling)
- [Redis TTL Strategy](#-redis-ttl-time-to-live-strategy)
- [Redis Token Architecture](#-redis-token-architecture)
- [Redis Usage Benefits](#-redis-usage-benefits)
- [Email & Background Jobs](#-email--background-jobs)
- [API Endpoints](#-api-endpoints)
- [Technology Stack](#-technology-stack)
- [Installation & Setup](#-installation--setup)
- [Testing the Application](#-testing-the-application)
- [Project Structure](#-project-structure)
- [Security Summary](#-security-summary)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)
- [Author](#-author)

---

## 🔥 Project Overview

This system provides a secure authentication workflow with frontend and backend integration, using Redis for token/session management and Celery for asynchronous email handling.

**Key Highlights:**
- Pure PyJWT implementation (no third-party JWT libraries)
- Hybrid token storage (Access token in localStorage, Refresh token in HttpOnly cookie)
- Real-time session invalidation via WebSockets
- Redis TTL-based automatic token expiry
- Enterprise-grade security practices

---

## ✨ Features

### 🔐 Authentication & Security
- **JWT Authentication** (Access + Refresh Tokens)
- **Refresh Token Rotation** - New refresh token on every refresh request
- **Redis-based Token Blacklisting** - Centralized token management
- **HttpOnly Cookies for Refresh Tokens** - Prevents XSS attacks
- **Rate Limiting** on authentication endpoints
- **Email Verification** before login
- **Secure Password Reset** workflow (3-minute expiry tokens)
- **Device-based Session Tracking** with unique device IDs
- **JWT Claims Validation** (iss, aud, exp, iat, jti)

### 📡 Real-time Session Management
- **WebSocket Integration** using Django Channels
- **Real-time Session Invalidation** across multiple devices
- **Automatic Logout** when password is changed from another device
- **Device-based Session Tracking** using `device_id`
- **Redis-based Channel Layer** for WebSocket communication

### 🗄️ Redis & Token Management
- **Centralized token storage** in Redis
- **Automatic TTL-based expiry** - No manual cleanup needed
- **Hash-based user session storage**
- **One-time use tokens** for password reset and email verification

### 📧 Email & Background Jobs
- **Email verification workflow**
- **Password reset emails**
- **New login alerts** with device information
- **Password change confirmation emails**
- **Asynchronous email handling** using Celery

### 🎨 Frontend Features
- **React 18** with Functional Components
- **Redux Toolkit** for State Management
- **Manual Token Persistence** (Access token in localStorage only)
- **Protected Routes** with token verification
- **Axios Interceptors** for automatic token refresh
- **WebSocket Connection** with auto-reconnect
- **Form Validation** with real-time error messages
- **Responsive Design** with CSS gradients

### ⚙️ Backend Features
- **Django REST Framework** APIs
- **Pure PyJWT Implementation** (no third-party JWT libraries)
- **Custom JWT Authentication Class**
- **Redis-based Session Management** with TTL
- **Django Channels** for WebSocket support
- **Celery** for asynchronous email tasks
- **Device Tracking** and session handling

---

## 🧠 System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend                          │
│                  (Redux Toolkit + Axios)                    │
│                    (Port: 3000)                             │
└─────────────────┬───────────────────┬───────────────────────┘
                  │                   │
            HTTP APIs             WebSocket (WS)
          (REST calls)          (Real-time)
                  │                   │
                  ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                  Django REST API + Channels                 │
│              (Custom JWT Authentication)                    │
│                    (Port: 8000)                             │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                         Redis                               │
│  • Refresh Tokens (Hash Map)                               │
│  • Password Reset Tokens (3 min TTL)                       │
│  • Email Verification Tokens (5 min TTL)                   │
│  • WebSocket Channel Layer                                 │
│  • TTL-based Auto Expiry                                   │
│                    (Port: 6379)                             │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL / SQLite                      │
│                    (User Data Only)                         │
└─────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      Celery + Redis                         │
│                  (Async Email Tasks)                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Authentication Flow

```text
┌──────────────┐
│  User Login  │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Django Backend                          │
│  • Validate credentials                  │
│  • Check email verification              │
│  • Generate device_id                    │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  JWT Token Generation                    │
│  • Access Token (15 min expiry)          │
│  • Refresh Token (7 days expiry)         │
│  • Store refresh token in Redis (Hash)   │
│  • Set TTL on Redis keys                 │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Response to Frontend                    │
│  • Access token in JSON                  │
│  • Refresh token in HTTP-only Cookie     │
│  • User data in JSON                     │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  React Frontend                          │
│  • Store access token in localStorage    │
│  • Store user data in Redux              │
│  • Store device_id in localStorage       │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  WebSocket Connection                    │
│  • Connect with access token             │
│  • Join user+device specific group       │
│  • Listen for logout events              │
└──────────────────────────────────────────┘
```

---

## 🔐 JWT Security Implementation

### Access Token

- **Short-lived** access token for API authentication (15 minutes)
- Used for protected API routes
- Stored in **localStorage** (persists across page refreshes)
- Contains minimal claims: `user_id`, `device_id`, `platform`, `jti`
- Automatically refreshed when expired

### Refresh Token

- **Long-lived** refresh token for obtaining new access tokens (7 days)
- Stored securely using **HttpOnly cookies** for web clients
- Managed through **Redis-backed session workflows**
- Rotated on every refresh request
- Cannot be accessed by JavaScript (XSS protection)

---

## 🔁 Refresh Token Rotation

Each refresh request follows this secure workflow:

1. **Validate** existing refresh token from HttpOnly cookie
2. **Generate** new access token
3. **Issue** new refresh token (rotation)
4. **Invalidate** previous refresh token in Redis
5. **Update** Redis hash with new token reference

### Why Rotation?

| Security Benefit | Explanation |
|-----------------|-------------|
| **Token Replay Prevention** | Stolen tokens become invalid after use |
| **Limited Damage Window** | Each token works only once |
| **Session Integrity** | Each refresh creates new credentials |
| **Audit Trail** | Track token usage patterns |

### Rotation Flow Diagram

```text
Initial Login
     │
     ▼
Refresh Token A (RT-A) ──────► Redis Store
     │
     │ (After 15 mins)
     ▼
Refresh Request with RT-A
     │
     ▼
Backend Validates RT-A ✓
     │
     ▼
Generate RT-B ──────► Invalidate RT-A
     │                    │
     │                    ▼
     │              Redis: RT-A Deleted
     │
     ▼
Return RT-B (new) + New Access Token
     │
     ▼
Client stores RT-B (HttpOnly cookie)
```

---

## 🚫 Token Blacklisting

Tokens are blacklisted on logout to prevent further use.

### Blacklisting Mechanism

1. **User initiates logout**
2. **Refresh token JTI extracted** from cookie
3. **Token removed from Redis hash**
4. **Future requests with same token** are rejected

### Redis Blacklisting Strategy

```text
Logout Request
      │
      ▼
Extract JTI from Refresh Token
      │
      ▼
HDEL hash-rt-for-user-{user_id} {jti}
      │
      ▼
Token Removed from Redis
      │
      ▼
Future requests with same token → 401 Unauthorized
```

### Hybrid Approach Benefits

When using refresh token rotation and token blacklisting, JWT authentication becomes a **hybrid approach** combining:

- **Stateless access tokens** - Quick validation, no database lookups
- **Stateful refresh token/session management** - Revocable, controllable

---

## 🔐 Advanced JWT Security Practices

### 🚫 Minimal Token Claims

Tokens avoid storing sensitive user information such as:

- ❌ Email
- ❌ Username
- ❌ Personal details
- ❌ Passwords

**Only minimal claims are included:**

```json
{
  "user_id": "1",
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "platform": "web",
  "type": "access",
  "jti": "unique-token-identifier"
}
```

### 🧾 Issuer (`iss`) Validation

Each token includes an issuer claim to validate token origin.

```json
{
  "iss": "your-app"
}
```

**Validation:** Token must be issued by trusted issuer.

### 🎯 Audience (`aud`) Validation

Each token includes an audience claim to validate intended token usage.

```json
{
  "aud": "your-app-users"
}
```

**Validation:** Token must be intended for this application.

### 🔐 Secure Algorithm Enforcement

- Explicit JWT algorithm validation using `HS256`
- Prevents insecure algorithm usage (e.g., `none` algorithm attacks)
- Algorithm mismatch → Immediate rejection

```python
# utils.py - decode_token()
jwt.decode(
    token,
    settings.SECRET_KEY,
    algorithms=[settings.JWT_ALGORITHM],  # Only HS256 allowed
    audience=settings.JWT_AUDIENCE,
    issuer=settings.JWT_ISSUER
)
```

### 🍪 Secure Cookie Storage

Refresh tokens are stored using secure cookie settings:

```python
response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,      # Not accessible via JavaScript
    secure=False,       # Set to True in production (HTTPS only)
    samesite="Lax",     # CSRF protection
    max_age=7 * 24 * 60 * 60,  # 7 days
    path="/api/users/"
)
```

**Security Benefits:**
- **HttpOnly** → Prevents XSS attacks
- **Secure** (in production) → Only sent over HTTPS
- **SameSite=Lax** → CSRF protection

### 🔄 Token Replay Protection

- Refresh tokens rotate on every refresh request
- Previous refresh tokens are invalidated automatically
- Redis helps manage token/session references
- Stolen tokens become useless after first use

### 📱 Device-Based Token Binding

Each token is associated with a `device_id`.

**Enables:**
- Device tracking
- Device-level logout
- Multi-device session management
- Targeted session invalidation

### ⚡ Real-Time Session Invalidation

- WebSocket-based logout notifications
- Session invalidation events across connected devices
- Real-time session handling workflows
- **Auto-logout on password change** from any device

### 🧠 Secure Token Lifecycle

```text
┌──────────────────────────────────────────────────────┐
│                    Token Lifecycle                   │
├──────────────────────────────────────────────────────┤
│ 1. User Login → Tokens Generated                    │
│ 2. Access Token: 15 minutes (short-lived)           │
│ 3. Refresh Token: 7 days (rotated on each use)      │
│ 4. Redis TTL: Auto-expires after lifetime           │
│ 5. Logout → Token blacklisted (Redis hash delete)   │
│ 6. Password Change → All tokens invalidated         │
└──────────────────────────────────────────────────────┘
```

---

## 📱 Device-Based Session Handling

Each token is associated with a `device_id`, enabling granular session management.

### Device ID Generation

```javascript
// Frontend generates unique device ID on login
const deviceId = crypto.randomUUID();
// Example: "550e8400-e29b-41d4-a716-446655440000"
```

### Device Tracking Capabilities

| Feature | Description |
|---------|-------------|
| **Device Identification** | Each session tied to specific device |
| **Multi-device Support** | Same user can log in from multiple devices |
| **Targeted Logout** | Logout specific devices only |
| **Session Monitoring** | Track active sessions per user |
| **Security Alerts** | Notify on new device logins |

### Device Session Flow

```text
User Device A                    User Device B
     │                                  │
     │ Login                            │
     │ device_id: AAA                    │
     ▼                                  │
Redis: hash-rt-for-user-1              │
  ├── jti_AAA: {device: AAA}           │
  │                                    │
  │                          Login     │
  │                          device_id: BBB
  │                          ▼
  │                    Redis: hash-rt-for-user-1
  │                      ├── jti_AAA: {device: AAA}
  │                      └── jti_BBB: {device: BBB}
  │                                    │
  │ Password Change (Device B)         │
  │                                    │
  │◄───── WebSocket LOGOUT ────────────┤
  │                                    │
  ▼                                    ▼
Auto-logout                         Session continues
```

---

## ⏱️ Redis TTL (Time-To-Live) Strategy

Redis TTL automatically expires tokens and sessions after their lifetime, eliminating the need for manual cleanup jobs.

### Token Expiry Configuration

| Token Type | Redis Key Pattern | TTL Duration | Purpose |
|------------|------------------|--------------|---------|
| **Refresh Token Session** | `hash-rt-for-user-{user_id}` | 7 days | User session storage |
| **Individual Refresh Token** | Hash field within user hash | 7 days | Token-level expiry |
| **Password Reset Token** | `pwd_reset:{user_id}` | 3 minutes | Secure password reset |
| **Email Verification Token** | `email_verify:{user_id}:{token}` | 5 minutes | Email verification |
| **Legacy Password Reset** | `password_reset:{user_id}:{token}` | 5 minutes | Legacy reset flow |

### How Redis TTL Works in This Project

#### 1. Refresh Token Session TTL
```python
# utils.py - store_refresh_token()
ttl_seconds = settings.REFRESH_TOKEN_LIFETIME * 24 * 60 * 60  # 7 days in seconds
redis_client.expire(user_tokens_key, ttl_seconds)
```

**What happens:** After 7 days, entire user session hash is automatically deleted from Redis.

#### 2. Password Reset Token TTL
```python
# utils.py - secure_generate_password_reset_token()
redis_client.setex(
    f"pwd_reset:{user_id}",
    180,  # 3 minutes (180 seconds)
    token
)
```

**What happens:** After 3 minutes, token auto-deletes from Redis. User must request new reset link.

#### 3. Email Verification Token TTL
```python
# utils.py - generate_verification_token()
redis_client.setex(key, 300, json.dumps(token_data))  # 5 minutes (300 seconds)
```

**What happens:** After 5 minutes, verification link expires. User needs new verification email.

### TTL Flow Diagram

```text
User Login
    │
    ▼
Store Refresh Token in Redis
    │
    ├── Key: hash-rt-for-user-{user_id}
    ├── TTL: 7 days (604800 seconds)
    └── Redis starts countdown
    │
    ▼
┌─────────────────────────────────────┐
│  Day 1-6: Token Active             │
│  Day 7: Token about to expire      │
│  Day 7 + 1 second: AUTO DELETED!   │
└─────────────────────────────────────┘
    │
    ▼
User must login again
    │
    ▼
New session created with new TTL
```

### Benefits of Redis TTL

| Benefit | Explanation |
|---------|-------------|
| **Automatic Cleanup** | No cron jobs or scheduled tasks needed |
| **Memory Optimization** | Expired tokens don't clutter Redis memory |
| **Security** | Tokens automatically removed after lifetime |
| **Performance** | Redis handles expiry natively (O(1) operation) |
| **Stateless Expiry** | No database queries to check token age |

### TTL-Based Security Features

**Automatic Session Termination**
- Users are automatically logged out after 7 days of inactivity
- No need for server-side cleanup jobs
- Redis handles expiry natively

**One-Time Token Security**
- Password reset links work only for 3 minutes
- Email verification links work only for 5 minutes
- After TTL expires, tokens are completely removed

**Memory Management**
- Redis memory doesn't grow indefinitely
- Expired tokens don't need manual deletion
- Average memory usage remains stable

### Redis TTL Commands for Debugging

```bash
# Check TTL for user session (in seconds)
redis-cli
> TTL hash-rt-for-user-1
> (integer) 604800  # 7 days remaining

# Check if key exists
> EXISTS hash-rt-for-user-1
> (integer) 1  # Key exists

# Get remaining TTL in human-readable format
> PTTL hash-rt-for-user-1
> (integer) 604800000  # milliseconds

# Watch key auto-delete (monitor mode)
> MONITOR

# Check all keys with their TTL
redis-cli --scan | while read key; do 
    ttl=$(redis-cli ttl "$key")
    echo "$key: $ttl seconds remaining"
done

# Check expired keys count
redis-cli info stats | grep expired_keys
```

### Production Tuning

For production, adjust TTL values in `settings.py`:

```python
# settings.py
REFRESH_TOKEN_LIFETIME = 7        # 7 days for web
ACCESS_TOKEN_LIFETIME = 15        # 15 minutes
PASSWORD_RESET_TIMEOUT = 180      # 3 minutes (seconds)
EMAIL_VERIFICATION_TIMEOUT = 300  # 5 minutes (seconds)

# For high-security apps
REFRESH_TOKEN_LIFETIME = 1        # 1 day
ACCESS_TOKEN_LIFETIME = 5         # 5 minutes

# For remember-me features
REFRESH_TOKEN_LIFETIME = 30       # 30 days
ACCESS_TOKEN_LIFETIME = 15        # 15 minutes
```

---

## 🗄️ Redis Token Architecture

| Key Pattern | Purpose | TTL |
|-------------|---------|-----|
| `hash-rt-for-user-{user_id}` | User's refresh tokens hash map | 7 days |
| `pwd_reset:{user_id}` | Password reset tokens (secure) | 3 minutes |
| `email_verify:{user_id}:{token}` | Email verification tokens | 5 minutes |
| `password_reset:{user_id}:{token}` | Legacy password reset tokens | 5 minutes |

### Redis Hash Structure

```redis
# User session hash example
redis-cli
> HGETALL hash-rt-for-user-1
1) "550e8400-e29b-41d4-a716-446655440000"  # jti
2) "{\"jti\":\"550e8400...\",\"user_id\":\"1\",\"device_id\":\"device-123\",\"platform\":\"web\",\"created_at\":\"2024-01-01T00:00:00\"}"
```

---

## ⚡ Redis Usage Benefits

| Benefit | Description |
|---------|-------------|
| **Centralized token management** | Single source of truth for all sessions |
| **Automatic expiry handling** | Native Redis TTL eliminates cleanup jobs |
| **Simplified blacklist workflows** | HDEL operations instead of database queries |
| **Real-time session handling** | Sub-second token validation |
| **Reduced database load** | User tokens never hit PostgreSQL |
| **Horizontal scalability** | Redis Cluster for multi-node deployments |
| **Atomic operations** | Thread-safe token operations |

---

## 📧 Email & Background Jobs

### Email Workflows

| Email Type | Trigger | TTL | Async |
|------------|---------|-----|-------|
| **Verification Email** | User Registration | 5 minutes | ✅ Celery |
| **Password Reset Email** | Forgot Password request | 3 minutes | ✅ Celery |
| **New Login Alert** | Login from new device | N/A | ✅ Celery |
| **Password Change Confirmation** | Password updated | N/A | ✅ Celery |

### Celery Task Examples

```python
# tasks.py
@shared_task
def send_email_task(subject, message, recipient_list):
    """Async email sending"""
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)

@shared_task
def send_new_login_alert_task(user_email, id, userId, device_name, ip_address, platform, reset_token):
    """Send alert email when new login detected"""
    reset_link = f"{settings.DOMAIN_URL}/secure-password-change-template/{id}/{reset_token}/"
    # ... email content
    send_email_task.delay(subject, message, [user_email])
```

### Celery Worker Setup

```bash
# Start Celery worker
celery -A auth_project worker --loglevel=info

# Start Celery beat for periodic tasks (optional)
celery -A auth_project beat --loglevel=info

# Monitor Celery tasks
celery -A auth_project inspect active
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description | Auth Required | Request Body |
|--------|----------|-------------|---------------|--------------|
| POST | `/api/users/register/` | Register new user | ❌ | `{user_id, email, password}` |
| POST | `/api/users/login/` | User login | ❌ | `{userId, password, platform}` |
| POST | `/api/users/token/refresh/` | Refresh access token | ❌ | `{platform}` (cookie: refresh_token) |
| POST | `/api/users/logout/` | Logout | ❌ | `{platform}` (cookie: refresh_token) |
| GET | `/api/users/authenticated/` | Get user data | ✅ | None |
| POST | `/api/users/forgot-password/` | Request reset email | ❌ | `{userId}` |
| POST | `/api/users/password-change/` | Reset password with token | ❌ | `{user_id, token, new_password, confirm_password}` |
| POST | `/api/users/secure-password-change/` | Change password (logged in) | ✅ | `{user_id, token, current_password, new_password, confirm_password}` |
| WS | `/ws/auth/?token=<access_token>` | WebSocket connection | ✅ | Query param: `token` |

### Response Examples

**Login Response (Web Platform):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "userId": "john_doe",
    "email": "john@example.com"
  }
}
```
*Refresh token automatically set as HttpOnly cookie*

**Login Response (Mobile Platform):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "userId": "john_doe",
    "email": "john@example.com"
  }
}
```

**Authenticated User Response:**
```json
{
  "msg": "Welcome to authenticated view",
  "user": {
    "id": 1,
    "userId": "john_doe",
    "email": "john@example.com"
  },
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "platform": "web"
}
```

---

## 🛠️ Technology Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Django | 5.2+ | Web framework |
| Django REST Framework | 3.15+ | API development |
| PyJWT | 2.8+ | JWT encoding/decoding |
| Redis | 7.0+ | Token storage & session management |
| Django Channels | 4.1+ | WebSocket support |
| Celery | 5.3+ | Async email tasks |
| PostgreSQL | 15+ | Production database |
| SQLite | 3+ | Development database |
| Daphne | 4.1+ | ASGI server for WebSockets |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.2+ | UI framework |
| Redux Toolkit | 1.9+ | State management |
| React Router DOM | 6.20+ | Routing |
| Axios | 1.6+ | HTTP client with interceptors |

### Development Tools

| Tool | Purpose |
|------|---------|
| Git | Version control |
| pip | Python package management |
| npm | Node package management |
| Redis CLI | Redis debugging |
| Django Debug Toolbar | Performance profiling |

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Redis Server 7.0+
- PostgreSQL (optional, SQLite works for development)
- Git

### Backend Setup

```bash
# 1. Clone repository
git clone https://github.com/PritpalSingh786/Production-Ready-Custom-JWT-Auth-System-using-DRF-and-Pyjwt.git
cd Production-Ready-Custom-JWT-Auth-System-using-DRF-and-Pyjwt

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup Redis (Linux/Mac)
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis                   # MacOS
redis-server

# 5. Configure environment variables
cp .env.example .env
# Edit .env with your configurations

# 6. Run migrations
python manage.py migrate

# 7. Create superuser (optional)
python manage.py createsuperuser

# 8. Start Celery worker (new terminal)
celery -A auth_project worker --loglevel=info

# 9. Start Django with Daphne (WebSocket support)
daphne -b 127.0.0.1 -p 8000 auth_project.asgi:application
```

### Frontend Setup

```bash
# 1. Navigate to frontend directory
cd react-auth-frontend

# 2. Install dependencies
npm install

# 3. Configure environment
cp .env.example .env
# Edit .env with your backend URL

# 4. Start development server
npm start
```

### Environment Variables

**Backend (.env)**
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0
DOMAIN_URL=http://localhost:3000
JWT_ISSUER=your-app
JWT_AUDIENCE=your-app-users
JWT_ALGORITHM=HS256
ACCESS_TOKEN_LIFETIME=15
REFRESH_TOKEN_LIFETIME=7
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

**Frontend (.env)**
```env
REACT_APP_API_URL=http://localhost:8000/api/users
REACT_APP_WS_URL=ws://localhost:8000/ws/auth
REACT_APP_DOMAIN_URL=http://localhost:3000
```

### Docker Setup (Optional)

```dockerfile
# Dockerfile for backend
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "auth_project.asgi:application"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - db
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: auth_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
```

---

## 🧪 Testing the Application

### Test Registration Flow
1. Open `http://localhost:3000/register`
2. Create new account with user_id, email, password
3. Check email for verification link
4. Click verification link (automatically verifies email)
5. Login with credentials

### Test Real-time Auto-logout
1. Login in **Browser A** (Chrome)
2. Login in **Browser B** (Firefox/Incognito)
3. In Browser B, change password using "Forgot Password" flow
4. **Browser A will automatically logout** within seconds
5. Browser A redirects to login page with message

### Test Token Refresh
1. Login and note the access token expiry (15 minutes)
2. After 15 minutes, make an API request
3. Axios interceptor automatically refreshes token
4. Request retries successfully with new token

### Test Multi-Device Session
1. Login from different browsers/devices
2. Check that each device has unique `device_id`
3. Change password from one device
4. Other devices receive WebSocket logout notification

### API Testing with cURL

```bash
# Register
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{"user_id":"testuser","email":"test@example.com","password":"testpass123"}'

# Login
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"userId":"testuser","password":"testpass123","platform":"web"}'

# Refresh token (cookie automatically sent)
curl -X POST http://localhost:8000/api/users/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"platform":"web"}' \
  --cookie "refresh_token=your-refresh-token"

# Get authenticated user
curl -X GET http://localhost:8000/api/users/authenticated/ \
  -H "Authorization: Bearer your-access-token"
```

---

## 📁 Project Structure

```
auth_project/                    # Django Backend
├── auth_project/
│   ├── __init__.py
│   ├── settings.py             # Django settings
│   ├── urls.py                 # Main URL config
│   ├── asgi.py                 # ASGI config for WebSockets
│   └── celery.py               # Celery app config
├── users/                      # Main authentication app
│   ├── __init__.py
│   ├── admin.py                # Admin interface
│   ├── models.py               # User model
│   ├── views.py                # API views
│   ├── serializers.py          # DRF serializers
│   ├── utils.py                # JWT utilities
│   ├── tasks.py                # Celery tasks
│   ├── consumers.py            # WebSocket consumers
│   ├── routing.py              # WebSocket routing
│   ├── websocketjwtmiddleware.py # JWT middleware for WS
│   └── urls.py                 # App URL config
├── templates/                  # Email templates
│   └── users/
│       ├── email_verification_success.html
│       ├── email_verification_error.html
│       └── secure_password_change_template.html
├── manage.py
└── requirements.txt

react-auth-frontend/            # React Frontend
├── public/
│   └── index.html
├── src/
│   ├── app/
│   │   ├── store.js            # Redux store configuration
│   │   └── socket.js           # WebSocket service
│   ├── components/
│   │   ├── Navbar.jsx          # Navigation bar
│   │   ├── ProtectedRoute.jsx  # Route guard
│   │   ├── LoadingSpinner.jsx  # Loading indicator
│   │   └── WebSocketDebug.jsx  # Debug component
│   ├── features/
│   │   └── auth/
│   │       ├── authSlice.js    # Redux slice
│   │       └── authAPI.js      # API calls
│   ├── hooks/
│   │   └── useWebSocket.js     # WebSocket custom hook
│   ├── pages/
│   │   ├── Register.jsx        # Registration page
│   │   ├── Login.jsx           # Login page
│   │   ├── Dashboard.jsx       # Dashboard page
│   │   ├── ForgotPassword.jsx  # Forgot password page
│   │   └── PasswordChange.jsx  # Password change page
│   ├── utils/
│   │   ├── axiosConfig.js      # Axios with interceptors
│   │   └── validation.js       # Form validation
│   ├── App.js                  # Main app component
│   ├── index.js                # Entry point
│   └── index.css               # Global styles
├── .env                        # Environment variables
└── package.json
```

---

## 🔒 Security Summary

| Security Feature | Implementation Status |
|-----------------|----------------------|
| **HttpOnly Cookies** for Refresh Tokens | ✅ Implemented |
| **Minimal JWT Claims** | ✅ Implemented |
| **JWT Audience Validation** | ✅ Implemented |
| **JWT Issuer Validation** | ✅ Implemented |
| **Refresh Token Rotation** | ✅ Implemented |
| **Redis-based Token Blacklisting** | ✅ Implemented |
| **Rate Limiting** | ✅ Implemented |
| **Email Verification** | ✅ Implemented |
| **Secure Password Reset** (3 min TTL) | ✅ Implemented |
| **Device-based Session Tracking** | ✅ Implemented |
| **Real-time Session Invalidation** | ✅ Implemented |
| **CORS Configuration** | ✅ Implemented |
| **Redis TTL Auto-expiry** | ✅ Implemented |
| **One-time Use Tokens** | ✅ Implemented |
| **2FA (Two-Factor Authentication)** | 🔜 Planned |
| **OAuth2 Social Login** | 🔜 Planned |
| **RBAC (Role-Based Access Control)** | 🔜 Planned |
| **Session Management Dashboard** | 🔜 Planned |

---

## 🐛 Troubleshooting

### WebSocket Connection Issues

```bash
# Make sure you're using daphne, not runserver
daphne -b 127.0.0.1 -p 8000 auth_project.asgi:application

# Check Redis is running
redis-cli ping  # Should return PONG

# Check WebSocket URL in browser console
console.log(process.env.REACT_APP_WS_URL)

# Verify token in WebSocket connection
ws://localhost:8000/ws/auth/?token=your-access-token
```

### Token Refresh Failing

```bash
# Clear browser cookies and localStorage
# Check Redis hash exists
redis-cli
> KEYS hash-rt-for-user-*
> HGETALL hash-rt-for-user-1

# Check TTL
> TTL hash-rt-for-user-1

# Manual token refresh test
curl -X POST http://localhost:8000/api/users/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"platform":"web"}' \
  --cookie "refresh_token=your-token" -v
```

### Email Not Sending

```bash
# For Gmail, use App Password (not regular password)
# Enable 2FA on Google account
# Generate App Password: Google Account > Security > App Passwords

# Test Celery
celery -A auth_project worker --loglevel=info

# Test email in Django shell
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Message', 'from@example.com', ['to@example.com'])
```

### CORS Issues

```python
# settings.py - Add these settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = ['*']
```

### Redis Connection Issues

```bash
# Check Redis is running
ps aux | grep redis

# Check Redis port
netstat -an | grep 6379

# Test Redis connection
redis-cli -h localhost -p 6379 ping

# Check Redis config
redis-cli CONFIG GET maxmemory
redis-cli INFO memory
```

### Common Error Messages

| Error | Solution |
|-------|----------|
| `No route found for path 'ws/auth'` | Use daphne instead of runserver |
| `Invalid or expired refresh token` | Check Redis hash TTL, user may need to login again |
| `Email not verified` | Click verification link sent to email |
| `CORS policy blocked` | Add origin to CORS_ALLOWED_ORIGINS |
| `WebSocket disconnected with code 4001` | Invalid or missing token in WebSocket connection |

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. **Fork** the repository
2. **Create** your feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use ESLint for JavaScript/React code
- Write meaningful commit messages
- Add comments for complex logic
- Update documentation for new features

---

## 📝 License

This project is open-source and available under the MIT License.

```
MIT License

Copyright (c) 2024 Pritpal Singh

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions...
```

---

## 👨‍💻 Author

**Pritpal Singh**

- 🔗 [GitHub Profile](https://github.com/PritpalSingh786)
- 🔗 [Project Repository](https://github.com/PritpalSingh786/Production-Ready-Custom-JWT-Auth-System-using-DRF-and-Pyjwt)

---

## 🙏 Acknowledgments

- Django REST Framework community
- PyJWT documentation
- Redis documentation
- React community
- Django Channels team
- Celery team

---

## ⭐ Star the Project

If you found this project helpful, please give it a star on GitHub! ⭐

---

## 📊 Project Stats

- **Language:** Python 50.3%, JavaScript 13.8%, HTML 35.1%, CSS 0.8%
- **Latest Commit:** June 2, 2026
- **Commits:** 21
- **Contributors:** 1

---

**Built with ❤️ using Django, React, Redis, and WebSockets**

---

*For questions, issues, or feature requests, please open an issue on GitHub.*
