variable "project" { 
  type = string 
}

variable "env" { 
  type = string 
}

variable "region" { 
  type = string 
}

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

variable "frontend_ecr_image" { 
  type = string 
}

variable "backend_ecr_image" { 
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

variable "desired_count" { 
  type    = number
  default = 1
}

variable "cpu" { 
  type    = number
  default = 512
}

variable "memory" { 
  type    = number
  default = 1024
}
