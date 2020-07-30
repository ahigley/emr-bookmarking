# EMR Roles
resource "aws_iam_role" "emr_ec2_role" {
  count = length(var.jobs)
  name  = join("_", list(lookup(var.jobs[count.index], "job_name"), "emr_ec2_role"))

  description          = format("The role to be used for EMR EC2 with job = %s", lookup(var.jobs[count.index], "job_name"))
  assume_role_policy   = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": ["elasticmapreduce.amazonaws.com", "ecs-tasks.amazonaws.com"]
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
  max_session_duration = 43200 # 12 hours
  tags = {
    Name = join("_", list(lookup(var.jobs[count.index], "job_name"), "emr_ec2_role"))
  }
}

resource "aws_iam_role_policy" "emr-ec2-role-s3-access" {
  count  = length(var.jobs)
  name   = join("-", list(lookup(var.jobs[count.index], "job_name"), "emr-ec2-role-s3-read-write"))
  role   = element(aws_iam_role.emr_ec2_role.*.id, count.index)
  policy = element(data.template_file.allow_read_write_s3_policy_file.*.rendered, count.index)
}

resource "aws_iam_instance_profile" "emr_ec2_instance_profile" {
  count = length(var.jobs)
  name  = join("_", list(lookup(var.jobs[count.index], "job_name"), "emr_ec2_role"))
  role  = element(aws_iam_role.emr_ec2_role.*.name, count.index)
}


resource "aws_iam_role_policy_attachment" "aws-managed-ec2-emr" {
  count      = length(var.jobs)
  role       = element(aws_iam_role.emr_ec2_role.*.id, count.index)
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceforEC2Role"
}

data "template_file" "emr_ec2_policy_file" {
  count    = length(var.jobs)
  template = file(format("%s/%s", "config", "emr_ec2_policy.json"))

  vars = {
    logs_bucket = element(aws_s3_bucket.emr-bucket.*.bucket, count.index)
  }
}

resource "aws_iam_role_policy" "inline_policy_emr_ec2_role" {
  count  = length(var.jobs)
  name   = join("-", list(lookup(var.jobs[count.index], "job_name"), "emr-ec2-base"))
  role   = element(aws_iam_role.emr_ec2_role.*.id, count.index)
  policy = element(data.template_file.emr_ec2_policy_file.*.rendered, count.index)
}

resource "aws_iam_role_policy" "inline_policy_emr_ec2_role_run_ecs" {
  count  = length(var.jobs)
  name   = join("-", list(lookup(var.jobs[count.index], "job_name"), "emr-ec2-run-ecs"))
  role   = element(aws_iam_role.emr_ec2_role.*.id, count.index)
  policy = element(data.template_file.allow_run_ecs_task.*.rendered, count.index)
}

data "template_file" "emr_ec2_access_lambda" {
  count    = length(var.jobs)
  template = file(format("%s/%s", "config", "allow-invoke-lambda.json"))
  vars = {
    lambda_function_arn = element(aws_lambda_function.emr_resolver_trigger.*.arn, count.index)
  }
}

resource "aws_iam_role_policy" "emr_ec2_role_run_lambda" {
  count  = length(var.jobs)
  name   = join("-", list(lookup(var.jobs[count.index], "job_name"), "emr-ec2-run-lambda"))
  role   = element(aws_iam_role.emr_ec2_role.*.id, count.index)
  policy = element(data.template_file.emr_ec2_access_lambda.*.rendered, count.index)
}

resource "aws_iam_role_policy_attachment" "aws-managed-emr-full-access-ec2" {
  count      = length(var.jobs)
  role       = element(aws_iam_role.emr_ec2_role.*.id, count.index)
  policy_arn = "arn:aws:iam::aws:policy/AmazonElasticMapReduceFullAccess"
}

resource "aws_iam_role_policy_attachment" "aws-managed-ec2-full-access-ec2-role" {
  count      = length(var.jobs)
  role       = element(aws_iam_role.emr_ec2_role.*.id, count.index)
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2FullAccess"
}

resource "aws_iam_role_policy_attachment" "aws-managed-s3-full-access-ec2-role" {
  count      = length(var.jobs)
  role       = element(aws_iam_role.emr_ec2_role.*.id, count.index)
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}


