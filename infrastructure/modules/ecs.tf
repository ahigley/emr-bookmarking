variable "launcher-cpu" {}
variable "launcher-memory" {}
variable resolver_cpu {}
variable "resolver_memory" {}

resource "aws_ecs_cluster" "main-cluster" {
  name = "emr-bookmarking-cluster"
}

resource "aws_ecs_task_definition" "launcher" {
  count                    = length(var.jobs)
  family                   = join("_", list(lookup(var.jobs[count.index], "job_name"), "launcher"))
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.launcher-cpu
  memory                   = var.launcher-memory
  task_role_arn            = element(aws_iam_role.ecs_task_launcher_role.*.arn, count.index)
  execution_role_arn       = element(aws_iam_role.ecs_task_execution_role.*.arn, count.index)

  container_definitions = <<DEFINITION
[
  {
    "cpu": ${var.launcher-cpu},
    "image": "${element(aws_ecr_repository.emr-launcher.*.repository_url, count.index)}:latest",
    "memory": ${var.launcher-memory},
    "name": "${lookup(var.jobs[count.index], "job_name")}_launcher",
    "networkMode": "awsvpc",
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "${join("_", list(lookup(var.jobs[count.index], "job_name"), "launcher"))}_emr_launcher_logs",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "${join("_", list(lookup(var.jobs[count.index], "job_name", "launcher")))}_emr_launcher_task"
      }
    }
  }
]
DEFINITION
}

resource "aws_cloudwatch_log_group" "log_group" {
  count             = length(var.jobs)
  name              = "${join("_", list(lookup(var.jobs[count.index], "job_name"), "launcher"))}_emr_launcher_logs"
  retention_in_days = 14
}

resource "aws_ecs_task_definition" "resolver" {
  count                    = length(var.jobs)
  family                   = join("_", list(lookup(var.jobs[count.index], "job_name"), "resolver"))
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  # Launcher and resolver should require roughly the same resources but
  cpu                      = var.resolver_cpu
  memory                   = var.resolver_memory
  task_role_arn            = element(aws_iam_role.ecs_task_resolver_role.*.arn, count.index)
  execution_role_arn       = element(aws_iam_role.ecs_task_execution_role.*.arn, count.index)

  container_definitions = <<DEFINITION
[
  {
    "cpu": ${var.resolver_cpu},
    "image": "${element(aws_ecr_repository.emr-resolver.*.repository_url, count.index)}:latest",
    "memory": ${var.resolver_memory},
    "name": "${lookup(var.jobs[count.index], "job_name")}_resolver",
    "networkMode": "awsvpc",
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "${join("_", list(lookup(var.jobs[count.index], "job_name"), "resolver"))}_emr_resolver_logs",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "${join("_", list(lookup(var.jobs[count.index], "job_name", "resolver")))}_emr_resolver_task"
      }
    }
  }
]
DEFINITION
}

resource "aws_cloudwatch_log_group" "log_group2" {
  count             = length(var.jobs)
  name              = "${join("_", list(lookup(var.jobs[count.index], "job_name"), "resolver"))}_emr_resolver_logs"
  retention_in_days = 14
}