# ─────────────────────────────────────────────────────────────────────────────
# AWS EC2 Free-Tier Instance & Elastic IP Setup
# ─────────────────────────────────────────────────────────────────────────────

# Latest Amazon Linux 2023 AMI
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

# Free-Tier Single EC2 Instance
resource "aws_instance" "app" {
  ami                  = data.aws_ami.amazon_linux_2023.id
  instance_type        = var.instance_type
  iam_instance_profile = aws_iam_instance_profile.ec2.name
  vpc_security_group_ids = [aws_security_group.ec2.id]

  root_block_device {
    volume_size           = 8 # 8 GB GP3 (within 30 GB Free Tier limit)
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  # Cloud-init user data script to install Docker, Docker Compose, and launch app
  user_data = <<-EOF
              #!/bin/bash
              set -e

              # Update system & install Docker + git
              dnf update -y
              dnf install -y docker git
              systemctl enable --now docker
              usermod -aG docker ec2-user

              # Install Docker Compose plugin
              mkdir -p /usr/local/lib/docker/cli-plugins
              curl -SL https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose
              chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

              # Create app directory
              mkdir -p /opt/myblog
              cd /opt/myblog

              # Write systemd service for container auto-restart on EC2 reboot
              cat <<'SERVICE' > /etc/systemd/system/myblog.service
              [Unit]
              Description=My-Blog Container Application
              After=docker.service
              Requires=docker.service

              [Service]
              Type=oneshot
              RemainAfterExit=yes
              WorkingDirectory=/opt/myblog
              ExecStart=/usr/local/lib/docker/cli-plugins/docker-compose -f docker-compose.prod.yml up -d --build
              ExecStop=/usr/local/lib/docker/cli-plugins/docker-compose -f docker-compose.prod.yml down

              [Install]
              WantedBy=multi-user.target
              SERVICE

              systemctl daemon-reload
              systemctl enable myblog.service
              EOF

  tags = {
    Name        = "${var.app_name}-ec2-${var.environment}"
    Environment = var.environment
  }

  lifecycle {
    ignore_changes = [ami]
  }
}

# Elastic IP (100% Free while attached to a running EC2 instance)
resource "aws_eip" "app" {
  instance = aws_instance.app.id
  domain   = "vpc"

  tags = {
    Name        = "${var.app_name}-eip-${var.environment}"
    Environment = var.environment
  }
}
