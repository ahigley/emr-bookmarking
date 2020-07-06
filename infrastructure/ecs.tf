variable "launcher-cpu" {}
variable "launcher-memory" {}

resource "aws_ecs_cluster" "main-cluster" {
  name = "emr-bookmarking-cluster"
}

resource "aws_ecs_task_definition" "launcher" {
  family                   = "launcher"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.launcher-cpu
  memory                   = var.launcher-memory
  task_role_arn            = aws_iam_role.ecs_task_launcher_role.arn
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = <<DEFINITION
[
  {
    "cpu": ${var.launcher-cpu},
    "image": "${aws_ecr_repository.emr-launcher.repository_url}:latest",
    "memory": ${var.launcher-memory},
    "name": "launcher",
    "networkMode": "awsvpc",
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "emr-launcher-logs",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "emr-launcher-task"
      }
    }
  }
]
DEFINITION
}

resource "aws_cloudwatch_log_group" "log_group" {
  name = "emr-launcher-logs"
  retention_in_days = 14
}