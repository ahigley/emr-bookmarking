# EMR Roles
resource "aws_iam_role" "emr_ec2_role" {
  name = "ahigley_emr_ec2_role"

  description          = "The role to be used for EMR EC2"
  assume_role_policy   = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "elasticmapreduce.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
  max_session_duration = 43200 # 12 hours
  tags = {
    Name = "ahigley_emr_ec2_role"
  }
}

data "template_file" "emr_ec2_policy_file" {
  template = file(format("%s/%s", "config", "emr_ec2_policy.json"))

  vars = {
    logs_bucket = aws_s3_bucket.emr-bucket.bucket
  }
}

resource "aws_iam_role_policy" "inline_policy_emr_ec2_role" {
  name   = "ahigley-emr-ec2-base"
  role   = aws_iam_role.emr_ec2_role.id
  policy = data.template_file.emr_ec2_policy_file.rendered
}

resource "aws_iam_role" "emr_service_role" {
  name = "ahigley_emr_service_role"

  description          = "The role to be used for EMR service"
  assume_role_policy   = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "elasticmapreduce.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
  max_session_duration = 43200 # 12 hours
  tags = {
    Name = "ahigley_emr_service_role"
  }
}

data "template_file" "emr_service_policy_file" {
  template = file(format("%s/%s", "config", "emr_service_policy.json"))
}

resource "aws_iam_role_policy" "inline_policy_emr_service_role" {
  name   = "ahigley-emr-service-base"
  role   = aws_iam_role.emr_service_role.id
  policy = data.template_file.emr_service_policy_file.rendered
}

# ECS Roles
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "ahigley_ecs_task_execution_role"

  description          = "The role to be used for ECS Task Execution"
  assume_role_policy   = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
  max_session_duration = 43200 # 12 hours
  tags = {
    Name = "ahigley_ecs_task_execution_role"
  }
}

data "template_file" "ecs_task_execution_policy_file" {
  template = file(format("%s/%s", "config", "ecs_task_execution_policy.json"))
}

resource "aws_iam_role_policy" "ecs-task-execution-base-policy" {
  name   = "ahigley-ecs-task-execution-base"
  role   = aws_iam_role.ecs_task_execution_role
  policy = data.template_file.ecs_task_execution_policy_file
}

resource "aws_iam_role" "ecs_task_launcher_role" {
  name = "ahigley_ecs_launcher_task"

  description          = "The role to be used for ECS Task for the emr launcher"
  assume_role_policy   = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
  max_session_duration = 43200 # 12 hours
  tags = {
    Name = "ahigley_ecs_launcher_task"
  }
}

resource "aws_iam_role_policy" "ecs-launcher-task-base" {
  name   = "ahigley-ecs-launcher-task-base"
  role   = aws_iam_role.ecs_task_launcher_role
  # Badly named but we want this here also
  policy = data.template_file.ecs_task_execution_policy_file
}

data "template_file" "allow_read_write_s3_policy_file" {
  template = file(format("%s/%s", "config", "allow_read_write_s3.json"))
  vars = {
    bucket = aws_s3_bucket.emr-bucket.bucket
  }
}

resource "aws_iam_role_policy" "ecs-launcher-task-s3-access" {
  name   = "ahigley-ecs-launcher-task-s3-read-wriote"
  role   = aws_iam_role.ecs_task_launcher_role
  policy = data.template_file.allow_read_write_s3_policy_file
}

resource "aws_iam_role_policy" "ecs-launcher-emr-access" {
  name   = "ahigley-ecs-launcher-emr-access"
  role   = aws_iam_role.ecs_task_launcher_role.id
  # Use this one again so the task is able to launch the emr cluster
  policy = data.template_file.emr_service_policy_file.rendered
}