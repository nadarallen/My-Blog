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

variable "instance_type" {
  description = "Free-Tier eligible EC2 instance type (t2.micro / t3.micro)"
  type        = string
  default     = "t2.micro"
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

variable "domain_name" {
  description = "Custom domain name (optional)"
  type        = string
  default     = ""
}
