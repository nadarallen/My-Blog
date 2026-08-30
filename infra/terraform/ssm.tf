# ─────────────────────────────────────────────────────────────────────────────
# AWS SSM Parameter Store — 100% Free Standard Parameter
# ─────────────────────────────────────────────────────────────────────────────

# Random 64-character secret key for Flask session cryptography
resource "random_password" "flask_secret" {
  length  = 64
  special = false
}

# Free SSM Parameter (Standard Tier)
resource "aws_ssm_parameter" "flask_secret_key" {
  name        = "/${var.app_name}/${var.environment}/SECRET_KEY"
  description = "Production SECRET_KEY for Flask session cryptography"
  type        = "SecureString"
  value       = random_password.flask_secret.result

  tags = {
    Name        = "${var.app_name}-secret-key"
    Environment = var.environment
  }
}
