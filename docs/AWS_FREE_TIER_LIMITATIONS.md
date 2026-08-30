# AWS Free Tier Limitations & Expiry Guide — My-Blog

> [!NOTE]
> **Cost Disclaimer**: Designed to remain within applicable AWS Free Tier allowances under the documented usage assumptions. Actual AWS charges depend on account eligibility, usage, region, resource configuration, and AWS pricing.

---

## 1. Free Tier Resource Allocation Map

| Resource | AWS Free Tier Allocation | Application Usage | Safety Margin |
|---|---|---|---|
| **EC2 `t2.micro` / `t3.micro`** | 750 hours/month | 1 instance running 24/7 = 720–744 hrs/mo | 6–30 hours buffer |
| **Elastic IP** | 1 IP included when attached to running EC2 | 1 Elastic IP attached to `myblog-ec2-production` | Covered within limits |
| **DynamoDB Storage** | 25 GB free | ~50 MB for blog posts, users, comments | 99.8% buffer |
| **DynamoDB Read/Write** | 25 RCU & WCU / 25M requests/mo | ~100,000 requests/month | 99.6% buffer |
| **S3 Media Storage** | 5 GB standard storage | ~500 MB image uploads | 90% buffer |
| **S3 Operations** | 20,000 GETs, 2,000 PUTs/mo | ~5,000 GETs, 200 PUTs/mo | 75% buffer |
| **SSM Parameter Store** | Standard parameters tier | 1 parameter (`/myblog/production/SECRET_KEY`) | Covered within limits |
| **Data Transfer Out** | 100 GB/month internet egress | ~5–10 GB/month | 90% buffer |

---

## 2. Operational Limitations of Stage 1 Architecture

1. **Single Point of Failure (Compute)**: If the single EC2 instance is terminated or restarted, the application will experience ~1–2 minutes of downtime while systemd/Docker auto-restarts.
2. **No Automated Load Balancer**: Nginx handles proxying directly on the EC2 instance without an AWS Application Load Balancer (ALB).
3. **No Automatic Horizontal Scaling**: Traffic spikes cannot automatically scale EC2 instances without transitioning to Stage 2 (ALB + EC2 Auto Scaling) or Stage 3 (ECS Fargate).
4. **Log Retention**: CloudWatch logs are capped at 5 GB/month ingestion to stay within log allocations.

---

## 3. What Changes When 12-Month Free Tier Expires?

After 12 months, AWS 12-Month Free Tier expires for EC2 and S3, but **Always Free** services remain within always-free allocations:

* **Always Free (Under Always Free Allocations)**:
  - DynamoDB (25 GB storage + 25M read/write units)
  - SSM Parameter Store (standard parameters)
  - Data Transfer Out (up to 100 GB/month)
  - AWS Systems Manager Session Manager

* **Paid Services Post-12 Months (Estimated Costs)**:
  - EC2 `t2.micro` / `t3.micro`: ~$8.50/month (or ~$3.50/mo with 1-Year Savings Plan).
  - S3 Storage (5 GB): ~$0.12/month.
  - Total Estimated Monthly Cost Post-Free-Tier: **~$3.60 to $8.60 / month**.
