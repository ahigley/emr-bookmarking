variable jobs {}
resource "aws_lambda_function" "emr_launcher_trigger" {
  count = length(var.jobs)
  lifecycle {
    # Sadly we cannot ignore only certain environment variables. last_run and inputs should be ignored
    # But the rest it would be nice to maintain via terraform. Since these variables will be changed by the ecs
    # resolver job we have to ignore changes accross the board
    ignore_changes = [environment.0.variables]
  }
  function_name = join("_", list("launcher_trigger_lambda", lookup(var.jobs[count.index], "job_name")))
  filename      = "../emr_launcher/triggering_lambda/trigger_launcher.zip"
  role          = aws_iam_role.launcher_trigger_lambda_role.arn
  handler       = "trigger_launcher.lambda_handler"

  source_code_hash = filebase64sha256("../emr_launcher/triggering_lambda/trigger_launcher.zip")

  runtime     = "python3.7"
  memory_size = 128
  timeout     = 30


  tags = {
    Name = join("_", list("launcher_trigger_lambda", lookup(var.jobs[count.index], "job_name")))
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
  function_name = join("_", list("resolver_trigger_lambda", lookup(var.jobs[count.index], "job_name")))
  filename      = "../emr_resolver/triggering_lambda/trigger_resolver.zip"
  role          = aws_iam_role.resolver_trigger_lambda_role.arn
  handler       = "trigger_resolver.lambda_handler"

  source_code_hash = filebase64sha256("../emr_resolver/triggering_lambda/trigger_resolver.zip")

  runtime     = "python3.7"
  memory_size = 128
  timeout     = 30


  tags = {
    Name = join("_", list("resolver_trigger_lambda", lookup(var.jobs[count.index], "job_name")))
  }
  environment {
    variables = {
      cluster  = aws_ecs_cluster.main-cluster.name
      subnets  = join(",", aws_subnet.public_subnet.*.id)
      resolver = element(aws_ecs_task_definition.resolver.*.id, count.index)
      run_info = "changes"
      temp_prefix = "changes"
      final_prefix = "changes"
      meta_data_prefix = lookup(var.jobs[count.index], "meta_data_prefix")
      launcher_function = element(aws_lambda_function.emr_launcher_trigger.*.function_name, count.index)
    }
  }
}