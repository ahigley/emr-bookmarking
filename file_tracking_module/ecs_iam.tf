resource "aws_iam_role" "first_run_or_reset_task_role" {
  for_each           = var.job_tracked_prefixes
  name               = "${each.value.job_name}_first_run_or_reset_task_role"
  description        = "ECS Role for the first run or reset of job ${each.value.job_name}"
  assume_role_policy = data.aws_iam_policy_document.ecs_trusted_entities.json
}

data "aws_iam_policy_document" "allow_modify_dynamodb_file_tracking" {
  for_each = var.job_tracked_prefixes
  version  = "2012-10-17"
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:BatchGetItem",
      "dynamodb:ConditionCheckItem",
      "dynamodb:DeleteItem",
      "dynamodb:DescribeTable",
      "dynamodb:DescribeTimeToLive",
      "dynamodb:GetItem",
      "dynamodb:PartiQLDelete",
      "dynamodb:PartiQLInsert",
      "dynamodb:PartiQLSelect",
      "dynamodb:PartiQLUpdate",
      "dynamodb:PutItem",
      "dynamodb:Query",
      "dynamodb:UpdateItem"
    ]
    resources = [aws_dynamodb_table.file-tracking-table[each.key].arn]
  }

}

resource "aws_iam_role_policy" "allow_dynamodb_reset" {
  for_each = var.job_tracked_prefixes
  name     = "${each.value.job_name}_reset_allow_dynamodb"
  role     = aws_iam_role.first_run_or_reset_task_role[each.key].id
  policy   = data.aws_iam_policy_document.allow_modify_dynamodb_file_tracking.json
}

data "aws_iam_policy_document" "s3_read_only" {
  for_each = var.job_tracked_prefixes
  version  = "2012-10-17"
  statement {
    effect = "Allow"
    actions = [
      "s3:Get*",
      "s3:List*"
    ]
    resources = ["arn:aws:s3:::${each.value.bucket}/${each.value.prefix}",
    "arn:aws:s3:::${each.value.bucket}/${each.value.prefix}/*)"]
  }

}

resource "aws_iam_role_policy" "allow_s3_reset" {
  for_each = var.job_tracked_prefixes
  name     = "${each.value.job_name}_reset_allow_read_s3"
  role     = aws_iam_role.first_run_or_reset_task_role[each.key].id
  policy   = data.aws_iam_policy_document.s3_read_only.json
}


resource "aws_iam_role" "first_run_or_reset_execution_role" {
  for_each           = var.job_tracked_prefixes
  name               = "${each.value.job_name}_first_run_or_reset_excecution_role"
  description        = "ECS Role for the first run or reset of job ${each.value.job_name}"
  assume_role_policy = data.aws_iam_policy_document.ecs_trusted_entities.json
}

data "aws_iam_policy_document" "ecs_execution" {
  for_each = var.job_tracked_prefixes
  version  = "2012-10-17"
  statement {
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["*"]
  }

}

resource "aws_iam_role_policy" "allow_ecs_execution_reset" {
  for_each = var.job_tracked_prefixes
  name     = "${each.value.job_name}_reset_allow_ecs_execution"
  role     = aws_iam_role.first_run_or_reset_execution_role[each.key].id
  policy   = data.aws_iam_policy_document.ecs_execution.json
}

resource "aws_iam_role" "rewind_task_role" {
  for_each           = var.job_tracked_prefixes
  name               = "${each.value.job_name}_rewind_role"
  description        = "ECS Role for the rewinding of job ${each.value.job_name}"
  assume_role_policy = data.aws_iam_policy_document.ecs_trusted_entities.json
}

resource "aws_iam_role_policy" "allow_dynamodb_rewind" {
  for_each = var.job_tracked_prefixes
  name     = "${each.value.job_name}_rewind_allow_dynamodb"
  role     = aws_iam_role.rewind_task_role[each.key].id
  policy   = data.aws_iam_policy_document.allow_modify_dynamodb_file_tracking.json
}

data "aws_iam_policy_document" "ecs_trusted_entities" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type = "Service"
      identifiers = [
        "ecs-tasks.amazonaws.com"
      ]
    }
    effect = "Allow"
  }
}

resource "aws_iam_role" "rewind_execution_role" {
  for_each           = var.job_tracked_prefixes
  name               = "${each.value.job_name}_rewind_excecution_role"
  description        = "ECS Role for the rewind of job ${each.value.job_name}"
  assume_role_policy = data.aws_iam_policy_document.ecs_trusted_entities.json
}

resource "aws_iam_role_policy" "allow_ecs_execution_rewind" {
  for_each = var.job_tracked_prefixes
  name     = "${each.value.job_name}_rewind_allow_ecs_execution"
  role     = aws_iam_role.rewind_execution_role[each.key].id
  policy   = data.aws_iam_policy_document.ecs_execution.json
}