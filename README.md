# ✍️ My-Blog — Cloud-Native Production Blog

[![Security Compliance](https://img.shields.io/badge/OWASP%20Compliance-A01--A10%20Verified-brightgreen.svg)](#-owasp-top-10-security-matrix)
[![Test Suite Status](https://img.shields.io/badge/Pytest%20Suite-63%20cases%20passed-blue.svg)](#-automated-testing-suite)
[![Architecture](https://img.shields.io/badge/AWS%20Infrastructure-EC2%20%7C%20S3%20%7C%20DynamoDB-orange.svg)](#-cloud-native-aws-architecture)

A highly secure, containerized, cloud-native full-stack blogging application. Re-architected from a vulnerable monolithic codebase into an enterprise-ready, modular system featuring an **AWS-native serverless data layer** and a custom **Doodle-Glassmorphism** aesthetic.

This project is built to demonstrate production-grade software development skills, security engineering compliance (OWASP Top 10), and cloud architecture integration.

---

## 🏗️ Cloud-Native AWS Architecture

The application has been migrated from local storage to a fully managed, serverless AWS infrastructure.

```
                  ┌────────────────────────────────────────┐
                  │              Your Browser              │
                  └───────────────────┬────────────────────┘
                                      │ HTTP (Port 80)
                                      ▼
                  ┌────────────────────────────────────────┐
                  │     AWS EC2 Instance (t2.micro)        │
                  │   └── Docker Compose Orchestration     │
                  │        ├── Nginx Reverse Proxy (:80)   │
                  │        └── Flask Gunicorn Server (:5000)│
                  └───────────────────┬────────────────────┘
                                      │
              ┌───────────────────────┴───────────────────────┐
              ▼ (Via IAM Role — No Keys)                      ▼ (Via IAM Role — No Keys)
┌───────────────────────────┐                   ┌───────────────────────────┐
│     Amazon S3 Bucket      │                   │    Amazon DynamoDB        │
│   (Private Object Store)  │                   │ (Managed NoSQL Database)  │
│  Serving Presigned URLs   │                   │  Tables: Users, Posts     │
└───────────────────────────┘                   └───────────────────────────┘
```

* **Amazon DynamoDB**: Serves as the high-velocity NoSQL store for users and blog posts, replacing local database dependencies. It utilizes `ConditionExpression` attributes to guarantee race-free, atomic write states.
* **Amazon S3**: Acts as the durable object store for cover image attachments. The bucket remains fully **private** (Block Public Access enabled); images are served using server-side generated **presigned URLs** with a 1-hour expiration limit.
* **AWS IAM Instance Profiles**: Eliminates hardcoded AWS API credentials on-disk. The EC2 instance assumes an IAM role (`myblog-ec2-role`) to request temporary credentials dynamically from AWS Metadata services.
* **Docker & Nginx**: The Flask app runs behind a non-root Gunicorn WSGI container, reverse-proxied by Nginx to optimize static asset delivery and hide backend system signatures.

---

## 🔄 Software Development Life Cycle (SDLC)

This project was built following a structured, industry-standard Software Development Life Cycle:

```
┌────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌────────────────┐
│   1. Audit &   │ ──► │  2. Architecture│ ──► │  3. Implement & │ ──► │  4. Automated   │ ──► │ 5. Container & │
│   Analysis     │     │     Design      │     │    Hardening    │     │   Validation    │     │   Deployment   │
└────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘     └────────────────┘
```

### 1. Requirements Analysis & Security Audit
We started by auditing the legacy application, identifying critical security loopholes (GET method deletions, lack of CSRF tokens, basic MD5/PBKDF2 password structures, user enumeration vulnerabilities, and bypassable file uploads). We defined target architectural requirements for migration to AWS.

### 2. Architecture & Database Design
We restructured the app from a monolithic script into an **Application Factory pattern** with isolated Flask Blueprints. We designed DynamoDB tables (`myblog-users` and `myblog-posts`) and mapped their partition keys for optimized queries.

### 3. Implementation & Security Hardening
Code was written incrementally:
* Transitioned the database driver to Boto3.
* Implemented Argon2id cryptography.
* Integrated global CSRF token filters.
* Created server-side magic byte inspection for file uploads to prevent script execution attacks.

### 4. Testing & Verification
We developed an automated pytest suite containing **63 mock-integrated cases** mapping directly to the OWASP Top 10 vulnerabilities. Tests run offline using `moto` to mock AWS S3/DynamoDB engines, ensuring absolute isolation.

### 5. Deployment Orchestration
We containerized the runtime environment using a secure multi-stage Docker build, set up local reverse-proxy networking, and drafted automated host-level bootstrap scripts.

---

## 🔐 OWASP Top 10 Security Matrix

| OWASP Risk Category | Vulnerability Identified | Production-Grade Mitigation Implemented |
|---|---|---|
| **A01:2021 – Broken Access Control** | Deletion routes executed via simple HTTP `GET` requests, allowing link-triggered deletion. | Restructured mutating routes to **POST-only**, protected by a single-session `@author_required` authorization decorator. |
| **A02:2021 – Cryptographic Failures** | Weak legacy password hashing; missing security flags on user cookies. | Migrated hashing to **Argon2id** (OWASP-recommended). Enforced `HttpOnly` and `SameSite=Lax` cookie flags. |
| **A03:2021 – Injection** | Stored XSS vulnerability in post titles and Markdown content. | Integrated **bleach** to strip HTML tags from inputs and sanitize rendered Markdown outputs against a strict allowlist. |
| **A04:2021 – Insecure Design** | User enumeration possible via differing login error messages and response times. | Unified login errors to generic messages and implemented timing-safe dummy password hashing for missing users. |
| **A05:2021 – Security Misconfiguration** | Debug mode exposed tracebacks; server version headers visible. | Disabled debug modes in production, hid Nginx server signatures, and wrote custom error templates for 404/500 faults. |
| **A07:2021 – Identification & Auth Failures** | Exposed to brute-force credential stuffing; session fixation risks. | Set up **Flask-Limiter** (5 logins/min per IP) and rotated session IDs completely on successful login. |
| **A08:2021 – Software & Data Integrity** | Spoofed file uploads (e.g. PHP files renamed to JPG) bypass extension checks. | Added **magic byte signature checks** to inspect file headers. Applied global **CSRF validation** to all POST forms. |
| **A10:2021 – Server-Side Request Forgery** | Open redirect vulnerability via unvalidated `?next=` parameter. | Added an URL parser that validates the `?next=` value, allowing only safe relative redirects. |

---

## 🎨 Premium Doodle-Glassmorphism UI

The frontend features a unique hand-drawn aesthetic designed for a professional portfolio:
* **Custom Typography**: Integrates Google Font's **Outfit** for readability and **Caveat** for hand-drawn details.
* **Modern CSS Stylesheet**: Leverages custom doodle borders (`border-doodle`), paper background patterns, glassmorphism overlays (`backdrop-filter: blur()`), and smooth wiggling hover states.
* **Live Markdown Preview**: A dual-pane tabbed editor inside `create.html` allows writers to preview rendered Markdown in real-time before publishing.

---

## 📂 Project Repository Map

```
My-Blog/
├── app/
│   ├── models/            # Data access layers (DynamoDB & Argon2id)
│   ├── routes/            # Flask Blueprints (API, auth, posts)
│   ├── utils/             # Helper modules (security filters, S3 storage, decorators)
│   ├── config.py          # Development & Production configs
│   ├── extensions.py      # Flask CSRF & Rate Limiter singletons
│   └── __init__.py        # Blueprint application factory
├── deploy/
│   ├── aws-setup.sh       # Ubuntu EC2 installation bootstrap script
│   ├── DEPLOY.md          # Step-by-step AWS deployment console guide
│   ├── LOCAL_TESTING.md   # Developer testing guide (Cloud / Offline)
│   └── PRE_DEPLOYMENT_CHECKLIST.md # Verification checklist before release
├── nginx/
│   └── nginx.conf         # Production Nginx reverse proxy configuration
├── static/
│   └── style.css          # Doodle glassmorphism stylesheet
├── templates/
│   ├── errors/            # Custom 404 & 500 pages
│   ├── base.html          # DRY base layout
│   ├── index.html         # Main feed grid with search
│   └── *.html             # Creation, edit, login, register templates
├── tests/
│   ├── conftest.py        # Moto mocked AWS client fixtures
│   └── test_owasp.py      # 63 security/vulnerability verification tests
├── Dockerfile             # Multi-stage production container build
├── docker-compose.prod.yml# Production container orchestration setup
├── requirements.txt       # Core production dependencies
├── requirements-dev.txt   # Local testing dependencies
├── wsgi.py                # Gunicorn entry point
└── app.py                 # Backwards-compatibility Flask shim
```

---

## 🧪 Quick Start & Local Testing

You can run the test suite and launch the application locally in minutes:

### 1. Setup Virtual Environment
```bash
# Clone the repository
git clone https://github.com/nadarallen/My-Blog.git
cd My-Blog

# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt
```

### 2. Run Security Tests
Verify all 63 OWASP Top 10 security test cases locally:
```bash
python -m pytest tests/test_owasp.py --tb=short
```

*For step-by-step details on running the application locally connected to AWS, or completely offline using `moto_server`, refer to the [Local Development Guide](deploy/LOCAL_TESTING.md).*

---

## 🚀 AWS Production Release

Before executing the deployment, ensure you complete the [Pre-Deployment Verification Checklist](deploy/PRE_DEPLOYMENT_CHECKLIST.md). For step-by-step console instructions, follow the [AWS Deployment Guide](deploy/DEPLOY.md).
