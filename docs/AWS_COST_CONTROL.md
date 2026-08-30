# AWS Cost Control & Guardrails Guide — My-Blog

> [!NOTE]
> **Cost Disclaimer**: Designed to remain within applicable AWS Free Tier allowances under the documented usage assumptions. Actual AWS charges depend on account eligibility, usage, region, resource configuration, and AWS pricing.

---

## 💰 Active AWS Resource Registry & Free Tier Limits

| Service | Resource Name | AWS Free Tier Allowance | Cost Risk / Triggers |
|---|---|---|---|
| **EC2** | `myblog-ec2-production` (`t2.micro` / `t3.micro`) | **750 hours/month** (1 instance 24/7) for 12 months. | Running multiple EC2 instances simultaneously. |
| **Elastic IP** | `myblog-eip-production` | **Included in Free Tier** while attached to running EC2. | Detached Elastic IP ($0.005/hr if EC2 stopped). |
| **DynamoDB** | 9 Tables (`myblog-*`) | **25 GB Storage** + **25M Read/Write Units/month** (PAY_PER_REQUEST or 25 WCU/RCU). | Unthrottled traffic spikes > 25M requests/month. |
| **S3** | `myblog-images-<suffix>` | **5 GB Storage** + **20,000 GET** + **2,000 PUT** requests/month. | Storing > 5 GB media or high-frequency uploads. |
| **SSM Parameter Store** | `/myblog/production/SECRET_KEY` | Standard parameter tier allowance. | Using Advanced parameters or high-throughput API. |
| **CloudWatch** | `/ecs/myblog-production` | **5 GB Log Ingestion** + **10 Custom Metrics** / month. | Unrestricted debug logging generating > 5 GB logs. |
| **AWS Systems Manager** | SSM Session Manager | Included shell access feature (replaces SSH port 22). | None. |

---

## 🚫 Avoided Paid AWS Services

To prevent unexpected billing, the following services have been **explicitly excluded** from the Stage 1 deployment:
* **NAT Gateway**: Saved ~$32/month (EC2 resides in public subnet with Elastic IP).
* **Application Load Balancer (ALB)**: Saved ~$18/month (Nginx on EC2 handles HTTP reverse proxying).
* **ECS Fargate Task Pricing**: Saved hourly compute charges.
* **AWS Secrets Manager**: Saved $0.40/secret/month (SSM Parameter Store used instead).
* **RDS / OpenSearch / ElastiCache**: Saved minimum $15–$50/month per instance.

---

## 📊 Billing Alarm Setup

Set up an automated AWS Billing Alarm to receive alerts if monthly charges exceed **$1.00**:

```bash
# Create an SNS topic for billing alerts
aws sns create-topic --name myblog-billing-alerts --region us-east-1

# Subscribe your email address to the topic
aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:922930151841:myblog-billing-alerts \
    --protocol email \
    --notification-endpoint your-email@example.com \
    --region us-east-1

# Create a CloudWatch Billing Alarm for $1.00 threshold
aws cloudwatch put-metric-alarm \
    --alarm-name "myblog-billing-alarm-1usd" \
    --metric-name "EstimatedCharges" \
    --namespace "AWS/Billing" \
    --statistic "Maximum" \
    --period 21600 \
    --threshold 1.0 \
    --comparison-operator "GreaterThanOrEqualToThreshold" \
    --evaluation-periods 1 \
    --alarm-actions arn:aws:sns:us-east-1:922930151841:myblog-billing-alerts \
    --dimensions Name=Currency,Value=USD \
    --region us-east-1
```

---

## 🧹 Complete Resource Teardown Runbook

If you wish to terminate all AWS resources to eliminate all potential costs:

```powershell
cd infra/terraform
powershell -Command "aws configure export-credentials --format powershell | Invoke-Expression; $env:AWS_REGION='ap-south-1'; .\terraform.exe destroy -auto-approve"
```
