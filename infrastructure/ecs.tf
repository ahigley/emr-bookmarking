variable "launcher-cpu" {}
variable "launcher-memory" {}
variable "launcher-image" {}


resource "aws_ecs_cluster" "main-cluster" {
  name = "emr-bookmarking-cluster"
}

resource "aws_ecs_task_definition" "launcher" {
  count = var.launcher-image == "" ? 0 : 1
  family                   = "launcher"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.launcher-cpu
  memory                   = var.launcher-memory
  task_role_arn = aws_iam_role.ecs_task_launcher_role.arn
  execution_role_arn = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = <<DEFINITION
[
  {
    "cpu": ${var.launcher-cpu},
    "image": "${var.launcher-image}",
    "memory": ${var.launcher-memory},
    "name": "app",
    "networkMode": "awsvpc",
    "portMappings": [
      {
        "containerPort": 0,
        "hostPort": 3000
      }
    ]
  }
]
DEFINITION
}