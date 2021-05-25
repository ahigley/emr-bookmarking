resource "aws_lambda_function" "emr_launcher_trigger" {
  count = length(var.jobs)
  lifecycle {
    # Sadly we cannot ignore only certain environment variables. last_run and inputs should be ignored
    # But the rest it would be nice to maintain via terraform. Since these variables will be changed by the ecs
    # resolver job we have to ignore changes accross the board
    ignore_changes = [environment.0.variables]
  }
  function_name = join("_", tolist(["launcher_trigger_lambda", lookup(var.jobs[count.index], "job_name")]))
  filename      = "../emr_launcher/triggering_lambda/trigger_launcher.zip"
  role          = aws_iam_role.launcher_trigger_lambda_role.arn
  handler       = "trigger_launcher.lambda_handler"

  source_code_hash = filebase64sha256("../emr_launcher/triggering_lambda/trigger_launcher.zip")

  runtime     = "python3.7"
  memory_size = 128
  timeout     = 30


  tags = {
    Name = join("_", tolist(["launcher_trigger_lambda", lookup(var.jobs[count.index], "job_name")]))
  }
  environment {
    variables = {
      cluster  = aws_ecs_cluster.main-cluster.name
      subnets  = join(",", aws_subnet.public_subnet.*.id)
      inputs   = "input_manually"
      launcher = element(aws_ecs_task_definition.launcher.*.id, count.index)
      last_run = "changes"
    }
  }
}

resource "aws_lambda_function" "emr_resolver_trigger" {
  count = length(var.jobs)
  lifecycle {
    # Sadly we cannot ignore only certain environment variables. last_run and inputs should be ignored
    # But the rest it would be nice to maintain via terraform. Since these variables will be changed by the ecs
    # resolver job we have to ignore changes accross the board
    ignore_changes = [environment.0.variables]
  }
  function_name = join("_", tolist(["resolver_trigger_lambda", lookup(var.jobs[count.index], "job_name")]))
  filename      = "../emr_resolver/triggering_lambda/trigger_resolver.zip"
  role          = aws_iam_role.resolver_trigger_lambda_role.arn
  handler       = "trigger_resolver.lambda_handler"

  source_code_hash = filebase64sha256("../emr_resolver/triggering_lambda/trigger_resolver.zip")

  runtime     = "python3.7"
  memory_size = 128
  timeout     = 30


  tags = {
    Name = join("_", tolist(["resolver_trigger_lambda", lookup(var.jobs[count.index], "job_name")]))
  }
  environment {
    variables = {
      cluster           = aws_ecs_cluster.main-cluster.name
      subnets           = join(",", aws_subnet.public_subnet.*.id)
      resolver          = element(aws_ecs_task_definition.resolver.*.id, count.index)
      run_info          = "changes"
      temp_prefix       = "changes"
      final_prefix      = "changes"
      meta_data_prefix  = lookup(var.jobs[count.index], "meta_data_prefix")
      launcher_function = element(aws_lambda_function.emr_launcher_trigger.*.function_name, count.index)
    }
  }
}



resource "aws_lambda_function" "file_tracking" {
  lifecycle {
    # Sadly we cannot ignore only certain environment variables. last_run and inputs should be ignored
    # But the rest it would be nice to maintain via terraform. Since these variables will be changed by the ecs
    # resolver job we have to ignore changes accross the board
    ignore_changes = [environment]
  }
  count = length(local.job-prefix-association)
  function_name = join("_", tolist(["cdc_prefix_tracking",
    lookup(local.job-prefix-association[count.index], "job"),
  replace(lookup(local.job-prefix-association[count.index], "prefix"), "/", "")]))
  filename = "../cdc_tracking/cdc_tracking.zip"
  role     = lookup(local.job-lambda-role-association, lookup(local.job-prefix-association[count.index], "job"))
  handler  = "cdc_tracking.lambda_handler"

  source_code_hash = filebase64sha256("../cdc_tracking/cdc_tracking.zip")

  runtime     = "python3.7"
  memory_size = 128
  timeout     = 30


  tags = {
    Name = join("_", tolist(["cdc_prefix_tracking",
      lookup(local.job-prefix-association[count.index], "job"),
    replace(lookup(local.job-prefix-association[count.index], "prefix"), "/", "")]))
  }
  environment {
    variables = {
      prefix     = lookup(local.job-prefix-association[count.index], "prefix")
      run_number = "run_0"
      table_name = lookup(local.job-dynamodb-table-association,
      lookup(local.job-prefix-association[count.index], "job"))
    }
  }
}

resource "aws_lambda_permission" "allow_bucket" {
  count = length(local.job-prefix-association)
  statement_id = join("-", tolist([lookup(local.job-prefix-association[count.index], "job"),
          replace(lookup(local.job-prefix-association[count.index], "prefix"), "/", ""),
  "allow-bucket"]))
  action        = "lambda:InvokeFunction"
  function_name = element(aws_lambda_function.file_tracking.*.function_name, count.index)
  principal     = "s3.amazonaws.com"
  source_arn    = local.job-bucket-arn-association[lookup(local.job-prefix-association[count.index], "job")]
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  count  = length(local.job-prefix-association)
  bucket = lookup(local.job-bucket-id-association, lookup(local.job-prefix-association[count.index], "job"))

  lambda_function {
    lambda_function_arn = element(aws_lambda_function.file_tracking.*.arn, count.index)
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = lookup(local.job-prefix-association[count.index], "prefix")
  }

  depends_on = [aws_lambda_permission.allow_bucket]
}