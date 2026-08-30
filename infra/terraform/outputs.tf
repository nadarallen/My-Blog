output "alb_dns_name" {
  description = "Public URL of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "ecr_repository_url" {
  description = "URL of the Amazon ECR container repository"
  value       = aws_ecr_repository.app.repository_url
}

output "s3_media_bucket" {
  description = "Name of the created private S3 media bucket"
  value       = aws_s3_bucket.media.id
}

output "ecs_cluster_name" {
  description = "Name of the ECS Cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "Name of the ECS Service"
  value       = aws_ecs_service.main.name
}

output "cloudwatch_log_group" {
  description = "CloudWatch Log Group name"
  value       = aws_cloudwatch_log_group.ecs.name
}
