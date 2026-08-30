# ─────────────────────────────────────────────────────────────────────────────
# AWS IAM Role & Instance Profile for EC2 (Least-Privilege Scoped Policy)
# ─────────────────────────────────────────────────────────────────────────────

# EC2 Assume Role
resource "aws_iam_role" "ec2_role" {
  name = "${var.app_name}-ec2-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# Attach AWS SSM Managed Instance Core policy (Enables credential-free SSM Session Manager shell)
resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Application Data & Secrets Policy
resource "aws_iam_policy" "app_data_policy" {
  name        = "${var.app_name}-app-data-policy-${var.environment}"
  description = "Allows least-privilege DynamoDB, S3, and SSM Parameter Store data operations"

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
      },
      {
        Sid    = "SSMParameterAccess"
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = [
          aws_ssm_parameter.flask_secret_key.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "app_data_attachment" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.app_data_policy.arn
}

# EC2 Instance Profile attached to EC2 resource
resource "aws_iam_instance_profile" "ec2" {
  name = "${var.app_name}-ec2-profile-${var.environment}"
  role = aws_iam_role.ec2_role.name
}
