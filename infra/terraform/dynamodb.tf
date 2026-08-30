# ─────────────────────────────────────────────────────────────────────────────
# Amazon DynamoDB Tables — On-Demand (Pay-Per-Request), PITR & SSE Enabled
# ─────────────────────────────────────────────────────────────────────────────

# 1. Posts Table
resource "aws_dynamodb_table" "posts" {
  name         = "${var.app_name}-posts"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "post_id"

  attribute {
    name = "post_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.app_name}-posts"
  }
}

# 2. Users Table
resource "aws_dynamodb_table" "users" {
  name         = "${var.app_name}-users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "username"

  attribute {
    name = "username"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.app_name}-users"
  }
}

# 3. Comments Table
resource "aws_dynamodb_table" "comments" {
  name         = "${var.app_name}-comments"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "comment_id"

  attribute {
    name = "comment_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.app_name}-comments"
  }
}

# 4. Interactions Table
resource "aws_dynamodb_table" "interactions" {
  name         = "${var.app_name}-interactions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "interaction_id"

  attribute {
    name = "interaction_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.app_name}-interactions"
  }
}

# 5. Notifications Table
resource "aws_dynamodb_table" "notifications" {
  name         = "${var.app_name}-notifications"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "notification_id"

  attribute {
    name = "notification_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.app_name}-notifications"
  }
}

# 6. Audit Logs Table
resource "aws_dynamodb_table" "audit" {
  name         = "${var.app_name}-audit"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "log_id"

  attribute {
    name = "log_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.app_name}-audit"
  }
}

# 7. Taxonomy (Categories/Tags) Table
resource "aws_dynamodb_table" "taxonomy" {
  name         = "${var.app_name}-taxonomy"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "item_id"

  attribute {
    name = "item_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.app_name}-taxonomy"
  }
}

# 8. Settings & Distributed Locks Table
resource "aws_dynamodb_table" "settings" {
  name         = "${var.app_name}-settings"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "key"

  attribute {
    name = "key"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.app_name}-settings"
  }
}

# 9. Reports Table
resource "aws_dynamodb_table" "reports" {
  name         = "${var.app_name}-reports"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "report_id"

  attribute {
    name = "report_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.app_name}-reports"
  }
}
