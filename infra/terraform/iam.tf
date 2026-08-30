# ─────────────────────────────────────────────────────────────────────────────
# AWS IAM Roles for ECS (Execution Role & Task Role)
# ─────────────────────────────────────────────────────────────────────────────

# 1. ECS Task Execution Role (Pulling images from ECR, Writing logs to CloudWatch)
resource "aws_iam_role" "ecs_execution_role" {
  name = "${var.app_name}-ecs-execution-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Allow Execution Role to read secrets from Secrets Manager
resource "aws_iam_policy" "ecs_secrets_policy" {
  name        = "${var.app_name}-ecs-secrets-policy"
  description = "Allows ECS execution role to fetch application secrets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "kms:Decrypt"
        ]
        Resource = [
          aws_secretsmanager_secret.flask_secret_key.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_secrets_policy_attachment" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = aws_iam_policy.ecs_secrets_policy.arn
}

# 2. ECS Task Role (Runtime permissions for Flask App: DynamoDB + S3)
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.app_name}-ecs-task-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# Least-Privilege Scoped Policy for App Data Operations
resource "aws_iam_policy" "app_data_policy" {
  name        = "${var.app_name}-app-data-policy"
  description = "Allows least-privilege DynamoDB and S3 data operations"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DynamoDBTableAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:DescribeTable"
        ]
        Resource = [
          aws_dynamodb_table.posts.arn,
          aws_dynamodb_table.users.arn,
          aws_dynamodb_table.comments.arn,
          aws_dynamodb_table.interactions.arn,
          aws_dynamodb_table.notifications.arn,
          aws_dynamodb_table.audit.arn,
          aws_dynamodb_table.taxonomy.arn,
          aws_dynamodb_table.settings.arn,
          aws_dynamodb_table.reports.arn
        ]
      },
      {
        Sid    = "S3MediaAccess"
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:HeadBucket",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.media.arn,
          "${aws_s3_bucket.media.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_role_attachment" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.app_data_policy.arn
}
