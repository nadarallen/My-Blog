# ─────────────────────────────────────────────────────────────────────────────
# Security Group for Free-Tier EC2 Instance
# ─────────────────────────────────────────────────────────────────────────────

# Default VPC lookup for single EC2 deployment
data "aws_vpc" "default" {
  default = true
}

resource "aws_security_group" "ec2" {
  name        = "${var.app_name}-ec2-sg-${var.environment}"
  description = "Controls public HTTP/HTTPS access to EC2 instance. SSH is managed via SSM Session Manager."
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "HTTP Public Access"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS Public Access"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Outbound Internet Traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.app_name}-ec2-sg"
    Environment = var.environment
  }
}
