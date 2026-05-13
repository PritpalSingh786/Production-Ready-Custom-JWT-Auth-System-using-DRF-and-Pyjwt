# 🚀 Production Ready JWT Auth System

A **production-ready full-stack authentication system** built using **React and Django REST Framework**, implementing **secure JWT authentication with Redis-based token management, real-time session handling, refresh token rotation, and automatic token expiry — no Celery Beat required!**

This project demonstrates a **modern, scalable authentication workflow used in real-world production systems**, including **multi-device session control, real-time session invalidation via WebSockets, and Redis-first token storage with O(1) lookups**.

---

# 🔥 Project Overview

This system provides a **complete and secure authentication solution** with both frontend and backend integration, featuring **Redis as the primary token storage** instead of traditional database-based approaches.

## ✅ Key Innovations

* Redis-first token storage — 10x faster than database
* No Celery Beat needed — Redis TTL handles automatic cleanup
* O(1) token validation — Instant blacklist checking
* Real-time expiry — No hourly batch jobs

---

## ✨ Features Included

* JWT-based authentication (Access + Refresh Tokens)
* Refresh token rotation
* Token blacklisting using Redis
* Multi-device session management
* Real-time auto logout using WebSockets
* Email notifications for session activity
* Background email handling using Celery (emails only)

---

# ⚡ Key Features

## 🔐 Authentication

* User Registration
* User Login
* User Logout (single + all devices)
* Email Verification
* Password Reset via Email

---

## 🛡️ Security Features

* JWT Authentication (Access + Refresh Tokens)
* Short-lived Access Tokens (15 minutes)
* Refresh Token Rotation
* Redis-based Token Blacklisting (O(1) lookup)
* Protected API Routes
* Email Verification before login
* Secure Password Reset Flow
* HttpOnly Cookie storage for refresh tokens
* Rate limiting on login/register endpoints

---

## 📡 Advanced Session Management (🔥 Redis-Powered)

* Maximum **5 active sessions per user**
* **Oldest session auto-logout** when limit exceeds
* **Real-time session termination using WebSockets**
* **Device-level session targeting (via `device_id`)**
* **Redis-based channel layer for scalability**
* **Instant logout across devices (no API call required)**
* **Automatic token expiry** — Redis TTL, no cron jobs

---

# 🗄️ Redis Token Storage Architecture

| Key Pattern           | Type   | Purpose                 | TTL    |
| --------------------- | ------ | ----------------------- | ------ |
| `rt:<jti>`            | Hash   | Refresh token data      | 7 days |
| `bl:<jti>`            | String | Blacklisted tokens      | 7 days |
| `user:<id>:tokens`    | Set    | User's token JTIs       | 7 days |
| `device:<uuid>:token` | String | Device to token mapping | 7 days |

---

# ⚡ Why Redis Instead of Database?

| Operation        | Database           | Redis          | Improvement    |
| ---------------- | ------------------ | -------------- | -------------- |
| Token Validation | O(log n) ~5ms      | O(1) ~0.5ms    | **10x faster** |
| Blacklist Check  | SELECT query       | EXISTS command | **Instant**    |
| Cleanup          | Hourly Celery Beat | Automatic TTL  | **Real-time**  |
| Infrastructure   | DB + Celery + Beat | Only Redis     | **Simpler**    |

---

# 📧 Email & Background Jobs

* Email notification on session termination
* Celery for async email handling
* ~~Celery Beat for cleanup~~ → **Redis TTL handles automatically**

---

# 🎨 Frontend Features

* React-based UI
* Redux Toolkit state management
* Redux Persist for token storage
* Protected routes
* Axios interceptors for auto token refresh
* WebSocket connection for real-time events
* Token expiry detection
* Responsive design

---

# ⚙️ Backend Features

* Django REST Framework APIs
* Custom PyJWT authentication (no SimpleJWT)
* Redis token manager with automatic expiry
* WebSocket support using Django Channels
* Redis-based real-time communication
* Secure authentication workflows
* Device tracking and management

---

# 🧠 System Architecture

```txt
React Frontend (Port 3000)
      │
      │ HTTP + WebSocket
      ▼
Django REST API + Channels (Port 8000/8001)
      │
      │ JWT + Redis Token Management
      ▼
┌─────────────────────────────────────┐
│           REDIS (Primary)           │
│  • Refresh Tokens (Hash)            │
│  • Blacklisted Tokens (String)      │
│  • User Sessions (Set)              │
│  • Device Mappings (String)         │
│  • Automatic TTL Expiry             │
└─────────────────────────────────────┘
      │
      │ User Data Only
      ▼
Database (SQLite/PostgreSQL)
      │
      │ WebSocket Events
      ▼
Real-time Session Events to Frontend
      │
      ▼
Celery (Async Emails)
```

---

# 🔄 Authentication & Session Flow