resource "aws_iam_role" "emr_service_role" {
  count = length(var.jobs)

  name = join("_", list(lookup(var.jobs[count.index], "job_name"), "emr_service_role"))

  description          = format("The role to be used for EMR service for job = %s", lookup(var.jobs[count.index], "job_name"))
  assume_role_policy   = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": ["elasticmapreduce.amazonaws.com", "s3.amazonaws.com"]
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
  max_session_duration = 43200 # 12 hours
  tags = {
    Name = join("_", list(lookup(var.jobs[count.index], "job_name"), "emr_service_role"))
  }
}

resource "aws_iam_role_policy" "emr-service-role-s3-access" {
  count  = length(var.jobs)
  name   = join("-", list(lookup(var.jobs[count.index], "job_name"), "emr-ec2-service-s3-read-write"))
  role   = element(aws_iam_role.emr_service_role.*.id, count.index)
  policy = element(data.template_file.allow_read_write_s3_policy_file.*.rendered, count.index)
}

resource "aws_iam_instance_profile" "emr_service_instance_profile" {
  count = length(var.jobs)
  name  = join("_", list(lookup(var.jobs[count.index], "job_name"), "emr_service_role"))
  role  = element(aws_iam_role.emr_service_role.*.name, count.index)
}

resource "aws_iam_role_policy_attachment" "aws-managed-s3-full-access-emr-role" {
  count      = length(var.jobs)
  role       = element(aws_iam_role.emr_service_role.*.id, count.index)
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "aws-managed-emr-service" {
  count      = length(var.jobs)
  role       = element(aws_iam_role.emr_service_role.*.id, count.index)
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceRole"
}

resource "aws_iam_role_policy_attachment" "aws-managed-emr-full-access-service" {
  count      = length(var.jobs)
  role       = element(aws_iam_role.emr_service_role.*.id, count.index)
  policy_arn = "arn:aws:iam::aws:policy/AmazonElasticMapReduceFullAccess"
}

resource "aws_iam_role_policy_attachment" "aws-managed-ec2-full-access" {
  count      = length(var.jobs)
  role       = element(aws_iam_role.emr_service_role.*.id, count.index)
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2FullAccess"
}

data "template_file" "emr_service_policy_file" {
  template = file(format("%s/%s", "config", "emr_service_policy.json"))
}

resource "aws_iam_role_policy" "inline_policy_emr_service_role" {
  count  = length(var.jobs)
  name   = join("-", list(lookup(var.jobs[count.index], "job_name"), "emr-service-base"))
  role   = element(aws_iam_role.emr_service_role.*.id, count.index)
  policy = data.template_file.emr_service_policy_file.rendered
}

# ECS Roles
resource "aws_iam_role" "ecs_task_execution_role" {
  count = length(var.jobs)
  name  = join("_", list(lookup(var.jobs[count.index], "job_name"), "ecs_task_execution_role"))

  description          = format("The role to be used for ECS Task Execution for job = %s", lookup(var.jobs[count.index], "job_name"))
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
    Name = join("_", list(lookup(var.jobs[count.index], "job_name"), "ecs_task_execution_role"))
  }
}

data "template_file" "ecs_task_execution_policy_file" {
  template = file(format("%s/%s", "config", "ecs_task_execution_policy.json"))
}

resource "aws_iam_role_policy" "ecs-task-execution-base-policy" {
  count  = length(var.jobs)
  name   = join("-", list(lookup(var.jobs[count.index], "job_name"), "ecs-task-execution-base"))
  role   = element(aws_iam_role.ecs_task_execution_role.*.id, count.index)
  policy = data.template_file.ecs_task_execution_policy_file.rendered
}

# Launcher
resource "aws_iam_role" "ecs_task_launcher_role" {
  count = length(var.jobs)
  name  = join("_", list(lookup(var.jobs[count.index], "job_name"), "ecs_launcher_task"))

  description = format("The role to be used for ECS Task for the emr launcher for job = %s",
  lookup(var.jobs[count.index], "job_name"))
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
    Name = join("_", list(lookup(var.jobs[count.index], "job_name"), "ecs_launcher_task"))
  }
}

