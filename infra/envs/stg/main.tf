terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

locals {
  dummy = "actions-test"
  name = "${var.project}-${var.env}"
  tags = {
    Project = var.project
    Env     = var.env
  }
}

# VPC Module
module "vpc" {
  source = "../../modules/vpc"

  name                   = local.name
  vpc_cidr               = var.vpc_cidr
  azs                    = var.azs
  public_subnet_cidrs    = var.public_subnet_cidrs
  private_subnet_cidrs   = var.private_subnet_cidrs
  tags                   = local.tags
}

# Secrets Module
module "secrets" {
  source = "../../modules/secrets"

  name        = local.name
  db_username = var.db_username
  db_password = var.db_password
  tags        = local.tags
}

# RDS Module
module "rds" {
  source = "../../modules/rds"

  name                     = local.name
  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnet_ids
  allowed_security_groups  = [module.ecs.ecs_security_group_id]
  instance_class           = var.rds_instance_class
  allocated_storage        = var.rds_allocated_storage
  multi_az                 = var.rds_multi_az
  backup_retention_period  = var.rds_backup_retention_period
  skip_final_snapshot      = var.rds_skip_final_snapshot
  db_name                  = var.db_name
  db_username              = var.db_username
  db_password              = var.db_password
  tags                     = local.tags
}

# ECS Module
module "ecs" {
  source = "../../modules/ecs"

  name                    = local.name
  vpc_id                  = module.vpc.vpc_id
  public_subnet_ids       = module.vpc.public_subnet_ids
  region                  = var.region
  frontend_ecr_image      = var.frontend_ecr_image
  backend_ecr_image       = var.backend_ecr_image
  database_url            = "mysql+pymysql://${var.db_username}:${var.db_password}@${module.rds.endpoint}:3306/${var.db_name}?charset=utf8mb4"
  cpu                     = var.ecs_cpu
  memory                  = var.ecs_memory
  desired_count           = var.ecs_desired_count
  log_retention_days      = var.log_retention_days
  secrets_arns            = [module.secrets.secret_arn]
  tags                    = local.tags
}
