data "archive_file" "file_tracking" {
  type        = "zip"
  source_file = "../on_going_tracking_code/tracking.py"
  output_path = "/tmp/workflow_monitor.zip"
}

resource "aws_lambda_function" "on_going_file_tracking" {
  for_each      = var.job_tracked_prefixes
  function_name = "${each.value.job_name}-on-going-file-tracking"
  filename      = data.archive_file.file_tracking.output_path
  role          = "TODO"
  handler       = "tracking.lambda_handler"

  source_code_hash = data.archive_file.file_tracking.output_base64sha256

  runtime     = "python3.7"
  memory_size = 128
  timeout     = 300


  tags = {
    Name = "${each.value.job_name}-on-going-file-tracking"
  }
  environment {
    variables = {
      bucket     = each.value.bucket
      prefix     = each.value.prefix
      table_name = aws_dynamodb_table.file-tracking-table[each.key].name
    }
  }
}


resource "aws_lambda_permission" "allow_bucket" {
  for_each      = var.job_tracked_prefixes
  statement_id  = "${each.value.job_name}_tracking_lambda_allow_bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.on_going_file_tracking[each.key].function_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${each.value.bucket}"
}


resource "aws_s3_bucket_notification" "bucket_notification" {
  for_each = var.job_tracked_prefixes
  bucket   = each.value.bucket

  lambda_function {
    lambda_function_arn = aws_lambda_function.on_going_file_tracking[each.key].arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = each.value.prefix
  }

  depends_on = [aws_lambda_permission.allow_bucket]
}