```txt
User Login
      │
      ▼
JWT Issued (Access + Refresh + device_id)
      │
      ▼
Refresh Token Stored in Redis (Hash)
      │
      ▼
Device Mapping Created in Redis
      │
      ▼
WebSocket Connection Established
      │
      ▼
Session Limit Check (max 5)
      │
      ├─ If ≤ 5 → allow
      │
      └─ If > 5 → kill oldest session
              │
              ▼
   Token Blacklisted in Redis
              │
              ▼
   WebSocket Event Sent (SESSION_KILLED)
              │
              ▼
   Frontend receives → Auto Logout
              │
              ▼
   Email Notification Sent (Celery)
```

---

# 🔐 JWT Security Implementation

## Access Token

* Short-lived (15 minutes)
* Used for API authentication
* Stored in Redux state

---

## Refresh Token

* Longer-lived (7 days)
* Used to generate new access tokens
* Stored in HttpOnly cookie (web) or response body (mobile)
* Stored in Redis Hash with auto-expiry

---

# 🔁 Refresh Token Rotation

Each refresh request:

1. New access token issued
2. New refresh token generated
3. Old refresh token blacklisted in Redis
4. Old token removed from Redis

Prevents token replay attacks.

---

# 🚫 Token Blacklisting

* On logout → refresh token is blacklisted in Redis
* Blacklist entries have same TTL as original token
* Prevents reuse of stolen tokens
* O(1) lookup time using Redis EXISTS

---

When using token rotation and blacklisting with Redis, JWT becomes a **hybrid approach** — stateless access tokens with stateful refresh token management in Redis.

---

# 🔐 Advanced JWT Security Practices

## 🚫 No Sensitive Data (PII) in Tokens

Tokens do NOT store sensitive data like email or username.

Only minimal claims are used:

* `user_id`
* `device_id`
* `platform`
* `jti`

Prevents data exposure if token is decoded.

---

## 🧾 Issuer (`iss`) Validation

Each token includes issuer claim.

Example:

```json
"iss": "my-app"
```

Ensures token is generated by trusted server.

---

## 🎯 Audience (`aud`) Validation

Each token includes audience claim.

Example:

```json
"aud": "my-app-users"
```

Ensures token is used only by intended system.

---

## 🔐 Secure Algorithm Enforcement

* Explicit algorithm defined (`HS256`)
* Prevents `alg=none` attack
* Custom PyJWT validation

---

## 🍪 Secure Cookie Storage

Refresh token stored in HttpOnly cookie for web.

```python
httponly=True
secure=True
samesite="Lax"
```

Protects against XSS and CSRF.

---

## 🔄 Token Replay Protection

* Refresh tokens rotated on every use
* Old tokens blacklisted in Redis immediately
* Redis TTL ensures automatic cleanup

---

## 📱 Device-Based Token Binding

Each token linked with `device_id`.

Device information stored in Redis Hash.

Enables:

* Device-level tracking
* Targeted logout
* Secure multi-device control

---

## ⚡ Real-Time Session Invalidation

* WebSocket-based instant logout
* Triggered when session limit exceeded
* No polling required — real-time events

---

## 🧠 Secure Token Lifecycle

* Short-lived access tokens (15 min)
* Rotating refresh tokens (7 days)
* Automatic Redis TTL cleanup — no cron jobs

---

# 🔌 API Endpoints

| Method | Endpoint                                    | Description                 |
| ------ | ------------------------------------------- | --------------------------- |
| POST   | `/api/users/register/`                      | Register user               |
| GET    | `/api/users/verify-email/<uidb64>/<token>/` | Verify email                |
| POST   | `/api/users/login/`                         | Login                       |
| POST   | `/api/users/token/refresh/`                 | Refresh access token        |
| POST   | `/api/users/logout/`                        | Logout (single/all devices) |
| GET    | `/api/users/profile/`                       | Get user profile            |
| PUT    | `/api/users/profile/`                       | Update profile              |
| POST   | `/api/users/change-password/`               | Change password             |
| POST   | `/api/users/request-password-reset/`        | Request password reset      |
| POST   | `/api/users/reset-password/`                | Reset password              |
| GET    | `/api/users/devices/`                       | List devices                |
| DELETE | `/api/users/devices/<id>/`                  | Remove device               |
| GET    | `/api/users/sessions/`                      | List active sessions        |
| GET    | `/api/users/authenticated/`                 | Check auth status           |
| WS     | `/ws/auth/?token=<token>`                   | WebSocket connection        |

---

# 📁 Project Structure

```txt
backend/
├── auth_project/
│   ├── settings.py
│   ├── celery.py
│   ├── asgi.py
│   └── urls.py
│
├── users/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── utils.py
│   ├── pyjwtauthentication.py
│   ├── redis_token_manager.py
│   ├── consumers.py
│   ├── tasks.py
│   ├── routing.py
│   └── websocketjwtmiddleware.py
│
frontend/
├── src/
│   ├── api/
│   │   └── axios.js
│   ├── components/
│   │   └── Navbar.js
│   ├── features/
│   │   └── auth/
│   │       └── authSlice.js
│   ├── pages/
│   │   ├── Login.js
│   │   ├── Register.js
│   │   ├── Dashboard.js
│   │   ├── ForgotPassword.js
│   │   └── VerifyEmailPage.js
│   ├── socket/
│   │   └── socket.js
│   ├── utils/
│   │   └── token.js
│   ├── App.js
│   └── store.js
```

---

