# Random 32-byte secret key generation
resource "random_password" "flask_secret" {
  length  = 64
  special = false
}

# AWS Secrets Manager Secret
resource "aws_secretsmanager_secret" "flask_secret_key" {
  name                    = "${var.app_name}-secret-key-${var.environment}"
  description             = "Production SECRET_KEY for Flask session cryptography"
  recovery_window_in_days = 0

  tags = {
    Name = "${var.app_name}-secret-key"
  }
}

resource "aws_secretsmanager_secret_version" "flask_secret_key_val" {
  secret_id     = aws_secretsmanager_secret.flask_secret_key.id
  secret_string = random_password.flask_secret.result
}