resource "aws_iam_role_policy" "ecs-launcher-task-base" {
  count = length(var.jobs)
  name  = join("-", list(lookup(var.jobs[count.index], "job_name"), "ecs-launcher-task-base"))
  role  = element(aws_iam_role.ecs_task_launcher_role.*.id, count.index)
  # Badly named but we want this here also
  policy = data.template_file.ecs_task_execution_policy_file.rendered
}

data "template_file" "allow_read_write_s3_policy_file" {
  count    = length(var.jobs)
  template = file(format("%s/%s", "config", "allow_read_write_s3.json"))
  vars = {
    buckets = element(aws_s3_bucket.emr-bucket.*.bucket, count.index)
  }
}

resource "aws_iam_role_policy" "ecs-launcher-task-s3-access" {
  count  = length(var.jobs)
  name   = join("-", list(lookup(var.jobs[count.index], "job_name"), "ecs-launcher-task-s3-read-write"))
  role   = element(aws_iam_role.ecs_task_launcher_role.*.id, count.index)
  policy = element(data.template_file.allow_read_write_s3_policy_file.*.rendered, count.index)
}

resource "aws_iam_role_policy" "ecs-launcher-emr-access" {
  count = length(var.jobs)
  name  = join("-", list(lookup(var.jobs[count.index], "job_name"), "ecs-launcher-emr-access"))
  role  = element(aws_iam_role.ecs_task_launcher_role.*.id, count.index)
  # Use this one again so the task is able to launch the emr cluster
  policy = data.template_file.emr_service_policy_file.rendered
}

# Resolver
resource "aws_iam_role" "ecs_task_resolver_role" {
  count = length(var.jobs)
  name  = join("_", list(lookup(var.jobs[count.index], "job_name"), "ecs_resolver_task"))

  description = format("The role to be used for ECS Task for the emr resolver for job = %s",
  lookup(var.jobs[count.index], "job_name"))
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
    Name = join("_", list(lookup(var.jobs[count.index], "job_name"), "ecs_resolver_task"))
  }
}

resource "aws_iam_role_policy" "ecs-resolver-task-base" {
  count = length(var.jobs)
  name  = join("-", list(lookup(var.jobs[count.index], "job_name"), "ecs-resolver-task-base"))
  role  = element(aws_iam_role.ecs_task_launcher_role.*.id, count.index)
  # Badly named but we want this here also
  policy = data.template_file.ecs_task_execution_policy_file.rendered
}

resource "aws_iam_role_policy" "ecs-resolver-task-s3-access" {
  count  = length(var.jobs)
  name   = join("-", list(lookup(var.jobs[count.index], "job_name"), "ecs-resolver-task-s3-read-write"))
  role   = element(aws_iam_role.ecs_task_resolver_role.*.id, count.index)
  policy = element(data.template_file.allow_read_write_s3_policy_file.*.rendered, count.index)
}

data "template_file" "ecs-resolver-lambda-access-file" {
  count    = length(var.jobs)
  template = file(format("%s/%s", "config", "allow-invoke-lambda.json"))
  vars = {
    lambda_function_arn = element(aws_lambda_function.emr_launcher_trigger.*.arn, count.index)
  }
}

resource "aws_iam_role_policy" "ecs-resolver-lambda-access-policy" {
  count  = length(var.jobs)
  name   = join("-", list(lookup(var.jobs[count.index], "job_name"), "ecs-resolver-run-lambda"))
  role   = element(aws_iam_role.ecs_task_resolver_role.*.id, count.index)
  policy = element(data.template_file.ecs-resolver-lambda-access-file.*.rendered, count.index)
}

