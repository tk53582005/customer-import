output "alb_dns_name" {
  description = "ALB DNS name to access the application"
  value       = aws_lb.this.dns_name
}

output "rds_endpoint" {
  description = "RDS MySQL endpoint"
  value       = aws_db_instance.this.address
}
