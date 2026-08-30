terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment to enable S3 backend for remote state locking in production:
  # backend "s3" {
  #   bucket         = "myblog-terraform-state-922930151841"
  #   key            = "prod/terraform.tfstate"
  #   region         = "ap-south-1"
  #   dynamodb_table = "myblog-terraform-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "My-Blog"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
