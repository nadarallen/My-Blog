# 🚀 My-Blog — AWS Production Deployment Guide

**Architecture**: Flask/Gunicorn + Nginx Proxy ──► AWS DynamoDB + AWS S3  
**AWS Services Showcase**: EC2, S3, DynamoDB, IAM Instance Profiles, Elastic IPs, Security Groups  
**Access**: `http://<your-elastic-ip>`  
**Estimated setup time**: ~25 minutes

---

## 🏗️ Architecture Design

```
Your Browser
      │ HTTP (Port 80)
      ▼
 AWS EC2 (Ubuntu 24.04, t2.micro)
   └── Docker Compose
        ├── Nginx (:80) ──► Reverse proxies / static assets
        └── Flask (:5000) ──► Gunicorn app server
             ├── S3 Bucket ──► Storage for image uploads (Presigned URLs)
             └── DynamoDB ───► Serverless managed NoSQL database
```

---

## 📋 Prerequisites

- An **AWS Account** (Free Tier eligible)
- Your blog code pushed to a **GitHub repository**
- SSH client (Terminal, PowerShell, or Git Bash)

---

## 🛠️ Step 1 — Create AWS S3 Bucket (Image Storage)

We store user-uploaded images in an S3 bucket. The bucket is kept completely **private**, and the app generates time-limited **presigned URLs** (1-hour expiry) to display images securely.

1. Open the **AWS S3 Console** → click **Create bucket**.
2. **Bucket name**: Enter a unique name (e.g., `myblog-images-12345`).
3. **AWS Region**: Select your region (e.g., `ap-south-1` Mumbai).
4. **Object Ownership**: Select **ACLs disabled (recommended)**.
5. **Block Public Access settings**: Keep **Block all public access** checked (this is highly secure).
6. **Default encryption**: Keep **Server-side encryption with Amazon S3 managed keys (SSE-S3)** enabled.
7. Click **Create bucket**.

---

## 🛠️ Step 2 — Create AWS DynamoDB Tables (NoSQL Database)

We use DynamoDB, AWS's serverless managed NoSQL database. It requires no server administration.

### Table 1: Users
1. Open the **AWS DynamoDB Console** → click **Create table**.
2. **Table name**: `myblog-users`
3. **Partition key**: `username` (Type: **String**)
4. **Table settings**: Keep **Default settings** checked.
5. Click **Create table**.

### Table 2: Posts
1. In DynamoDB Console → click **Create table**.
2. **Table name**: `myblog-posts`
3. **Partition key**: `post_id` (Type: **String**)
4. **Table settings**: Keep **Default settings** checked.
5. Click **Create table**.

---

## 🛠️ Step 3 — Create IAM Role for EC2 (Security Best Practice)

Instead of hardcoding AWS access keys in `.env` files (which is a major security risk), we attach an **IAM Role** directly to our EC2 instance. The EC2 instance will retrieve credentials automatically from AWS metadata.

1. Open the **AWS IAM Console** → in the left menu, click **Roles** → click **Create role**.
2. **Trusted entity type**: Select **AWS service**.
3. **Service or use case**: Select **EC2** from the dropdown → click **Next**.
4. **Permissions policies**: Search for and select the following permissions (or create an inline policy for least privilege):
   - Search `AmazonS3FullAccess` (or create a custom S3 policy allowing operations on your bucket)
   - Search `AmazonDynamoDBFullAccess` (or create a custom DynamoDB policy allowing access to your tables)
   
   *Note: For a production environment, always prefer scoped policies limiting access only to `myblog-images-12345` bucket and the two DynamoDB tables.*
5. Click **Next**.
6. **Role name**: Name it `myblog-ec2-role`.
7. Click **Create role**.

---

## 🛠️ Step 4 — Launch an EC2 Instance

1. Open the **AWS EC2 Console** → click **Launch instance**.
2. **Name**: `myblog-server`
3. **AMI (OS)**: Select **Ubuntu Server 24.04 LTS (HVM), SSD Volume Type** (Free Tier eligible).
4. **Instance type**: Select `t2.micro` (or `t3.micro` depending on region).
5. **Key pair**: Click **Create new key pair** → name it `myblog-key` → Key pair type: **RSA**, Private key file format: **.pem** → click **Create key pair** and download the file.
6. **Network settings**: Click **Edit**:
   - **Auto-assign public IP**: Enable
   - **Security Group**: Create a new security group named `myblog-sg`:
     
     | Type | Protocol | Port | Source | Description |
     |---|---|---|---|---|
     | SSH | TCP | 22 | **My IP** | Strict SSH access (restricts brute force) |
     | HTTP | TCP | 80 | **Anywhere (0.0.0.0/0)** | Public HTTP access for blog visitors |

7. **Advanced details**: Expand this section:
   - **IAM instance profile**: Select the `myblog-ec2-role` created in Step 3.
8. Click **Launch instance**.

---

## 🛠️ Step 5 — Allocate an Elastic IP (Static IP)

An Elastic IP is a persistent public IP address that remains associated with your server even if it is restarted.

1. In the EC2 Console left sidebar, click **Elastic IPs**.
2. Click **Allocate Elastic IP address** → click **Allocate**.
3. Select the allocated IP → click **Actions** → **Associate Elastic IP address**.
4. **Resource type**: Instance
5. **Instance**: Select your `myblog-server` instance.
6. Click **Associate**.
7. Note down your Elastic IP (e.g., `52.66.12.34`).

