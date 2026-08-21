data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "app" {
  count                = var.enable_full_stack ? 1 : 0
  cidr_block           = "10.42.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "${local.name_prefix}-vpc" }
}

resource "aws_internet_gateway" "app" {
  count  = var.enable_full_stack ? 1 : 0
  vpc_id = aws_vpc.app[0].id
}

resource "aws_subnet" "public" {
  count                   = var.enable_full_stack ? 2 : 0
  vpc_id                  = aws_vpc.app[0].id
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  cidr_block              = cidrsubnet(aws_vpc.app[0].cidr_block, 8, count.index)
  map_public_ip_on_launch = false
  tags                    = { Name = "${local.name_prefix}-public-${count.index + 1}" }
}

resource "aws_subnet" "private_app" {
  count             = var.enable_full_stack ? 2 : 0
  vpc_id            = aws_vpc.app[0].id
  availability_zone = data.aws_availability_zones.available.names[count.index]
  cidr_block        = cidrsubnet(aws_vpc.app[0].cidr_block, 8, count.index + 10)
  tags              = { Name = "${local.name_prefix}-private-app-${count.index + 1}" }
}

resource "aws_subnet" "private_db" {
  count             = var.enable_full_stack ? 2 : 0
  vpc_id            = aws_vpc.app[0].id
  availability_zone = data.aws_availability_zones.available.names[count.index]
  cidr_block        = cidrsubnet(aws_vpc.app[0].cidr_block, 8, count.index + 20)
  tags              = { Name = "${local.name_prefix}-private-db-${count.index + 1}" }
}

resource "aws_eip" "nat" {
  count      = var.enable_full_stack ? 1 : 0
  domain     = "vpc"
  depends_on = [aws_internet_gateway.app]
}

resource "aws_nat_gateway" "app" {
  count         = var.enable_full_stack ? 1 : 0
  allocation_id = aws_eip.nat[0].id
  subnet_id     = aws_subnet.public[0].id
  depends_on    = [aws_internet_gateway.app]
}

resource "aws_route_table" "public" {
  count  = var.enable_full_stack ? 1 : 0
  vpc_id = aws_vpc.app[0].id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.app[0].id
  }
}

resource "aws_route_table_association" "public" {
  count          = var.enable_full_stack ? 2 : 0
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public[0].id
}

resource "aws_route_table" "private_app" {
  count  = var.enable_full_stack ? 1 : 0
  vpc_id = aws_vpc.app[0].id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.app[0].id
  }
}

resource "aws_route_table_association" "private_app" {
  count          = var.enable_full_stack ? 2 : 0
  subnet_id      = aws_subnet.private_app[count.index].id
  route_table_id = aws_route_table.private_app[0].id
}

