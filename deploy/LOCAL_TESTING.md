# 🧪 My-Blog — Local Development & Testing Guide

This guide explains how to set up and run the application locally for manual testing and development. You have two options:
1. **Cloud-Connected (Recommended)**: Connects your local Flask app to real AWS S3 and DynamoDB dev resources.
2. **Offline-Mocked (No AWS Cost)**: Runs a local mock AWS server (`moto_server`) simulating S3 and DynamoDB offline.

---

## 📋 General Setup

Before running either option, set up your Python environment:

```bash
# 1. Navigate to the project directory
cd "d:\my study\Project\My-Blog"

# 2. Create a virtual environment
python -m venv venv

# 3. Activate the virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# 4. Install all dependencies (production + development/testing)
pip install -r requirements.txt -r requirements-dev.txt
```

A local development configuration file `.env` has already been created for you in the project root.

---

## ⚡ Option 1 — Cloud-Connected Testing (Real AWS Dev Environment)

This option uses your actual AWS credentials to interact with dev tables and buckets in the cloud.

### 1. Configure local AWS CLI credentials
Install the [AWS CLI](https://aws.amazon.com/cli/) and run:
```bash
aws configure
```
Provide your dev AWS access key ID, secret access key, and set your default region to `ap-south-1`. Boto3 will automatically read these credentials when running the app locally.

### 2. Create Dev Resources
Ensure you have created S3 buckets and DynamoDB tables suffixed with `-dev` in your AWS account (similar to the instructions in `deploy/DEPLOY.md`).

### 3. Run the Development Server
```bash
# Set Flask entrypoint
$env:FLASK_APP="wsgi.py"
$env:FLASK_DEBUG="true"

# Start dev server
python app.py
```
Visit `http://127.0.0.1:5000` in your browser.

---

## 📴 Option 2 — Offline Mocked Testing (No AWS Account Needed)

You can run the entire AWS DynamoDB and S3 stack completely offline on your local machine using `moto_server` (which mimics AWS API endpoints).

### 1. Start the Moto Server
In a **separate** terminal window (with your virtual environment active):
```bash
# Starts a mock AWS server at http://localhost:5000
# S3 and DynamoDB mock endpoints will be active on that port
moto_server -p 5000
```
*(Alternatively, if you have Docker, you can run a Docker container for `motoserver/motor:latest` on port 5000).*

### 2. Configure AWS Mock client environment variables
Set fake credentials in your terminal so Boto3 thinks it is talking to AWS:
```powershell
$env:AWS_ACCESS_KEY_ID="mock-key"
$env:AWS_SECRET_ACCESS_KEY="mock-secret"
$env:AWS_DEFAULT_REGION="ap-south-1"
$env:FLASK_ENV="development"
$env:FLASK_DEBUG="true"
```

### 3. Create the Mock DynamoDB & S3 Tables
Before starting the app, run a quick initialization script to create the tables inside the running mock server. Create a file `init_mock_aws.py` and run it:

```python
import boto3

# Connect to local mock server
ddb = boto3.resource('dynamodb', endpoint_url='http://localhost:5000', region_name='ap-south-1')
s3 = boto3.client('s3', endpoint_url='http://localhost:5000', region_name='ap-south-1')

# Create tables
try:
    ddb.create_table(
        TableName='myblog-posts-dev',
        KeySchema=[{'AttributeName': 'post_id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'post_id', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    ddb.create_table(
        TableName='myblog-users-dev',
        KeySchema=[{'AttributeName': 'username', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'username', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    s3.create_bucket(
        Bucket='myblog-images-dev',
        CreateBucketConfiguration={'LocationConstraint': 'ap-south-1'}
    )
    print("Offline Mock AWS resources initialized successfully!")
except Exception as e:
    print(f"Error: {e}")
```

Run the initialization script:
```bash
python init_mock_aws.py
```

### 4. Run the Local App directed to the mock server
In `app/__init__.py`, when endpoint URLs are configured, you can direct Boto3 to use the local mock server endpoint. Since our conftest already handles mocking, you can also run your automated tests offline at any time!

---

## 🧪 Running Automated Tests

Run the security and functional test cases locally to verify security controls:

```bash
# Run pytest with warning capture and summary
python -m pytest tests/test_owasp.py --tb=short
```

*Expected output: `63 passed`.*
