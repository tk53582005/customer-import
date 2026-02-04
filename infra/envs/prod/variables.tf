variable "project" {
  type = string
}

variable "env" {
  type = string
}

variable "region" {
  type = string
}

# VPC
variable "vpc_cidr" {
  type = string
}

variable "azs" {
  type = list(string)
}

variable "public_subnet_cidrs" {
  type = list(string)
}

variable "private_subnet_cidrs" {
  type = list(string)
}

# RDS
variable "db_name" {
  type = string
}

variable "db_username" {
  type = string
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "rds_instance_class" {
  type = string
}

variable "rds_allocated_storage" {
  type    = number
  default = 20
}

variable "rds_multi_az" {
  type    = bool
  default = false
}

variable "rds_backup_retention_period" {
  type    = number
  default = 7
}

variable "rds_skip_final_snapshot" {
  type    = bool
  default = false
}

# ECS
variable "frontend_ecr_image" {
  type = string
}

variable "backend_ecr_image" {
  type = string
}

variable "ecs_cpu" {
  type = number
}

variable "ecs_memory" {
  type = number
}

variable "ecs_desired_count" {
  type = number
}

variable "log_retention_days" {
  type    = number
  default = 30
}

# WAF
variable "waf_rate_limit" {
  type    = number
  default = 2000
  description = "WAF rate limit per 5 minutes per IP"
}
