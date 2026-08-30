# Amazon ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.app_name}-cluster-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.app_name}-cluster"
  }
}

# ECS Fargate Task Definition
resource "aws_ecs_task_definition" "app" {
  family                   = "${var.app_name}-task-${var.environment}"
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.fargate_cpu
  memory                   = var.fargate_memory

  container_definitions = jsonencode([
    {
      name      = "${var.app_name}-app"
      image     = "${aws_ecr_repository.app.repository_url}:latest"
      essential = true

      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "AWS_REGION", value = var.aws_region },
        { name = "FLASK_ENV", value = "production" },
        { name = "FLASK_DEBUG", value = "false" },
        { name = "ADMIN_USERNAME", value = var.admin_username },
        { name = "PORT", value = tostring(var.container_port) },
        { name = "S3_BUCKET", value = aws_s3_bucket.media.id },
        { name = "S3_PRESIGNED_EXPIRY", value = "3600" },
        { name = "DYNAMODB_POSTS_TABLE", value = aws_dynamodb_table.posts.name },
        { name = "DYNAMODB_USERS_TABLE", value = aws_dynamodb_table.users.name },
        { name = "DYNAMODB_COMMENTS_TABLE", value = aws_dynamodb_table.comments.name },
        { name = "DYNAMODB_INTERACTIONS_TABLE", value = aws_dynamodb_table.interactions.name },
        { name = "DYNAMODB_NOTIFICATIONS_TABLE", value = aws_dynamodb_table.notifications.name },
        { name = "DYNAMODB_AUDIT_TABLE", value = aws_dynamodb_table.audit.name },
        { name = "DYNAMODB_TAXONOMY_TABLE", value = aws_dynamodb_table.taxonomy.name },
        { name = "DYNAMODB_SETTINGS_TABLE", value = aws_dynamodb_table.settings.name },
        { name = "DYNAMODB_REPORTS_TABLE", value = aws_dynamodb_table.reports.name }
      ]

      secrets = [
        {
          name      = "SECRET_KEY"
          valueFrom = aws_secretsmanager_secret.flask_secret_key.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "app"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')\" || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])
}

# ECS Fargate Service
resource "aws_ecs_service" "main" {
  name            = "${var.app_name}-service-${var.environment}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.app_count
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets          = aws_subnet.private[*].id
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "${var.app_name}-app"
    container_port   = var.container_port
  }

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  depends_on = [
    aws_lb_listener.http,
    aws_iam_role_policy_attachment.ecs_execution_role_policy
  ]

  tags = {
    Name = "${var.app_name}-ecs-service"
  }
}
