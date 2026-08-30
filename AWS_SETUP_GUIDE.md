# ☁️ Complete AWS Production Environment Setup Guide

This guide walks you step-by-step through setting up the complete AWS infrastructure for **My-Blog Platform**.

---

## 🏗️ Architecture Overview

```
                      Internet
                         │
                    HTTPS / HTTP (443 / 80)
                         ▼
        ┌──────────────────────────────────┐
        │       AWS EC2 (Ubuntu 24.04)     │
        │  ┌────────────────────────────┐  │
        │  │   Nginx Reverse Proxy      │  │
        │  └─────────────┬──────────────┘  │
        │                ▼                 │
        │  ┌────────────────────────────┐  │
        │  │ Gunicorn + Flask App (:5000)│  │
        │  └─────────────┬──────────────┘  │
        │   IAM Instance Role (No keys!)   │
        └────────────────┼─────────────────┘
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
┌───────────────────┐           ┌───────────────────┐
│   Amazon S3       │           │  Amazon DynamoDB  │
│ (Private Bucket)  │           │ (9 NoSQL Tables)  │
│ - Presigned URLs  │           │ - Pay-per-request │
│ - SSE-S3 Encrypted│           │ - Distributed Lock│
└───────────────────┘           └───────────────────┘
```

---

## 📋 Prerequisites

