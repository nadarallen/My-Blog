# 📋 Pre-Deployment Checklists — Production Verification

This checklists verify that all security, database, storage, and server configurations are secure and ready for AWS EC2 production deployment. Complete each section before running `docker compose up`.

---

## 🔐 1. Security & Secrets Checklist

- [ ] **Flask SECRET_KEY**: Generated a secure, high-entropy random key (do NOT use placeholder strings).
  - *Verify with command*: `python -c "import secrets; print(secrets.token_hex(32))"`
- [ ] **Flask Debug Mode**: Set `FLASK_DEBUG=false` and `FLASK_ENV=production` inside `.env.production`.
- [ ] **Session Expiry**: Set cookie settings inside `app/config.py` to secure values:
  - `SESSION_COOKIE_HTTPONLY = True`
  - `SESSION_COOKIE_SAMESITE = 'Lax'`
  - `SESSION_COOKIE_SECURE = True` *(Set to True if you configured HTTPS/SSL; keep False for pure Elastic IP HTTP).*
- [ ] **Admin Account**: Ensured the `ADMIN_USERNAME` variable in `.env.production` is set to your preferred username, and that username has been registered with a strong password.

---

## 🗄️ 2. AWS DynamoDB Database Checklist

- [ ] **Table Names**: Ensured `DYNAMODB_POSTS_TABLE` and `DYNAMODB_USERS_TABLE` variables inside `.env.production` match your actual tables in AWS.
- [ ] **Key Configuration**: Verify that your tables have been created with the correct Partition Keys (PK):
  - Table 1 (`myblog-users`): Primary Key must be `username` (Type: **String**).
  - Table 2 (`myblog-posts`): Primary Key must be `post_id` (Type: **String**).
- [ ] **Region Alignment**: Checked that `AWS_REGION` in `.env.production` matches the exact physical region where your tables are hosted (e.g., `ap-south-1`).

---

## 🪣 3. AWS S3 Storage Checklist

- [ ] **Bucket Name**: Verified `S3_BUCKET` in `.env.production` exactly matches the S3 bucket created.
- [ ] **Access Settings**: Double-checked S3 bucket has **Block all public access** enabled. *(Images are served via secure 1-hour presigned URLs generated server-side; the bucket should never be publicly readable).*
- [ ] **Encryption**: Default encryption is set to S3-managed keys (SSE-S3).

---

## 🌐 4. AWS IAM & EC2 Instance Checklist

- [ ] **IAM EC2 Role**: Created `myblog-ec2-role` in IAM Console containing policy access to:
  - DynamoDB tables (`myblog-users` and `myblog-posts`)
  - S3 bucket (`myblog-images-xxxx`)
- [ ] **EC2 Attachment**: Attached the `myblog-ec2-role` IAM instance profile to the running EC2 instance.
- [ ] **Security Group Rules**: Verified `myblog-sg` has the following firewall rules:
  - Inbound Port 80 (HTTP) allowed from **Anywhere (0.0.0.0/0)**.
  - Inbound Port 22 (SSH) allowed from **My IP ONLY** (protects against SSH brute forcing).
  - No database ports (like 27017 or 5432) are open to the internet.
- [ ] **Elastic IP**: Allocated and associated a static Elastic IP address to the EC2 instance.

---

## 🐳 5. Docker & Server Checklist

- [ ] **Git Sync**: Pushed the latest local commits to the remote GitHub repository.
- [ ] **Git Fetch**: Pulled the latest repository on the EC2 server inside `/opt/myblog`.
- [ ] **Docker Group Permissions**: Added `ubuntu` user to the `docker` group (`sudo usermod -aG docker ubuntu`) and re-logged in.
- [ ] **Configuration File**: Copied and populated `.env.production` inside `/opt/myblog` (ensure it is NOT committed to Git).
- [ ] **UFW Firewall Status**: Checked that UFW is enabled on EC2 and allows port 80/22 traffic:
  ```bash
  sudo ufw status
  ```

---

## 🧪 6. Final Health Check Verification

Once the stack is launched via `docker compose -f docker-compose.prod.yml up -d --build`, run the following commands on the EC2 host:

1. **Verify both containers are running:**
   ```bash
   docker compose -f docker-compose.prod.yml ps
   ```
2. **Verify API status matches AWS connectivity:**
   ```bash
   curl http://localhost/api/health
   ```
   *Expected Response (confirming DynamoDB and S3 are reachable from inside the container via IAM permissions):*
   ```json
   {
     "status": "ok",
     "uptime_seconds": 12.5,
     "checks": {
       "dynamodb": "ok",
       "s3": "ok"
     }
   }
   ```
3. **Inspect application logs for exceptions:**
   ```bash
   docker compose -f docker-compose.prod.yml logs -f app
   ```
