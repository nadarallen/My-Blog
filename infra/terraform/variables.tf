variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Deployment environment (production, staging)"
  type        = string
  default     = "production"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "myblog"
}

variable "admin_username" {
  description = "Admin username for the blog"
  type        = string
  default     = "admin"
}

variable "container_port" {
  description = "Port exposed by the Flask/Gunicorn container"
  type        = number
  default     = 5000
}

variable "fargate_cpu" {
  description = "Fargate task CPU units (256, 512, 1024, etc.)"
  type        = number
  default     = 256
}

variable "fargate_memory" {
  description = "Fargate task Memory in MB (512, 1024, 2048, etc.)"
  type        = number
  default     = 512
}

variable "app_count" {
  description = "Number of ECS tasks to run in parallel"
  type        = number
  default     = 2
}

variable "domain_name" {
  description = "Custom domain name (optional)"
  type        = string
  default     = ""
}