# Lambda Role
# Launcher trigger
resource "aws_iam_role" "launcher_trigger_lambda_role" {
  name = "launcher_trigger_lambda_role"
  tags = {
    Name = "launcher_trigger_lambda_role"
  }

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": ["lambda.amazonaws.com", "ecs-tasks.amazonaws.com"]
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

# Insert daily run cloudwatch event here if desired

data "template_file" "cloud_watch_full_access" {
  template = file("config/cloudwatch_full_access.json")
}

resource "aws_iam_role_policy" "cloud_watch_full_access" {
  name   = "cloudwatch_full_access"
  role   = aws_iam_role.launcher_trigger_lambda_role.id
  policy = data.template_file.cloud_watch_full_access.rendered
}


data "template_file" "lambda_vpc_execution_file" {
  template = file("config/lambda_vpc_execution_role.json")
}

resource "aws_iam_role_policy" "lambda_vpc_execution" {
  name   = "lambda_vpc_execution"
  role   = aws_iam_role.launcher_trigger_lambda_role.id
  policy = data.template_file.lambda_vpc_execution_file.rendered
}

# Ideally this would specify the specific task definition arn however the revision is always included which is
# problematic when ecs gets updated
data "template_file" "allow_run_ecs_task" {
  template = file("config/allow_run_ecs_task.json")
}

resource "aws_iam_role_policy" "allow_run_ecs_task" {
  name   = "allow_run_ecs_launcher_task"
  role   = aws_iam_role.launcher_trigger_lambda_role.id
  policy = data.template_file.allow_run_ecs_task.rendered
}

# Resolver trigger
resource "aws_iam_role" "resolver_trigger_lambda_role" {
  name = "resolver_trigger_lambda_role"
  tags = {
    Name = "resolver_trigger_lambda_role"
  }

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": ["lambda.amazonaws.com", "ecs-tasks.amazonaws.com"]
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "cloud_watch_full_access2" {
  name   = "cloudwatch_full_access_resolver"
  role   = aws_iam_role.resolver_trigger_lambda_role.id
  policy = data.template_file.cloud_watch_full_access.rendered
}

resource "aws_iam_role_policy" "lambda_vpc_execution2" {
  name   = "lambda_vpc_execution_resolver"
  role   = aws_iam_role.resolver_trigger_lambda_role.id
  policy = data.template_file.lambda_vpc_execution_file.rendered
}

resource "aws_iam_role_policy" "allow_run_ecs_task2" {
  name   = "allow_run_ecs_launcher_task_resolver"
  role   = aws_iam_role.resolver_trigger_lambda_role.id
  policy = data.template_file.allow_run_ecs_task.rendered
}

# Resolver trigger
resource "aws_iam_role" "file_tracking" {
  count = length(var.jobs)
  name  = join("_", list(lookup(var.jobs[count.index], "job_name"), "file_tracking_lambda_role"))
  tags = {
    Name = join("_", list(lookup(var.jobs[count.index], "job_name"), "file_tracking_lambda_role"))
  }

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": ["lambda.amazonaws.com", "s3.amazonaws.com", "dynamodb.amazonaws.com"]
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "cloud_watch_full_access3" {
  count  = length(var.jobs)
  name   = join("_", list(lookup(var.jobs[count.index], "job_name"), "cloudwatch_full_access_file_tracking"))
  role   = element(aws_iam_role.file_tracking.*.id, count.index)
  policy = data.template_file.cloud_watch_full_access.rendered
}

resource "aws_iam_role_policy" "lambda_vpc_execution3" {
  count  = length(var.jobs)
  name   = join("_", list(lookup(var.jobs[count.index], "job_name"), "lambda_vpc_execution_file_tracking"))
  role   = element(aws_iam_role.file_tracking.*.id, count.index)
  policy = data.template_file.lambda_vpc_execution_file.rendered
}

data "template_file" "allow_s3_read_only" {
  count    = length(var.jobs)
  template = file("config/allow_read_only_s3.json")
  vars = {
    buckets = element(aws_s3_bucket.emr-bucket.*.bucket, count.index)
  }
}

resource "aws_iam_role_policy" "file-tracking-s3-access" {
  count  = length(var.jobs)
  name   = join("-", list(lookup(var.jobs[count.index], "job_name"), "file-tracking-s3-read-only"))
  role   = element(aws_iam_role.file_tracking.*.id, count.index)
  policy = element(data.template_file.allow_s3_read_only.*.rendered, count.index)
}

data "template_file" "allow_dynamodb_table_access" {
  count = length(var.jobs)
  template = file("config/dynamodb-table-access.json")
  vars = {
    table = element(aws_dynamodb_table.file-tracking-table.*.name, count.index)
  }
}

resource "aws_iam_role_policy" "allow_dynamodb_access" {
  count = length(var.jobs)
  name = join("-", list(lookup(var.jobs[count.index], "job_name"), "dynamodb-access-file-tracking"))
  role = element(aws_iam_role.file_tracking.*.id, count.index)
  policy = element(data.template_file.allow_dynamodb_table_access.*.rendered, count.index)
}