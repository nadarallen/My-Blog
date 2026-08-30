# Architectural Scaling & Migration Roadmap — My-Blog

This document provides a step-by-step technical guide for evolving **My-Blog** from a single Free-Tier EC2 instance up to a multi-instance containerized cloud architecture.

---

## Migration Stage Overview

```text
Stage 1 (Current) ──────► Stage 2 ─────────────────► Stage 3 ────────────────► Stage 4
1 x EC2 (Free-Tier)       2+ EC2 Instances           Amazon ECS Fargate          CloudFront CDN
Docker + Nginx            + ALB + Auto Scaling       + ALB                       + ALB + ECS Auto Scaling
DynamoDB + S3             DynamoDB + S3              DynamoDB + S3               DynamoDB + S3 + OpenSearch
```

---

## Stage 1 — Current Free-Tier Single EC2

* **Infrastructure**: 1 x EC2 `t2.micro` / `t3.micro`, Docker Compose (Nginx + Gunicorn), DynamoDB, S3, SSM Parameter Store.
* **Monthly Cost**: **$0.00** (AWS Free Tier).
* **Capacity**: Supports ~1,000–5,000 daily active readers.
* **Application Changes Required**: None.

---

## Stage 2 — High-Availability Multiple EC2 Instances

### When to Migrate
Migrate to Stage 2 when traffic exceeds 10,000 daily readers or high availability is required.

### Architectural Changes
1. Provision an **Application Load Balancer (ALB)** spanning 2 Availability Zones.
2. Launch 2 x EC2 instances in private subnets.
3. Configure an **EC2 Auto Scaling Group (ASG)** (min: 2, max: 10).
4. Update Nginx to run on ALB or proxy directly to Gunicorn.

### Why Application Code Code Changes = ZERO
* **Sessions**: Server-side session invalidation uses DynamoDB `session_version`.
* **Uploads**: Presigned URLs write directly to S3.
* **Scheduled Jobs**: `BackgroundScheduler` uses DynamoDB conditional locking (`_acquire_lock("publish_scheduled")`).
* **Estimated Cost**: ~$25–$35/month.

---

## Stage 3 — Serverless Container Platform (Amazon ECS Fargate)

### When to Migrate
Migrate to Stage 3 when container orchestration, zero-downtime rolling deployments, and serverless compute maintenance are preferred.

### Architectural Changes
1. Build and push production Docker image to **Amazon ECR** (`myblog-app`).
2. Deploy ECS Fargate Task Definition (0.25 vCPU, 512MB RAM) and ECS Service.
3. Attach ALB target group to ECS Service on port 5000.
4. Enable GitHub Actions automated workflow (`.github/workflows/deploy.yml`).

### Estimated Cost
* ~$30–$45/month.

---

## Stage 4 — Global Scale & Advanced Search

### Architectural Changes
1. Position **Amazon CloudFront** in front of ALB with static asset caching (`/static/*`) and dynamic API forwarding.
2. Introduce **Amazon SQS** for heavy asynchronous background jobs.
3. Integrate **Amazon OpenSearch** via `SearchService` interface for full-text search indexing.

### Estimated Cost
* ~$60–$120+/month depending on scale.
