# Security Group for Application Load Balancer
resource "aws_security_group" "alb" {
  name        = "${var.app_name}-alb-sg-${var.environment}"
  description = "Controls public inbound access to the ALB"
  vpc_id      = aws_vpc.main.id

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
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.app_name}-alb-sg"
  }
}

# Security Group for ECS Tasks (Isolated in Private Subnets)
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.app_name}-ecs-tasks-sg-${var.environment}"
  description = "Allows inbound traffic exclusively from the ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Inbound from ALB target group"
    from_port       = var.container_port
    to_port         = var.container_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.app_name}-ecs-tasks-sg"
  }
}