---

## 🛠️ Step 6 — SSH into EC2 & Install Docker

1. Open a terminal on your local machine and navigate to the directory where your `.pem` key file is saved.
2. Set correct permissions for the key:
   
   **For Linux/macOS:**
   ```bash
   chmod 400 myblog-key.pem
   ssh -i myblog-key.pem ubuntu@<your-elastic-ip>
   ```

   **For Windows (PowerShell):**
   ```powershell
   icacls .\myblog-key.pem /inheritance:r /grant:r "$($env:USERNAME):(R)"
   ssh -i .\myblog-key.pem ubuntu@<your-elastic-ip>
   ```

3. **Install Docker and Docker Compose on EC2:**
   Once logged into Ubuntu, install Docker using the convenient repository setup:
   ```bash
   # Update package database
   sudo apt-get update -y
   
   # Install Docker dependencies
   sudo apt-get install -y ca-certificates curl gnupg
   
   # Add Docker GPG key
   sudo install -m 0755 -d /etc/apt/keyrings
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
   sudo chmod a+r /etc/apt/keyrings/docker.gpg
   
   # Set up repository
   echo \
     "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
     $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
     sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
     
   # Install Docker Engine & Compose
   sudo apt-get update -y
   sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   
   # Add current user to docker group to run without sudo
   sudo usermod -aG docker ubuntu
   ```
4. **Log out and log back in** to apply the group memberships:
   ```bash
   exit
   ssh -i myblog-key.pem ubuntu@<your-elastic-ip>
   ```

---

## 🛠️ Step 7 — Clone Repository & Set Environment Variables

1. Clone your project repository into `/opt/myblog` (requires root/sudo for directory creation):
   ```bash
   sudo mkdir -p /opt/myblog
   sudo chown -R ubuntu:ubuntu /opt/myblog
   git clone https://github.com/YOUR_GITHUB_USERNAME/My-Blog.git /opt/myblog
   cd /opt/myblog
   ```

2. Create the production environment configuration:
   ```bash
   cp .env.production.example .env.production
   nano .env.production
   ```

3. Edit `.env.production`:
   - Generate a strong `SECRET_KEY` using the command on your local machine: `python -c "import secrets; print(secrets.token_hex(32))"`
   - Fill in your custom values:
     ```env
     SECRET_KEY=your_generated_64_char_hex
     ADMIN_USERNAME=admin
     FLASK_ENV=production
     FLASK_DEBUG=false
     
     AWS_REGION=ap-south-1              # Make sure this matches your resource region
     S3_BUCKET=myblog-images-12345      # Make sure this is your S3 bucket name
     DYNAMODB_POSTS_TABLE=myblog-posts  # Make sure this matches your table name
     DYNAMODB_USERS_TABLE=myblog-users  # Make sure this matches your table name
     ```
   - Press `Ctrl+O`, `Enter`, then `Ctrl+X` to save and exit.

---

## 🛠️ Step 8 — Launch the Blog Application

1. Deploy the stack in detached mode:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

2. Check running containers:
   ```bash
   docker compose -f docker-compose.prod.yml ps
   ```
   *Expected Output:*
   ```
   NAME             IMAGE             STATUS    PORTS
   myblog-app       myblog-app-app    running   5000/tcp
   myblog-nginx     nginx:1.25-alpine running   0.0.0.0:80->80/tcp
   ```

3. Check health and API logs:
   ```bash
   curl http://localhost/api/health
   ```
   *Expected JSON:*
   ```json
   {
     "status": "ok",
     "uptime_seconds": 15.2,
     "checks": {
       "dynamodb": "ok",
       "s3": "ok"
     }
   }
   ```

4. You're live! Access the blog by navigating to **`http://<your-elastic-ip>`** in your web browser.

---

## 📂 Common Maintenance Commands

```bash
# View real-time application logs
docker compose -f docker-compose.prod.yml logs -f app

# Pull updates from main branch and hot-rebuild Flask container
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build app

# Stop the server application
docker compose -f docker-compose.prod.yml down
```

---

## 🔒 Security Audit & Compliance Matrix

This deployment complies with industry-standard web safety practices:

- **A01:2021 – Broken Access Control**: Authentication and role-authorization checks are enforced server-side. Deletions are limited to POST-only requests with CSRF validation.
- **A02:2021 – Cryptographic Failures**: Passwords are saved with the state-of-the-art Argon2id hashing algorithm. Cookies are flagged as `HttpOnly` and `SameSite=Lax`.
- **A03:2021 – Injection**: Input sanitization via `bleach` and HTML output escaping inside Jinja2 templates prevent XSS.
- **A05:2021 – Security Misconfiguration**: Flask's debug mode is turned off (`FLASK_DEBUG=false`), Nginx hides version tokens, and default error handlers display neat, custom pages.
- **A07:2021 – Auth Failures**: Rate limits (5 attempts/min) protect user access against brute-force attacks. Session IDs are fully cleared and rotated upon login.
- **A08:2021 – Software Integrity**: Image uploads require extension matches AND magic byte validation to prevent upload exploitation. CSRF tokens guard all mutating actions.
- **Dynamic Access Security**: AWS IAM roles handle EC2 server authorization, eliminating access key variables from server storage.
