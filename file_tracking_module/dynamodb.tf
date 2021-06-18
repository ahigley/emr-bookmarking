resource "aws_dynamodb_table" "file-tracking-table" {
  for_each     = var.job_tracked_prefixes
  name         = join("-", tolist([each.value.job_name, "file-tracking"]))
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "run_number"
  range_key    = "s3_path"

  attribute {
    name = "run_number"
    type = "S"
  }

  attribute {
    name = "s3_path"
    type = "S"
  }


  tags = {
    Name = join("-", tolist([each.value.job_name, "file-tracking"]))
  }
}

output "dynamodb_tracking_name" {
  value = { for k, v in var.job_tracked_prefixes : k => aws_dynamodb_table.file-tracking-table[k].name}
}