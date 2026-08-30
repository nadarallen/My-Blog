#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# My-Blog — AWS Free-Tier Automated Deployment Script (Linux / macOS)
# ─────────────────────────────────────────────────────────────────────────────
set -e

echo "=========================================================="
echo "🚀 Starting My-Blog AWS Free-Tier Automated Deployment"
echo "=========================================================="

# 1. Run Automated Test Suite
echo -e "\n1️⃣ Running automated test suite (pytest)..."
python -m pytest tests/ --tb=short
echo "✅ Test suite passed cleanly."

# 2. Validate Terraform IaC
echo -e "\n2️⃣ Validating Terraform configuration..."
cd infra/terraform
terraform validate
echo "✅ Terraform configuration is valid."

# 3. Plan Infrastructure Changes
echo -e "\n3️⃣ Generating Terraform execution plan..."
terraform plan -out=tfplan

# 4. Apply Infrastructure
read -p "Do you want to apply this Terraform plan to AWS? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n4️⃣ Applying Terraform infrastructure..."
    terraform apply tfplan
    echo "✅ AWS Free-Tier Infrastructure Applied Successfully!"
    terraform output
else
    echo "⚠️ Deployment cancelled."
fi