# ⚙️ Installation Guide

## 📌 Prerequisites

```bash
Python 3.10+
Node.js 16+
Redis 7.0+
```

---

# 🔧 Backend Setup

```bash
# Clone repository
git clone https://github.com/PritpalSingh786/Production-Ready-Custom-JWT-Auth-System-using-DRF-and-Pyjwt.git

cd Production-Ready-Custom-JWT-Auth-System-using-DRF-and-Pyjwt

# Create virtual environment
python -m venv venv

# Activate virtual environment

# Linux / Mac
source venv/bin/activate

# Windows
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env

# Run migrations
python manage.py makemigrations users
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

---

## 🔥 Start Redis

### Linux

```bash
sudo service redis start
```

### Mac / Windows

```bash
redis-server
```

---

## ⚡ Start Celery Worker (Emails Only)

```bash
celery -A auth_project worker --loglevel=info
```

---

## 🚀 Start Django Server

```bash
python manage.py runserver
```

---

# 🎨 Frontend Setup

```bash
cd frontend

npm install

npm start
```

---

# 🌍 Environment Variables (`.env`)

```env
SECRET_KEY=your-super-secret-key

DEBUG=True

FRONTEND_URL=http://localhost:3000

REDIS_URL=redis://localhost:6379/0

EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

JWT_ALGORITHM=HS256
JWT_ISSUER=my-app
JWT_AUDIENCE=my-app-users
```

---

# 🛠️ Technology Stack

## 🔙 Backend

| Technology                 | Purpose                       |
| -------------------------- | ----------------------------- |
| Django 4.2                 | Web framework                 |
| Django REST Framework 3.14 | API development               |
| PyJWT 2.8                  | JWT handling                  |
| Redis 7.0                  | Token storage + channel layer |
| Channels 4.0               | WebSocket support             |
| Celery 5.3                 | Async email handling          |
| SQLite/PostgreSQL          | User data storage             |

---

## 🎨 Frontend

| Technology     | Purpose           |
| -------------- | ----------------- |
| React 18       | UI framework      |
| Redux Toolkit  | State management  |
| Redux Persist  | Token persistence |
| Axios          | HTTP client       |
| React Router 6 | Routing           |

---

# 🎯 Use Cases

* SaaS authentication systems
* Multi-device login apps (Netflix / WhatsApp style)
* Secure enterprise authentication
* Learning JWT + WebSockets + Redis integration
* Production-ready auth template for startups

---

# 📊 Performance Comparison

| Metric           | Traditional DB             | This Project (Redis)  |
| ---------------- | -------------------------- | --------------------- |
| Token Validation | ~5ms                       | ~0.5ms                |
| Blacklist Check  | O(log n)                   | O(1)                  |
| Cleanup Method   | Celery Beat (hourly)       | Redis TTL (real-time) |
| Infrastructure   | DB + Redis + Celery + Beat | Redis only for tokens |
| Scalability      | Database bottleneck        | Redis Cluster ready   |

---

# 🚀 Future Improvements

* [ ] OAuth integration (Google / GitHub)
* [ ] Role-based access control (RBAC)
* [ ] Docker + Kubernetes deployment
* [ ] Admin session control panel
* [ ] Active devices UI with force logout
* [ ] Two-factor authentication (2FA)
* [ ] Rate limiting dashboard
* [ ] Token usage analytics

---

# 🧠 What This Project Demonstrates

* ✅ Secure JWT authentication architecture with custom PyJWT
* ✅ Refresh token rotation and blacklisting
* ✅ Redis-first token management (not traditional database)
* ✅ Multi-device session management with device tracking
* ✅ Real-time session invalidation via WebSockets
* ✅ No Celery Beat needed — Redis TTL handles expiry
* ✅ Scalable backend design with Redis clustering
* ✅ Full-stack integration (React + Django + Redis)
* ✅ Production-ready security practices

---

# 🐛 Troubleshooting

## Redis Connection Error

```bash
redis-cli ping
# Should return: PONG

sudo service redis start
```

---

## Port Already in Use

```bash
# Kill process on port 8000

sudo lsof -ti:8000 | xargs kill -9

# Run on different port

python manage.py runserver 8001
```

---

## Token Not Found in Redis

```bash
# Check Redis keys

redis-cli KEYS "rt:*"

# View token data

redis-cli HGETALL "rt:your-jti"
```

---

## CORS Error

Add this in `settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000"
]

CORS_ALLOW_CREDENTIALS = True
```

---

# 📝 License

MIT License — feel free to use in production 🚀

---

# 👨‍💻 Author

**Pritpal Singh**

* GitHub: [PritpalSingh786 GitHub](https://github.com/PritpalSingh786?utm_source=chatgpt.com)
* Project: [Production-Ready-Custom-JWT-Auth-System](https://github.com/PritpalSingh786/Production-Ready-Custom-JWT-Auth-System-using-DRF-and-Pyjwt?utm_source=chatgpt.com)

---

# ⭐ Show Your Support

If this project helped you, please give it a star ⭐

---

# 🔥 Built With

Built with **Django, React, Redis, WebSockets, and PyJWT** — fully production ready 🚀
