locals {
  reset_log_group_names          = { for k, v in var.job_tracked_prefixes : k => "${v.job_name}_reset_or_start_logs" }
  reset_log_stream_prefix_names  = { for k, v in var.job_tracked_prefixes : k => "${v.job_name}_rest_or_start_task" }
  rewind_log_group_names         = { for k, v in var.job_tracked_prefixes : k => "${v.job_name}_rewind_logs" }
  rewind_log_stream_prefix_names = { for k, v in var.job_tracked_prefixes : k => "${v.job_name}_rewind_task" }
}


resource "aws_ecs_task_definition" "first_run_or_reset" {
  for_each                 = var.job_tracked_prefixes
  family                   = join("_", tolist([each.value.job_name, "rest_or_start"]))
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = each.value.reset_cpu
  memory                   = each.value.reset_memory
  task_role_arn            = aws_iam_role.first_run_or_reset_task_role[each.key].arn
  execution_role_arn       = aws_iam_role.first_run_or_reset_execution_role[each.key].arn

  container_definitions = <<DEFINITION
[
  {
    "cpu": ${each.value.reset_cpu},
    "image": "${aws_ecr_repository.first_run_or_reset[each.key].repository_url}:latest",
    "memory": ${each.value.reset_memory},
    "name": "${each.value.job_name}_reset_or_start",
    "environment": [
      {"prefix": "${each.value.prefix}", "bucket": "${each.value.bucket}"
        "table_name": "${aws_dynamodb_table.file-tracking-table[each.key].name}",
        "max_count": "${each.value.max_count}"
    ],
    "networkMode": "awsvpc",
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "${local.reset_log_group_names[each.key]}",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "${local.reset_log_stream_prefix_names[each.key]}"
      }
    }
  }
]
DEFINITION
}

resource "aws_cloudwatch_log_group" "reset_log_group" {
  for_each          = var.job_tracked_prefixes
  name              = local.reset_log_group_names[each.key]
  retention_in_days = 14
}

resource "aws_ecs_task_definition" "rewinder" {
  for_each                 = var.job_tracked_prefixes
  family                   = "${each.value.job_name}_rewinder"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  # Launcher and resolver should require roughly the same resources but
  cpu                = each.value.rewind_cpu
  memory             = each.value.rewind_memory
  task_role_arn      = aws_iam_role.rewind_task_role[each.key].arn
  execution_role_arn = aws_iam_role.rewind_execution_role[each.key].arn
  # prefix and table name are known but you must pass rewind_to as an environment variable when running the task
  container_definitions = <<DEFINITION
[
  {
    "cpu": ${each.value.rewind_cpu},
    "image": "${aws_ecr_repository.job_rewind[each.key].repository_url}:latest",
    "memory": ${each.value.reset_memory},
    "name": "${each.value.job_name}_rewinder",
    "environment": [
      {"prefix": "${each.value.prefix}", "bucket": "${each.value.bucket}"
        "table_name": "${aws_dynamodb_table.file-tracking-table[each.key].name}",
        "max_count": "${each.value.max_count}"
    ],
    "networkMode": "awsvpc",
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "${local.rewind_log_group_names[each.key]}",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "${local.rewind_log_stream_prefix_names[each.key]}"
      }
    }
  }
]
DEFINITION
}

resource "aws_cloudwatch_log_group" "rewind_log_group" {
  for_each          = var.job_tracked_prefixes
  name              = local.rewind_log_group_names[each.key]
  retention_in_days = 14
}