1. An **AWS Account** with administrative access.
2. [AWS CLI](https://aws.amazon.com/cli/) installed on your local machine (or use **AWS CloudShell** directly in the AWS Console).
3. Git repository: `https://github.com/nadarallen/My-Blog.git`

---

## ⚡ Option A — 1-Click AWS CLI Setup (Fastest)

Open **AWS CloudShell** (or your local terminal with AWS CLI configured) and run:

```bash
# 1. Set your preferred AWS Region and Bucket Name
export AWS_REGION="ap-south-1"
export S3_BUCKET="myblog-images-$(aws sts get-caller-identity --query Account --output text)"

# 2. Create the Private S3 Bucket
aws s3api create-bucket \
    --bucket "$S3_BUCKET" \
    --region "$AWS_REGION" \
    --create-bucket-configuration LocationConstraint="$AWS_REGION"

aws s3api put-public-access-block \
    --bucket "$S3_BUCKET" \
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# 3. Create all 9 DynamoDB Tables (On-Demand Capacity)
tables=(
    "myblog-posts:post_id"
    "myblog-users:username"
    "myblog-comments:comment_id"
    "myblog-interactions:interaction_id"
    "myblog-notifications:notification_id"
    "myblog-audit:log_id"
    "myblog-taxonomy:item_id"
    "myblog-settings:key"
    "myblog-reports:report_id"
)

for entry in "${tables[@]}"; do
    IFS=":" read -r name pk <<< "$entry"
    echo "Creating table: $name with PK: $pk..."
    aws dynamodb create-table \
        --table-name "$name" \
        --attribute-definitions AttributeName="$pk",AttributeType=S \
        --key-schema AttributeName="$pk",KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "$AWS_REGION"
done
```

---

## 🛠️ Option B — Step-by-Step AWS Management Console Setup

### Step 1: Create the Private S3 Bucket

1. Open the [Amazon S3 Console](https://s3.console.aws.amazon.com/).
2. Click **Create bucket**.
3. **Bucket name**: `myblog-images-<your-unique-suffix>` (e.g. `myblog-images-nadarallen`).
4. **AWS Region**: Select your region (e.g., `ap-south-1` Mumbai).
5. **Object Ownership**: Select **ACLs disabled (recommended)**.
6. **Block Public Access**: Ensure **Block all public access** is **checked** ✅ (Presigned URLs will provide secure access).
7. **Default encryption**: Select **Server-side encryption with Amazon S3 managed keys (SSE-S3)**.
8. Click **Create bucket**.

---

### Step 2: Create DynamoDB Tables

Navigate to the [Amazon DynamoDB Console](https://console.aws.amazon.com/dynamodb/) → **Tables** → **Create table**.

Create each of the following 9 tables with **Pay-per-request (On-Demand)** capacity:

| # | Table Name | Partition Key (Primary Key) | Key Type | Capacity Mode |
|---|---|---|---|---|
| 1 | `myblog-posts` | `post_id` | String (`S`) | On-demand |
| 2 | `myblog-users` | `username` | String (`S`) | On-demand |
| 3 | `myblog-comments` | `comment_id` | String (`S`) | On-demand |
| 4 | `myblog-interactions` | `interaction_id` | String (`S`) | On-demand |
| 5 | `myblog-notifications` | `notification_id` | String (`S`) | On-demand |
| 6 | `myblog-audit` | `log_id` | String (`S`) | On-demand |
| 7 | `myblog-taxonomy` | `item_id` | String (`S`) | On-demand |
| 8 | `myblog-settings` | `key` | String (`S`) | On-demand |
| 9 | `myblog-reports` | `report_id` | String (`S`) | On-demand |

> [!TIP]
> Under **Table settings**, select **Customize settings** → choose **On-demand** billing mode so you only pay for requests with zero idle costs.

---

### Step 3: Create IAM Role for EC2 (Least Privilege)

Using IAM Instance Roles completely eliminates the need to store AWS Access Keys on your server.

1. Open the [AWS IAM Console](https://console.aws.amazon.com/iam/) → **Roles** → **Create role**.
2. **Trusted entity type**: **AWS service** → Use case: **EC2** → Click **Next**.
3. Click **Create policy** (opens a new tab), switch to **JSON**, and paste this least-privilege policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DynamoDBTableAccess",
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Query",
                "dynamodb:Scan",
                "dynamodb:DescribeTable"
            ],
            "Resource": [
                "arn:aws:dynamodb:*:*:table/myblog-*"
            ]
        },
        {
            "Sid": "S3ImageBucketAccess",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:HeadBucket",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::myblog-images-*",
                "arn:aws:s3:::myblog-images-*/*"
            ]
        }
    ]
}
```

4. Name the policy `MyBlog-App-Policy` and click **Create policy**.
5. Return to the Role creation tab, click the refresh button, search for `MyBlog-App-Policy`, check it, and click **Next**.
6. **Role name**: `myblog-ec2-role`.
7. Click **Create role**.

---

### Step 4: Launch EC2 Instance

1. Open the [Amazon EC2 Console](https://console.aws.amazon.com/ec2/) → **Launch instance**.
2. **Name**: `myblog-production-server`
3. **Application and OS Images**: **Ubuntu Server 24.04 LTS (HVM)** (64-bit x86).
4. **Instance type**: `t2.micro` or `t3.micro` (Free Tier eligible).
5. **Key pair**: Select or create a key pair (e.g. `myblog-key.pem`).
6. **Network settings** (Security Group):
   - Check **Allow SSH traffic** from **My IP** (Port 22).
   - Check **Allow HTTP traffic from the internet** (Port 80).
   - Check **Allow HTTPS traffic from the internet** (Port 443).
7. **Advanced details**:
   - **IAM instance profile**: Select `myblog-ec2-role`.
8. Click **Launch instance**.

---

### Step 5: Allocate and Associate Elastic IP (Static IP)

1. In EC2 Console left navigation, click **Network & Security** → **Elastic IPs**.
2. Click **Allocate Elastic IP address** → **Allocate**.
3. Select your newly allocated IP → Click **Actions** → **Associate Elastic IP address**.
4. **Instance**: Select `myblog-production-server`.
5. Click **Associate**. Note your public IP (e.g., `13.233.50.100`).

---

### Step 6: Connect to EC2 & Install Docker Engine

From your local machine (PowerShell or Terminal):

```bash
# Set permissions on private key (Linux/macOS)
chmod 400 myblog-key.pem
ssh -i myblog-key.pem ubuntu@<YOUR-ELASTIC-IP>

