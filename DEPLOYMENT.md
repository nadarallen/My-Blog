# 🚀 AWS Production Deployment Manual — My-Blog

This document describes the complete infrastructure architecture, Terraform IaC setup, container deployment workflow, zero-downtime rolling updates, and disaster recovery runbook for **My-Blog Platform**.

---

## 🏛️ Production AWS Architecture

```
                             Internet
                                │
                        HTTPS / HTTP (443 / 80)
                                ▼
               ┌─────────────────────────────────┐
               │    Application Load Balancer    │
               │   - HTTP to HTTPS redirection   │
               │   - /api/health target probe    │
               └────────────────┬────────────────┘
                                │
                     Private Subnets (VPC)
                                │
               ┌────────────────┴────────────────┐
               ▼                                 ▼
    ┌────────────────────┐            ┌────────────────────┐
    │  ECS Task (Node 1) │            │  ECS Task (Node 2) │
    │  - Gunicorn / WSGI │            │  - Gunicorn / WSGI │
    │  - Python 3.12     │            │  - Python 3.12     │
    │  - Non-root user   │            │  - Non-root user   │
    └──────────┬─────────┘            └──────────┬─────────┘
               │                                 │
               └────────────────┬────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Amazon DynamoDB  │  │    Amazon S3     │  │ Secrets Manager  │
│ (9 Tables)       │  │ (Private Media)  │  │ (FLASK_SECRET)   │
│ - Pay-per-request│  │ - Presigned URLs │  │ - Auto-rotation  │
│ - PITR Enabled   │  │ - SSE-S3 Encrypt │  └──────────────────┘
│ - SSE Encryption │  │ - Versioning     │
└──────────────────┘  └──────────────────┘
```

---

## 📦 Required AWS Services & Topology

| Service | Purpose | Configuration Details |
|---|---|---|
| **VPC & Networking** | Network Isolation | 2 Public Subnets (ALB), 2 Private Subnets (ECS Tasks), 1 NAT Gateway, 1 Internet Gateway. |
| **Amazon ECS (Fargate)** | Serverless Container Compute | 2+ Tasks running Python 3.12/Gunicorn WSGI on port 5000, 256 CPU, 512 MB RAM. |
| **Application Load Balancer** | Traffic Distribution & SSL | Public ALB listening on Port 80/443, routing to `/api/health` target group. |
| **Amazon ECR** | Container Image Registry | `myblog-app` repository with vulnerability scanning and 30-image lifecycle retention. |
| **Amazon DynamoDB** | Serverless NoSQL Database | 9 tables (`posts`, `users`, `comments`, `interactions`, `notifications`, `audit`, `taxonomy`, `settings`, `reports`) on `PAY_PER_REQUEST` billing mode with Point-in-Time Recovery (PITR). |
| **Amazon S3** | Object Media Storage | Private bucket with strict Block Public Access, SSE-S3 encryption, and presigned URLs. |
| **AWS Secrets Manager** | Secure Key Storage | Injected at task startup via IAM Execution Role (no secrets in Git or container images). |
| **Amazon CloudWatch** | Centralized Logging & Alarms | `/ecs/myblog-production` log group with 30-day retention and automated 5xx / Unhealthy Host alarms. |

---

## 🛠️ Step 1 — Infrastructure Provisioning (Terraform)

Navigate to the `infra/terraform/` directory:

```bash
cd infra/terraform

# 1. Initialize Terraform Providers
terraform init

# 2. Review Execution Plan
terraform plan -out=tfplan

# 3. Apply Infrastructure Changes
terraform apply tfplan
```

### Exported Outputs:
- `alb_dns_name`: Public URL to access your application (e.g. `http://myblog-alb-production-123456789.ap-south-1.elb.amazonaws.com`).
- `ecr_repository_url`: ECR registry endpoint for container pushes (e.g. `922930151841.dkr.ecr.ap-south-1.amazonaws.com/myblog-app`).
- `s3_media_bucket`: S3 bucket name.

---

## 🐳 Step 2 — Build & Push Container to Amazon ECR

```bash
# 1. Authenticate Docker with Amazon ECR
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin $(terraform output -raw ecr_repository_url)

# 2. Build and Tag the Container Image
docker build -t $(terraform output -raw ecr_repository_url):latest .

# 3. Push to ECR
docker push $(terraform output -raw ecr_repository_url):latest

# 4. Force ECS to deploy the latest image
aws ecs update-service --cluster myblog-cluster-production --service myblog-service-production --force-new-deployment --region ap-south-1
```

---

## 🔄 Step 3 — Continuous Deployment (GitHub Actions)

When code is pushed to `master` / `main`, GitHub Actions automatically:
1. Installs Python and runs all **76 automated tests**.
2. Halts deployment immediately if any test fails.
3. Builds the Docker image, tags it with the Git commit SHA, and pushes to ECR.
4. Updates the ECS task definition and performs a rolling update.
5. Verifies container health before terminating old instances.

### Required GitHub Repository Secrets:
- `AWS_ACCESS_KEY_ID`: IAM user/role deployment access key.
- `AWS_SECRET_ACCESS_KEY`: IAM user/role secret access key.

---

## 🚨 Disaster Recovery & Rollback Procedures

### Rollback Strategy (ECS)
If a new release encounters unexpected runtime issues:

```bash
# 1. List recent task definitions
aws ecs list-task-definitions --family-prefix myblog-task-production --sort DESC --region ap-south-1

# 2. Revert ECS service to the previous known good task definition revision (e.g. revision 3)
aws ecs update-service \
    --cluster myblog-cluster-production \
    --service myblog-service-production \
    --task-definition myblog-task-production:3 \
    --region ap-south-1
```

### Database Recovery (DynamoDB PITR)
Point-in-Time Recovery is enabled on all 9 tables, allowing 1-second granularity restoration for up to 35 days:

```bash
aws dynamodb restore-table-to-point-in-time \
    --source-table-name myblog-posts \
    --target-table-name myblog-posts-restored \
    --restore-date-time 2026-08-30T06:00:00.000Z \
    --region ap-south-1
```

---

## 📊 Monitoring & Operational Runbook

- **Live Logs**: `aws logs tail /ecs/myblog-production --follow --region ap-south-1`
- **Application Health Probe**: `http://<ALB_DNS_NAME>/api/health`
- **OpenAPI Documentation**: `http://<ALB_DNS_NAME>/api/v1/docs`
