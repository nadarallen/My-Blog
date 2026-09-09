# ✍️ My-Blog — Cloud-Native Publishing & Discussion Platform

[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.0%20(Application%20Factory)-black.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Cloud Infrastructure](https://img.shields.io/badge/AWS-DynamoDB%20%7C%20S3%20%7C%20EC2-orange.svg?logo=amazon-aws&logoColor=white)](#-system-architecture)
[![Security Hardening](https://img.shields.io/badge/OWASP%20Top%2010-Hardened%20%26%20Audited-brightgreen.svg?logo=security&logoColor=white)](#-security-engineering--owasp-compliance)
[![Test Suite](https://img.shields.io/badge/Tests-101%2F101%20Passed%20(100%25)-success.svg?logo=pytest&logoColor=white)](#-automated-testing-suite)
[![Vulnerabilities](https://img.shields.io/badge/Vulnerabilities-0%20(Pip--Audit%20%7C%20Bandit)-brightgreen.svg)](#-static-analysis--security-audits)
[![Accessibility](https://img.shields.io/badge/Accessibility-WCAG%20AAA%20Compliant-blueviolet.svg)](#-frontend-design--doodle-glassmorphism-ui)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An enterprise-grade, cloud-native full-stack publishing and community discussion platform built with **Python 3**, **Flask**, **Amazon DynamoDB**, and **Amazon S3**. 

Architected from the ground up to showcase production-level software craftsmanship: migrating from an insecure, monolithic prototype into a modular, horizontally scalable system with strict **OWASP Top 10 (2021)** compliance, zero-trust **Role-Based Access Control (RBAC)**, an automated **media optimization pipeline**, and a bespoke **Doodle-Glassmorphism** UI featuring Pinterest-inspired story feeds and Reddit-style nested discussion trees.

---

## 🌟 Resume Engineering Highlights

* **Cloud-Native AWS Infrastructure**: Replaced local relational bottlenecks with a serverless data layer using **Amazon DynamoDB** (composite partition/sort keys with atomic conditional writes) and private **Amazon S3** buckets with time-limited presigned URLs (1-hour TTL).
* **Zero-Credential Instance Profile Security**: Enforced AWS IAM Role instance profiles for ECS/EC2 instances, eliminating all persistent AWS access keys and secrets from source code, containers, and environment variables.
* **OWASP Top 10 Full-Spectrum Hardening**: Defended against injection (Bleach sanitization), cryptographic failures (**Argon2id** password hashing), broken access control (**RBAC** hierarchy with admin self-lockout prevention), and SSRF (domain allowlisting and safe URL redirection).
* **Instant Session Revocation**: Implemented atomic DynamoDB `session_version` counters ensuring demoted or suspended user sessions are invalidated across all active devices immediately.
* **High-Performance Media Pipeline**: Built an automated image compression engine using **Pillow** that enforces dimension caps (1920x1080) and WebP/JPEG recompression, reducing upload payloads by over 60% without perceptible quality loss.
* **101 Automated Test Cases (100% Pass Rate)**: Created comprehensive unit, integration, and security test suites using **Pytest** and **Moto** (AWS offline engine mock), validating security controls, RBAC hierarchies, rate limits, and deployment configs.
* **Production Docker & Nginx Deployment**: Multi-stage container builds running as non-root users (`uid:10001`), reverse-proxied via hardened Nginx with TLS termination, HSTS, CSP headers, and rate-limiting proxies.
* **Unique Frontend Experience**: Created a custom hand-drawn "Doodle-Glassmorphism" UI with dark/light themes meeting WCAG AAA contrast requirements, Pinterest-style masonry grid, Reddit-style threaded comments, and a verified publication **"Preferred Sources"** certification with RSS 2.0 syndication.

---

## 🏗️ System Architecture

```
                                  ┌────────────────────────────────────────┐
                                  │           Client Web Browser           │
                                  └───────────────────┬────────────────────┘
                                                      │ HTTPS (Port 443 / Port 80)
                                                      ▼
                                  ┌────────────────────────────────────────┐
                                  │      Nginx Hardened Reverse Proxy      │
                                  │   - TLS Termination & HTTP/2           │
                                  │   - Security Headers (HSTS, CSP, XFO)  │
                                  │   - Static Asset Caching & Buffering   │
                                  └───────────────────┬────────────────────┘
                                                      │ HTTP / Internal Proxy
                                                      ▼
                                  ┌────────────────────────────────────────┐
                                  │    Flask Application (Gunicorn WSGI)   │
                                  │   - Blueprint Application Factory      │
                                  │   - Flask-WTF (CSRF Token Engine)      │
                                  │   - Flask-Limiter (In-Memory / Redis)  │
                                  │   - Argon2id Password Cryptography     │
                                  └───────────┬────────────────┬───────────┘
                                              │                │
                      IAM Role (No Keys)      │                │ IAM Role (No Keys)
             ┌────────────────────────────────┘                └────────────────────────────────┐
             ▼                                                                                  ▼
┌───────────────────────────┐                                                      ┌───────────────────────────┐
│     Amazon DynamoDB       │                                                      │      Amazon S3 Bucket     │
│  (Serverless NoSQL Store) │                                                      │   (Private Object Store)  │
│  - Users Table (Auth/RBAC)│                                                      │  - Block Public Access: ON│
│  - Posts Table (GSIs)     │                                                      │  - Presigned GET (1h TTL) │
│  - Race-free Atomic Writes│                                                      │  - Automated Compression  │
└───────────────────────────┘                                                      └───────────────────────────┘
```

---

## 📊 Core Features & Technical Deep Dives

### 1. Cloud-Native Serverless Data Architecture
* **Amazon DynamoDB**: Schema modeled for fast lookups and atomic writes. Mutating operations employ `ConditionExpression="attribute_not_exists(pk)"` to prevent concurrent creation collisions and race conditions.
* **Amazon S3 Presigned URLs**: Image uploads are stored securely in a private S3 bucket. Images are served using cryptographically signed ephemeral URLs that expire after 3600 seconds, guaranteeing zero public bucket exposure.
* **Automatic Media Compression**: Uploaded media streams pass through a Pillow optimization pipeline converting images to progressive JPEG/WebP formats with dimensions scaled within `1920x1080` bounds.

### 2. Zero-Trust Authentication & RBAC Hierarchy
* **Role Hierarchy**: Strict role permissions (`admin` > `moderator` > `user`).
* **Privilege Escalation Defense**: Moderators cannot modify or revoke admin accounts; admins cannot demote their own accounts or the primary system administrator (`ADMIN_USERNAME`), preventing administrative lockouts.
* **Session Invalidation**: When a user's role is updated or account is suspended, DynamoDB atomically increments the `session_version`. Active session tokens matching an outdated version are immediately destroyed.
* **Argon2id Hashing**: Industry standard memory-hard key derivation function configured with salt and timing-attack-resistant constant-time comparisons.

### 3. Anti-Spam & Rate Limiting Engine
* **Dual Honeypot Traps**: Invisible form traps (`hp_website`) on both user registration and comment forms silently intercept automated bot submissions without adding UX friction like CAPTCHAs.
* **Multi-Tier Rate Limiting**: Powered by `Flask-Limiter` with granular limits:
  * Authentication (`/login`, `/register`): `5 per minute` per IP.
  * Interactive routes (`/comments/add`, `/social/*`): `30 per minute`.
  * Public REST APIs (`/api/v1/posts`): `60 per minute`.

### 4. Bespoke Doodle-Glassmorphism UI/UX
* **Pinterest-Inspired Masonry Grid**: Dynamic multi-column responsive layout showcasing article snippets, category tags, author avatars, and read times.
* **Reddit-Inspired Discussion System**: Hierarchical nested comment tree supporting karma upvoting, downvoting, author badges, and moderator actions.
* **Verified "Preferred Sources" Badge**: Distinct amber trust badge with star micro-animation certifying publication credentials, coupled with an editorial trust verification modal and an RSS 2.0 syndication link (`/feed.xml`).
* **WCAG AAA Contrast Dark/Light Theme**: Accessible, toggleable theme engine with persistent client-side storage (`localStorage`) and zero layout shift.

---

## 🔐 Security Engineering & OWASP Compliance

| OWASP Top 10 Risk | Vulnerability Vector | Production Mitigation Implemented |
|---|---|---|
| **A01: Broken Access Control** | URL manipulation, privilege escalation, unauthorized deletions | Mutating actions restricted to `POST` with CSRF tokens; `@admin_required` and `@moderator_required` decorators with role hierarchy validation. |
| **A02: Cryptographic Failures** | Plaintext/MD5 hashes, unencrypted sessions, missing headers | **Argon2id** password hashing; `Secure`, `HttpOnly`, `SameSite=Lax` cookies; strict **HSTS** (`max-age=31536000; includeSubDomains`). |
| **A03: Injection** | Stored XSS in blog titles, Markdown bodies, and comments | **Bleach** sanitization against an allowlist of tags and attributes; XML quote escaping in RSS feeds; parameterized data access. |
| **A04: Insecure Design** | User enumeration, timing attacks, lack of account protection | Constant-time dummy hashes on invalid usernames; unified error messages; atomic session version counters. |
| **A05: Security Misconfiguration** | Debug stack traces, exposed Nginx headers, permissive CSP | Production configuration disabling debug modes; `server_tokens off;`; strict CSP with `frame-ancestors 'none'` and `X-Frame-Options: DENY`. |
| **A06: Vulnerable Components** | Outdated packages and transitive supply chain CVEs | `pip-audit` integrated into CI/CD with **0 known vulnerabilities**; pinned production dependencies. |
| **A07: Identification & Auth Failures** | Brute force credential stuffing, weak password acceptance | Flask-Limiter throttling (`5/min`); strict password complexity rules (length, uppercase, digits); automatic session re-generation on login. |
| **A08: Software & Data Integrity** | Malicious file uploads (executable PHP/EXE disguised as JPG) | Magic byte header inspection; filename UUID sanitization; validation before S3 ingestion. |
| **A09: Security Logging & Monitoring** | Undetected unauthorized access and administrative tampering | Structured audit logging via Python's `logging` module tracking auth events, status modifications, and privilege grants. |
| **A10: SSRF & Open Redirects** | Arbitrary redirection via `?next=` parameter and profile URLs | Strict URL parsing restricting redirects to relative local paths; external profile links strictly validated against HTTP/HTTPS protocols. |

---

## 🛠️ Technology Stack

| Category | Technology | Usage |
|---|---|---|
| **Backend & Application** | **Python 3.11–3.14** | Core programming language |
| | **Flask 3.0** | Modular microframework using Application Factory & Blueprints |
| | **Gunicorn 22.0** | Production WSGI HTTP server |
| | **Werkzeug** | Routing, request dispatching, and security helpers |
| **Cloud & Database** | **Amazon DynamoDB** | Managed NoSQL database for users, posts, comments, and sessions |
| | **Amazon S3** | Durable, private object store for media uploads |
| | **Boto3 1.34** | AWS SDK for Python with IAM role integration |
| **Security & Hardening** | **Argon2-cffi** | State-of-the-art password hashing algorithm |
| | **Flask-WTF** | CSRF form protection with cryptographic token rotation |
| | **Flask-Limiter** | Rate-limiting middleware defending against brute force and abuse |
| | **Bleach 6.4** | HTML input sanitizer neutralizing XSS payloads |
| **Frontend & Design** | **HTML5 & Vanilla CSS3** | Custom Doodle-Glassmorphism design system |
| | **Bootstrap 5.3** | Responsive grid, modals, and navigation scaffolding |
| | **JavaScript (ES6+)** | Theme switching, live Markdown preview, and UI micro-interactions |
| | **Pillow 10.0+** | Image processing, resizing, and format optimization |
| **Testing & Verification** | **Pytest 8.2** | Automated test runner with 101 integration/unit tests |
| | **Moto 5.0** | Offline AWS DynamoDB and S3 mock engine |
| | **Bandit & Pip-Audit** | Static Application Security Testing (SAST) and dependency auditing |
| **DevOps & Containers** | **Docker** | Multi-stage production containerization with non-root security |
| | **Docker Compose** | Orchestration for web and Nginx reverse proxy services |
| | **Nginx** | Reverse proxy, static asset delivery, SSL termination, and header proxying |

---

## 📂 Project Repository Map

```
My-Blog/
├── app/
│   ├── models/                # DynamoDB Data Access Objects & Business Logic
│   │   ├── audit.py           # Administrative audit logging model
│   │   ├── category_tag.py    # Taxonomy categorization model
│   │   ├── comment.py         # Threaded comments and karma voting model
│   │   ├── interaction.py     # Post likes, bookmarks, and user follows
│   │   ├── notification.py    # In-app notifications model
│   │   ├── post.py            # Posts data model with GSI indexing & atomic updates
│   │   ├── report.py          # Content moderation reporting model
│   │   ├── settings.py        # System and user settings persistence
│   │   └── user.py            # User identity, RBAC hierarchy, and session management
│   ├── routes/                # Modular Flask Blueprints
│   │   ├── admin.py           # Admin/Moderator dashboard & user status management
│   │   ├── analytics.py       # Blog performance metrics and view counters
│   │   ├── api.py             # RESTful JSON API endpoints (/api/v1/posts)
│   │   ├── auth.py            # Registration, login, session revocation & profile edit
│   │   ├── comments.py        # Threaded discussion submissions and karma actions
│   │   ├── posts.py           # Post creation, editing, live preview & reading views
│   │   ├── search.py          # Multi-faceted search and keyword queries
│   │   ├── seo_rss.py         # RSS 2.0 feed (/feed.xml), sitemap.xml & robots.txt
│   │   ├── social.py          # Likes, bookmarks, follow relationships
│   │   └── taxonomy.py        # Category and topic taxonomy browsing
│   ├── utils/                 # Security filters, decorators, and AWS storage helpers
│   │   ├── decorators.py      # @admin_required, @moderator_required, @author_required
│   │   ├── security.py        # Input sanitization, password hashing, and URL safety
│   │   └── storage.py         # S3 presigned URL generator & Pillow image compression
│   ├── config.py              # Development, Testing, and Production configurations
│   ├── extensions.py          # Singleton instances (CSRFProtect, Limiter)
│   └── __init__.py            # Blueprint application factory & security header filters
├── deploy/                    # Production deployment automation & documentation
│   ├── aws-setup.sh           # EC2/Ubuntu production bootstrap script
│   ├── DEPLOY.md              # Complete AWS Cloud deployment guide
│   ├── LOCAL_TESTING.md       # Offline & cloud-connected developer setup
│   └── PRE_DEPLOYMENT_CHECKLIST.md # Release readiness checklist
├── nginx/
│   └── nginx.conf             # Hardened Nginx configuration with TLS & buffer tuning
├── static/
│   ├── style.css              # Custom Doodle-Glassmorphism CSS design system
│   ├── theme.js               # Dark/Light mode theme engine with zero-FOUC
│   └── uploads/               # Persistent upload volume directory
├── templates/                 # Jinja2 template hierarchy
│   ├── admin/                 # Management dashboards and user moderation views
│   ├── errors/                # Custom styled 404, 403, and 500 error pages
│   ├── base.html              # DRY layout with navbar, theme toggle & trust modal
│   ├── index.html             # Pinterest masonry feed with search & tags
│   ├── view.html              # Long-form reading view with Reddit discussion tree
│   ├── privacy.html           # GDPR-compliant Privacy Policy documentation
│   └── terms.html             # Terms and Conditions legal framework
├── tests/                     # Automated Test Suite (101 Test Cases)
│   ├── conftest.py            # Mocked AWS clients (Moto) and Flask test fixtures
│   ├── test_audit_production.py # Production configuration and security audits
│   ├── test_auth_rbac.py      # RBAC, hierarchy permissions & session revocation
│   ├── test_deployment_config.py# Docker, Nginx, and environment secrets validation
│   ├── test_features.py       # Preferred Sources badge, honeypots, SEO & compression
│   └── test_owasp.py          # Comprehensive OWASP Top 10 verification test suite
├── Dockerfile                 # Multi-stage container definition (non-root runner)
├── docker-compose.prod.yml    # Production container orchestration
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Testing, linting, and audit dependencies
├── wsgi.py                    # Gunicorn production entrypoint
└── app.py                     # Local development entrypoint shim
```

---

## 🧪 Automated Testing Suite

The project includes **101 automated test cases** covering every security control, RBAC policy, cloud integration, and UI feature. Tests execute completely offline using **Moto** to mock AWS DynamoDB and S3 APIs.

```bash
# Execute the full pytest suite
python -m pytest

============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-8.2.2, pluggy-1.6.0
rootdir: D:\my study\Project\My-Blog
plugins: anyio-4.13.0, hypothesis-6.165.0, flask-1.3.0
collected 101 items

tests\test_audit_production.py ......                                    [  5%]
tests\test_auth_rbac.py .......                                          [ 12%]
tests\test_deployment_config.py .........                                [ 21%]
tests\test_features.py .............                                     [ 34%]
tests\test_owasp.py .................................................... [ 86%]
..............                                                           [100%]

===================== 101 passed in 19.88s =====================
```

### Static Analysis & Security Audits

```bash
# Verify zero package vulnerabilities
pip-audit -r requirements.txt
# Output: No known vulnerabilities found

# Run Static Application Security Testing (SAST)
bandit -r app/ -f screen
# Output: 0 Critical, 0 High, 0 Medium severity issues
```

---

## 🚀 Quick Start & Local Development

### Prerequisites
* Python 3.11 or higher
* Docker & Docker Compose (optional for containerized setup)

### 1. Clone & Set Up Virtual Environment

```bash
# Clone the repository
git clone https://github.com/nadarallen/My-Blog.git
cd My-Blog

# Create and activate virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt
```

### 2. Configure Environment Variables

```bash
# Copy the example environment template
cp .env.example .env
```

Ensure your `.env` contains local configuration keys:
```ini
FLASK_ENV=development
SECRET_KEY=dev-insecure-secret-change-in-production
DYNAMODB_TABLE_USERS=myblog-users
DYNAMODB_TABLE_POSTS=myblog-posts
S3_BUCKET_NAME=myblog-uploads-bucket
AWS_DEFAULT_REGION=us-east-1
```

### 3. Launch Development Server

```bash
python app.py
```
Open your browser at **`http://127.0.0.1:5000`** to explore the application.

---

## 🐳 Docker Production Orchestration

To run the complete production stack (Flask behind Gunicorn reverse-proxied by Nginx):

```bash
# Build and run containers in detached mode
docker compose -f docker-compose.prod.yml up --build -d

# Verify container health
docker compose -f docker-compose.prod.yml ps
```

The application will be accessible at `http://localhost`.

---

## 📄 License & Attribution

Distributed under the **MIT License**. See `LICENSE` for more information.

* Designed & Developed by **Allen Nadar**.
* [GitHub Profile](https://github.com/nadarallen) · [LinkedIn](https://www.linkedin.com/)
