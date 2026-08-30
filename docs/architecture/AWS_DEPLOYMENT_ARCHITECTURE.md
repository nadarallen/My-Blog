# Architecture Decision Record (ADR): AWS Free-Tier & Upgradeable Architecture

## Status
**Approved & Active**

---

## Context & Requirements

My-Blog is a production-hardened Flask application utilizing Amazon DynamoDB for all database state and Amazon S3 for private media storage. The application supports:
* Authentication & Argon2id password hashing
* Role-Based Access Control (RBAC) & 2FA support
* Multi-instance safe background scheduling with DynamoDB distributed locking
* Posts, drafts, comments, social interactions, notifications, search, analytics, and admin moderation
* 76 automated tests passing clean

The initial deployment must run on **AWS Free Tier** with minimal to zero monthly cost while avoiding architectural dead-ends.

---

## Decision: 2-Tier Modular AWS Architecture

We select a **Single EC2 + Docker (Nginx + Gunicorn) + DynamoDB + S3** deployment architecture for Stage 1.

### Stage 1 Topology (Free-Tier Production Deployment)

```text
                                  Internet
                                     │
                             HTTP 80 / HTTPS 443
                                     ▼
                        Amazon EC2 (t2/t3.micro)
                        Elastic IP Attached
               ┌─────────────────────────────────────────┐
               │ Docker Compose                          │
               │  ├── Nginx (Reverse Proxy + Static)     │
               │  └── Gunicorn + Flask Application       │
               └────────────────────┬────────────────────┘
                                    │
                                    │ AWS SDK Credential Chain
                                    │ (IAM Instance Profile)
                                    ▼
                 ┌──────────────────┴──────────────────┐
                 ▼                                     ▼
        Amazon DynamoDB                            Amazon S3
        (9 Tables + Locking)                    (Private Media)
```

---

## Key Design Principles

1. **Zero Persistent Disk State on EC2**: All user state, sessions, metadata, and uploads live in DynamoDB and S3. EC2 is treated as disposable compute.
2. **Credential-Free Container Code**: Python code uses `boto3` without hardcoded access keys. The AWS SDK default credential provider chain automatically discovers:
   - EC2 IAM Instance Profile (Stage 1)
   - ECS Task Role (Stage 3)
   - Lambda Execution Role (Stage 4)
3. **Multi-Instance Safe Scheduler**: Background scheduling uses DynamoDB conditional `put_item` locking on the `settings` table. Even if multiple EC2 or ECS instances run concurrently, tasks publish exactly once.
4. **Parameter Store Integration**: Secrets are read from AWS SSM Parameter Store (`/myblog/production/SECRET_KEY`), which is 100% free for standard parameters.

---

## Future Evolution Roadmap (Zero Application Code Changes)

```text
Stage 1 (Current)           Stage 2                     Stage 3                     Stage 4
Single EC2                  Multiple EC2                ECS / Fargate               CloudFront CDN
+ Docker (Nginx)            + ALB                       + ALB                       + ALB + ECS Auto Scaling
+ DynamoDB + S3             + DynamoDB + S3             + DynamoDB + S3             + DynamoDB + S3
```

Because business logic depends entirely on abstractions (`StorageService`, `EmailService`, `BackgroundScheduler`) and externalized state (DynamoDB & S3), migrating from Stage 1 to Stage 4 requires **zero application code modifications**.
