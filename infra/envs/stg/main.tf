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
  name = "${var.project}-${var.env}"
  tags = {
    Project = var.project
    Env     = var.env
  }
}

# --------------------
# Network (VPC)
# --------------------
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = merge(local.tags, { Name = "${local.name}-vpc" })
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
  tags   = merge(local.tags, { Name = "${local.name}-igw" })
}

resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.azs[count.index]
  map_public_ip_on_launch = true
  tags = merge(local.tags, { Name = "${local.name}-public-${count.index + 1}" })
}

resource "aws_subnet" "private" {
  count             = length(var.private_subnet_cidrs)
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.azs[count.index]
  tags = merge(local.tags, { Name = "${local.name}-private-${count.index + 1}" })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id
  tags   = merge(local.tags, { Name = "${local.name}-rt-public" })
}

resource "aws_route" "public_inet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this.id
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.this.id
  tags   = merge(local.tags, { Name = "${local.name}-rt-private" })
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# --------------------
# Security Groups
# --------------------
resource "aws_security_group" "alb" {
  name        = "${local.name}-sg-alb"
  description = "ALB SG"
  vpc_id      = aws_vpc.this.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "to anywhere"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, { Name = "${local.name}-sg-alb" })
}

resource "aws_security_group" "ecs" {
  name        = "${local.name}-sg-ecs"
  description = "ECS tasks SG"
  vpc_id      = aws_vpc.this.id

  ingress {
    description     = "ALB to Frontend"
    from_port       = var.container_port_frontend
    to_port         = var.container_port_frontend
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  ingress {
    description     = "ALB to Backend"
    from_port       = var.container_port_backend
    to_port         = var.container_port_backend
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "to anywhere"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, { Name = "${local.name}-sg-ecs" })
}

resource "aws_security_group" "rds" {
  name        = "${local.name}-sg-rds"
  description = "RDS SG"
  vpc_id      = aws_vpc.this.id

  ingress {
    description     = "ECS to MySQL"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  egress {
    description = "to anywhere"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, { Name = "${local.name}-sg-rds" })
}

# --------------------
# RDS MySQL
# --------------------
resource "aws_db_subnet_group" "this" {
  name       = "${local.name}-db-subnet"
  subnet_ids = aws_subnet.private[*].id
  tags       = merge(local.tags, { Name = "${local.name}-db-subnet" })
}

resource "aws_db_instance" "this" {
  identifier             = "${local.name}-mysql"
  engine                 = "mysql"
  engine_version         = "8.0"
  instance_class         = "db.t4g.micro"
  allocated_storage      = 20
  db_name                = var.db_name
  username               = var.db_username
  password               = var.db_password
  port                   = 3306
  publicly_accessible    = false
  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  skip_final_snapshot    = true

  tags = merge(local.tags, { Name = "${local.name}-mysql" })
}

# --------------------
# ECS Cluster
# --------------------
resource "aws_ecs_cluster" "this" {
  name = "${local.name}-cluster"
  tags = local.tags
}

resource "aws_iam_role" "task_execution" {
  name = "${local.name}-ecs-task-exec"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "ecs-tasks.amazonaws.com" },
      Action = "sts:AssumeRole"
    }]
  })
  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "task_exec_attach" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${local.name}/frontend"
  retention_in_days = 14
  tags              = local.tags
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${local.name}/backend"
  retention_in_days = 14
  tags              = local.tags
}

resource "aws_ecs_task_definition" "this" {
  family                   = "${local.name}-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = tostring(var.cpu)
  memory                   = tostring(var.memory)
  execution_role_arn       = aws_iam_role.task_execution.arn

  container_definitions = jsonencode([
    {
      name      = "frontend",
      image     = var.frontend_ecr_image,
      essential = true,
      portMappings = [{
        containerPort = var.container_port_frontend,
        protocol      = "tcp"
      }],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          awslogs-group         = aws_cloudwatch_log_group.frontend.name,
          awslogs-region        = var.region,
          awslogs-stream-prefix = "ecs"
        }
      }
    },
    {
      name      = "backend",
      image     = var.backend_ecr_image,
      essential = true,
      portMappings = [{
        containerPort = var.container_port_backend,
        protocol      = "tcp"
      }],
      environment = [
        { name = "DOCKER_ENV", value = "true" },
        { name = "DATABASE_URL", value = "mysql+pymysql://${var.db_username}:${var.db_password}@${aws_db_instance.this.address}:3306/${var.db_name}?charset=utf8mb4" }
      ],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          awslogs-group         = aws_cloudwatch_log_group.backend.name,
          awslogs-region        = var.region,
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  tags = local.tags
}

# --------------------
# ALB
# --------------------
resource "aws_lb" "this" {
  name               = "${local.name}-alb"
  load_balancer_type = "application"
  subnets            = aws_subnet.public[*].id
  security_groups    = [aws_security_group.alb.id]
  tags               = local.tags
}

resource "aws_lb_target_group" "frontend" {
  name        = "${local.name}-tg-fe"
  port        = var.container_port_frontend
  protocol    = "HTTP"
  vpc_id      = aws_vpc.this.id
  target_type = "ip"

  health_check {
    path                = "/"
    matcher             = "200-399"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  tags = local.tags
}

resource "aws_lb_target_group" "backend" {
  name        = "${local.name}-tg-be"
  port        = var.container_port_backend
  protocol    = "HTTP"
  vpc_id      = aws_vpc.this.id
  target_type = "ip"

  health_check {
    path                = "/health"
    matcher             = "200-399"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  tags = local.tags
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

resource "aws_lb_listener_rule" "api" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}

# --------------------
# ECS Service
# --------------------
resource "aws_ecs_service" "this" {
  name            = "${local.name}-service"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.this.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = var.container_port_frontend
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = var.container_port_backend
  }

  depends_on = [aws_lb_listener.http]
  tags       = local.tags
}

# /health はbackendへ（ヘルスチェック用）
resource "aws_lb_listener_rule" "health" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 20

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }

  condition {
    path_pattern {
      values = ["/health"]
    }
  }
}
