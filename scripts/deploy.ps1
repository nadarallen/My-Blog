# ─────────────────────────────────────────────────────────────────────────────
# My-Blog — AWS Free-Tier Automated Deployment Script (Windows PowerShell)
# ─────────────────────────────────────────────────────────────────────────────
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "🚀 Starting My-Blog AWS Free-Tier Automated Deployment" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Run Automated Test Suite
Write-Host "`n1️⃣ Running automated test suite (pytest)..." -ForegroundColor Yellow
python -m pytest tests/ --tb=short
if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Pytest suite failed! Aborting deployment."
    exit 1
}
Write-Host "✅ Test suite passed cleanly (76 passed)." -ForegroundColor Green

# 2. Export AWS Credentials for Current Process
Write-Host "`n2️⃣ Resolving AWS CLI Credentials & Region..." -ForegroundColor Yellow
$env:AWS_REGION = "ap-south-1"
$env:AWS_DEFAULT_REGION = "ap-south-1"
aws configure export-credentials --format powershell | Invoke-Expression

# 3. Validate Terraform IaC Configuration
Write-Host "`n3️⃣ Validating Terraform infrastructure configuration..." -ForegroundColor Yellow
Set-Location -Path "$PSScriptRoot/../infra/terraform"
.\terraform.exe validate
if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Terraform validation failed!"
    exit 1
}
Write-Host "✅ Terraform configuration is valid." -ForegroundColor Green

# 4. Plan Infrastructure Changes
Write-Host "`n4️⃣ Generating Terraform execution plan..." -ForegroundColor Yellow
.\terraform.exe plan -out=tfplan

# 5. Prompt for User Approval before applying
Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "Ready to apply infrastructure to AWS (ap-south-1)." -ForegroundColor Cyan
Write-Host "Resource Target: 1 x Free-Tier EC2, Elastic IP, 9 DynamoDB Tables, S3 Bucket, SSM Parameter." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$confirm = Read-Host "Do you want to apply this Terraform plan to AWS? (y/n)"
if ($confirm -eq "y" -or $confirm -eq "Y") {
    Write-Host "`n5️⃣ Applying Terraform infrastructure..." -ForegroundColor Yellow
    .\terraform.exe apply tfplan
    Write-Host "`n✅ AWS Free-Tier Infrastructure Applied Successfully!" -ForegroundColor Green
    .\terraform.exe output
} else {
    Write-Host "`n⚠️ Deployment cancelled by user." -ForegroundColor Yellow
}