# Windows PowerShell:
# icacls .\myblog-key.pem /inheritance:r /grant:r "$($env:USERNAME):(R)"
# ssh -i .\myblog-key.pem ubuntu@<YOUR-ELASTIC-IP>
```

Run the following commands on the Ubuntu server:

```bash
# 1. Update system packages
sudo apt-get update -y && sudo apt-get upgrade -y

# 2. Install Docker & Docker Compose
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 3. Add ubuntu user to docker group
sudo usermod -aG docker ubuntu

# 4. Exit and reconnect to refresh group permissions
exit
```

Reconnect:
```bash
ssh -i myblog-key.pem ubuntu@<YOUR-ELASTIC-IP>
```

---

### Step 7: Clone Repository & Configure Environment

```bash
# 1. Create project folder and clone repo
sudo mkdir -p /opt/myblog
sudo chown -R ubuntu:ubuntu /opt/myblog
git clone https://github.com/nadarallen/My-Blog.git /opt/myblog
cd /opt/myblog

# 2. Create production .env file
nano .env.production
```

Paste the production configuration (replace with your S3 bucket name and generated secret key):

```env
# Flask Core
SECRET_KEY=9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a
ADMIN_USERNAME=admin
FLASK_ENV=production
FLASK_DEBUG=false

# AWS Configuration (Resolved via IAM Instance Role automatically)
AWS_REGION=ap-south-1
S3_BUCKET=myblog-images-nadarallen
S3_PRESIGNED_EXPIRY=3600

# DynamoDB Tables
DYNAMODB_POSTS_TABLE=myblog-posts
DYNAMODB_USERS_TABLE=myblog-users
DYNAMODB_COMMENTS_TABLE=myblog-comments
DYNAMODB_INTERACTIONS_TABLE=myblog-interactions
DYNAMODB_NOTIFICATIONS_TABLE=myblog-notifications
DYNAMODB_AUDIT_TABLE=myblog-audit
DYNAMODB_TAXONOMY_TABLE=myblog-taxonomy
DYNAMODB_SETTINGS_TABLE=myblog-settings
DYNAMODB_REPORTS_TABLE=myblog-reports
```

Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`).

---

### Step 8: Build and Launch Containers

```bash
# Start application containers in detached mode
docker compose -f docker-compose.prod.yml up -d --build
```

Verify running containers:
```bash
docker compose -f docker-compose.prod.yml ps
```

*Expected output:*
```text
NAME             IMAGE             STATUS          PORTS
myblog-app       myblog-app        Up 10 seconds   5000/tcp
myblog-nginx     nginx:1.25-alpine Up 10 seconds   0.0.0.0:80->80/tcp
```

Test the health probe:
```bash
curl http://localhost/api/health
```

*Expected JSON:*
```json
{
  "status": "ok",
  "uptime_seconds": 12.4,
  "checks": {
    "dynamodb": "ok",
    "s3": "ok"
  }
}
```

Open your browser and navigate to: **`http://<YOUR-ELASTIC-IP>`** 🎉

---

## 🔒 Optional: Custom Domain & Free SSL (HTTPS) with Certbot

If you have a domain name (e.g., `myblog.yourdomain.com` pointing to your Elastic IP):

```bash
# 1. Install Certbot
sudo apt-get install -y certbot

# 2. Stop temporary docker port 80 to obtain cert
docker compose -f docker-compose.prod.yml down

# 3. Obtain SSL certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# 4. Certificates will be stored in: /etc/letsencrypt/live/yourdomain.com/
```

Mount certificates into your Nginx configuration for automatic HTTPS encryption.

---

## 🛠️ Operational Commands Reference

```bash
# View real-time application logs
docker compose -f docker-compose.prod.yml logs -f app

# Pull latest code and restart
git pull origin master
docker compose -f docker-compose.prod.yml up -d --build app

# Stop the entire stack
docker compose -f docker-compose.prod.yml down
```
