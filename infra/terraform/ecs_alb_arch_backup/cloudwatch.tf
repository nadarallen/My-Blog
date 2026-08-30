# Centralized CloudWatch Log Group for Application Containers
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${var.app_name}-${var.environment}"
  retention_in_days = 30

  tags = {
    Name = "${var.app_name}-logs"
  }
}

# Alarm: Alert on high HTTP 5xx responses from ALB
resource "aws_cloudwatch_metric_alarm" "alb_5xx" {
  alarm_name          = "${var.app_name}-high-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Triggered when ALB returns more than 10 HTTP 5xx errors in a minute"

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
  }
}

# Alarm: Alert if any ECS tasks become unhealthy
resource "aws_cloudwatch_metric_alarm" "unhealthy_hosts" {
  alarm_name          = "${var.app_name}-unhealthy-tasks"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "UnHealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Maximum"
  threshold           = 0
  alarm_description   = "Triggered when ALB target group has unhealthy ECS tasks"

  dimensions = {
    TargetGroup  = aws_lb_target_group.app.arn_suffix
    LoadBalancer = aws_lb.main.arn_suffix
  }
}
