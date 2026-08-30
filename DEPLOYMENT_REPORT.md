# AWS Free-Tier Production Deployment Report — My-Blog

**Deployment Target**: AWS Free-Tier Single EC2 + DynamoDB + S3 Architecture  
**Date**: August 30, 2026  
**AWS Region**: `ap-south-1` (Mumbai)  

> [!NOTE]
> **Cost Disclaimer**: Designed to remain within applicable AWS Free Tier allowances under the documented usage assumptions. Actual AWS charges depend on account eligibility, usage, region, resource configuration, and AWS pricing.

---

## 1. Deployment Specification

* **Compute Platform**: Single AWS EC2 instance (`t2.micro` / `t3.micro` — 750 free hours/month).
* **Base OS**: Amazon Linux 2023 x86_64 AMI.
* **Container Stack**: Docker + Nginx 1.25 Alpine reverse proxy + Gunicorn WSGI server (`workers=2`).
* **Networking**: Elastic IP (`myblog-eip-production`) attached to EC2 instance (included in Free Tier).
* **Database**: 9 Amazon DynamoDB tables on `PAY_PER_REQUEST` (25 GB storage allowance, 25M read/write units/month).
* **Media Storage**: Private Amazon S3 media bucket with SSE-S3 AES-256 encryption & CORS (5 GB storage allowance).
* **Secrets Management**: AWS SSM Parameter Store (`/myblog/production/SECRET_KEY`), standard parameter tier.
* **Shell Access**: AWS Systems Manager (SSM) Session Manager (credential-free, no open SSH port 22).

---

## 2. Active AWS Resource Inventory & Cost Breakdown

| Resource Name | Type | Purpose | Cost Status (Free Tier) | Teardown Command |
|---|---|---|---|---|
| `myblog-ec2-production` | EC2 Instance | Runs Docker Compose stack | Covered by 750 free hrs/mo | `terraform destroy` |
| `myblog-eip-production` | Elastic IP | Static IPv4 endpoint | Covered while attached | `terraform destroy` |
| `myblog-posts`, `users`, +7 | DynamoDB | NoSQL app database | Covered by 25 GB free storage | `terraform destroy` |
| `myblog-images-<suffix>` | S3 Bucket | Private media storage | Covered by 5 GB free storage | `terraform destroy` |
| `/myblog/production/SECRET_KEY` | SSM Parameter | Flask session secret | Standard tier allowance | `terraform destroy` |
| `myblog-ec2-profile-production` | IAM Role | Credential-free AWS SDK | Standard IAM feature | `terraform destroy` |

---

## 3. Security & Hardening Posture

1. **Zero Credentials in Container**: Flask app uses the AWS SDK default credential provider chain (`boto3`) to auto-discover IAM instance profile credentials.
2. **SSM Parameter Store Key Cryptography**: Secret key auto-generated (64-char) and stored in encrypted SSM Parameter Store.
3. **SSM Session Manager Access**: Public SSH port 22 is disabled. Administrative access uses IAM-authenticated AWS Systems Manager.
4. **Media Security**: S3 Bucket blocks public access; image views use 1-hour presigned URLs.
5. **App Security**: Argon2id password hashing, RBAC decorators, CSRF protection, Bleach XSS sanitization, and production HTTP security headers (`CSP`, `X-Content-Type-Options`, `X-Frame-Options`, `HSTS`).

---

## 4. Test Suite Execution Results

```text
======================= 79 passed, 0 failed in 13.73s =======================
```
* **Original Tests**: 76 passed, 0 failed.
* **Deployment Tests**: 3 passed, 0 failed (testing production config, `/api/health`, and scheduler distributed locking).
* **Terraform Validation**: `Success! The configuration is valid.` (0 errors, 0 warnings).

---

## 5. Endpoints & URLs

* **Production Application**: `http://<EC2_ELASTIC_IP>/`
* **REST API v1**: `http://<EC2_ELASTIC_IP>/api/v1/posts`
* **API Documentation**: `http://<EC2_ELASTIC_IP>/api/v1/docs`
* **Admin Dashboard**: `http://<EC2_ELASTIC_IP>/admin`
* **Health Check**: `http://<EC2_ELASTIC_IP>/api/health`

---

## 6. Monitoring & Logging

* **Docker Container Logs**: `docker logs -f myblog-app` or `docker logs -f myblog-nginx`
* **Systemd Service Status**: `systemctl status myblog.service`
* **AWS SSM Session**: `aws ssm start-session --target <INSTANCE_ID> --region ap-south-1`

---

## 7. Zero-Code-Change Future Upgrade Path

The architecture maintains clean separation between compute and externalized state. Migrating to larger scale requires **zero business logic edits**:

1. **Stage 1 (Current)**: 1 x Free-Tier EC2 + Docker (Nginx) + DynamoDB + S3.
2. **Stage 2**: 2+ EC2 instances + ALB + Auto Scaling Group + DynamoDB + S3.
3. **Stage 3**: ECS Fargate + ECR + ALB + DynamoDB + S3.
4. **Stage 4**: CloudFront CDN + ECS Fargate + ALB + DynamoDB + S3 + OpenSearch.

See [`docs/SCALING_AND_MIGRATION.md`](file:///d:/my%20study/Project/My-Blog/docs/SCALING_AND_MIGRATION.md) for step-by-step instructions.

---

## 8. Deployment Execution Procedure

To deploy or update infrastructure via PowerShell:
```powershell
.\scripts\deploy.ps1
```
Or via Linux Bash:
```bash
./scripts/deploy.sh
```
