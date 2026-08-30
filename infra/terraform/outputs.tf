output "ec2_public_ip" {
  description = "Public IP address of the EC2 Instance"
  value       = aws_instance.app.public_ip
}

output "elastic_ip" {
  description = "Public Elastic IP assigned to the application"
  value       = aws_eip.app.public_ip
}

output "s3_media_bucket" {
  description = "Name of the created private S3 media bucket"
  value       = aws_s3_bucket.media.id
}

output "ssm_secret_key_parameter" {
  description = "AWS SSM Parameter Store key name for SECRET_KEY"
  value       = aws_ssm_parameter.flask_secret_key.name
}

output "ec2_instance_id" {
  description = "AWS EC2 Instance ID"
  value       = aws_instance.app.id
}