resource "aws_security_group" "alb" {
  count       = var.enable_full_stack ? 1 : 0
  name        = "${local.name_prefix}-alb"
  description = "HTTPS from staff clients"
  vpc_id      = aws_vpc.app[0].id
  ingress {
    protocol    = "tcp"
    from_port   = 443
    to_port     = 443
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "api" {
  count       = var.enable_full_stack ? 1 : 0
  name        = "${local.name_prefix}-api"
  description = "API traffic from the load balancer only"
  vpc_id      = aws_vpc.app[0].id
  ingress {
    protocol        = "tcp"
    from_port       = 8080
    to_port         = 8080
    security_groups = [aws_security_group.alb[0].id]
  }
  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "database" {
  count       = var.enable_full_stack ? 1 : 0
  name        = "${local.name_prefix}-database"
  description = "PostgreSQL from the API only"
  vpc_id      = aws_vpc.app[0].id
  ingress {
    protocol        = "tcp"
    from_port       = 5432
    to_port         = 5432
    security_groups = [aws_security_group.api[0].id]
  }
}

resource "random_password" "database" {
  count            = var.enable_full_stack ? 1 : 0
  length           = 32
  special          = true
  override_special = "!#$%&*+-=?"
}

resource "aws_secretsmanager_secret" "database" {
  count                   = var.enable_full_stack ? 1 : 0
  name                    = "${local.name_prefix}/database"
  kms_key_id              = aws_kms_key.data.arn
  recovery_window_in_days = 30
}

resource "aws_secretsmanager_secret_version" "database" {
  count     = var.enable_full_stack ? 1 : 0
  secret_id = aws_secretsmanager_secret.database[0].id
  secret_string = jsonencode({
    username = "reporting_admin"
    password = random_password.database[0].result
    database = "reporting"
  })
}

resource "aws_db_subnet_group" "database" {
  count      = var.enable_full_stack ? 1 : 0
  name       = local.name_prefix
  subnet_ids = aws_subnet.private_db[*].id
}

resource "aws_db_instance" "workflow" {
  count                        = var.enable_full_stack ? 1 : 0
  identifier                   = local.name_prefix
  engine                       = "postgres"
  engine_version               = "17"
  instance_class               = "db.t4g.micro"
  allocated_storage            = 20
  max_allocated_storage        = 100
  storage_type                 = "gp3"
  storage_encrypted            = true
  kms_key_id                   = aws_kms_key.data.arn
  db_name                      = "reporting"
  username                     = "reporting_admin"
  password                     = random_password.database[0].result
  port                         = 5432
  db_subnet_group_name         = aws_db_subnet_group.database[0].name
  vpc_security_group_ids       = [aws_security_group.database[0].id]
  publicly_accessible          = false
  backup_retention_period      = 7
  copy_tags_to_snapshot        = true
  deletion_protection          = var.protect_data
  skip_final_snapshot          = !var.protect_data
  final_snapshot_identifier    = var.protect_data ? "${local.name_prefix}-final" : null
  auto_minor_version_upgrade   = true
  performance_insights_enabled = true
}

resource "aws_ecs_cluster" "api" {
  count = var.enable_full_stack ? 1 : 0
  name  = local.name_prefix
  setting {
    name  = "containerInsights"
    value = "enhanced"
  }
}

resource "aws_cloudwatch_log_group" "api" {
  count             = var.enable_full_stack ? 1 : 0
  name              = "/ecs/${local.name_prefix}"
  retention_in_days = 30
}

resource "aws_iam_role" "ecs_execution" {
  count = var.enable_full_stack ? 1 : 0
  name  = "${local.name_prefix}-ecs-execution"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "ecs-tasks.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  count      = var.enable_full_stack ? 1 : 0
  role       = aws_iam_role.ecs_execution[0].name
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "api_task" {
  count = var.enable_full_stack ? 1 : 0
  name  = "${local.name_prefix}-api-task"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "ecs-tasks.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_iam_role_policy" "api_task" {
  count = var.enable_full_stack ? 1 : 0
  role  = aws_iam_role.api_task[0].id
  name  = "reporting-control-plane"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Action    = "s3:ListBucket"
        Resource  = aws_s3_bucket.data.arn
        Condition = { StringLike = { "s3:prefix" = ["configuration/*", "incoming/*"] } }
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject"]
        Resource = ["${aws_s3_bucket.data.arn}/configuration/*", "${aws_s3_bucket.data.arn}/incoming/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["kms:Encrypt", "kms:GenerateDataKey"]
        Resource = aws_kms_key.data.arn
      }
    ]
  })
}

resource "aws_lb" "api" {
  count                      = var.enable_full_stack ? 1 : 0
  name                       = substr(local.name_prefix, 0, 32)
  internal                   = false
  load_balancer_type         = "application"
  security_groups            = [aws_security_group.alb[0].id]
  subnets                    = aws_subnet.public[*].id
  drop_invalid_header_fields = true
}

resource "aws_lb_target_group" "api" {
  count       = var.enable_full_stack ? 1 : 0
  name        = substr("${local.name_prefix}-api", 0, 32)
  port        = 8080
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.app[0].id
  health_check {
    path    = "/health"
    matcher = "200"
  }
}

resource "aws_lb_listener" "https" {
  count             = var.enable_full_stack ? 1 : 0
  load_balancer_arn = aws_lb.api[0].arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.alb_certificate_arn
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api[0].arn
  }
}

resource "aws_ecs_task_definition" "api" {
  count                    = var.enable_full_stack ? 1 : 0
  family                   = local.name_prefix
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_execution[0].arn
  task_role_arn            = aws_iam_role.api_task[0].arn
  runtime_platform {
    cpu_architecture        = "ARM64"
    operating_system_family = "LINUX"
  }

  container_definitions = jsonencode([{
    name                   = "api"
    image                  = var.api_image_uri
    essential              = true
    readonlyRootFilesystem = true
    portMappings           = [{ containerPort = 8080, hostPort = 8080, protocol = "tcp" }]
    environment = [
      { name = "APP_ENV", value = "production" },
      { name = "AWS_REGION", value = var.aws_region },
      { name = "DATA_BUCKET", value = aws_s3_bucket.data.id },
      { name = "KMS_KEY_ARN", value = aws_kms_key.data.arn },
      { name = "OIDC_ISSUER", value = var.oidc_issuer },
      { name = "OIDC_AUDIENCE", value = var.oidc_audience }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.api[0].name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "api"
      }
    }
  }])
}

resource "aws_ecs_service" "api" {
  count           = var.enable_full_stack ? 1 : 0
  name            = "api"
  cluster         = aws_ecs_cluster.api[0].id
  task_definition = aws_ecs_task_definition.api[0].arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private_app[*].id
    security_groups  = [aws_security_group.api[0].id]
    assign_public_ip = false
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.api[0].arn
    container_name   = "api"
    container_port   = 8080
  }
  depends_on = [aws_lb_listener.https]
}

output "api_url" {
  value = var.enable_full_stack ? "https://${aws_lb.api[0].dns_name}" : null
}

output "database_secret_arn" {
  value     = var.enable_full_stack ? aws_secretsmanager_secret.database[0].arn : null
  sensitive = true
}
