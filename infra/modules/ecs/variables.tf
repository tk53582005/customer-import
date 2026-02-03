variable "name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "region" {
  type = string
}

variable "frontend_ecr_image" {
  type = string
}

variable "backend_ecr_image" {
  type = string
}

variable "database_url" {
  type = string
}

variable "container_port_frontend" {
  type    = number
  default = 80
}

variable "container_port_backend" {
  type    = number
  default = 8000
}

variable "cpu" {
  type = number
}

variable "memory" {
  type = number
}

variable "desired_count" {
  type = number
}

variable "log_retention_days" {
  type    = number
  default = 14
}

variable "secrets_arns" {
  type    = list(string)
  default = null
}

variable "tags" {
  type    = map(string)
  default = {}
}
