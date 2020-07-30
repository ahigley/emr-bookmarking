resource "aws_dynamodb_table" "file-tracking-table" {
  count        = length(var.jobs)
  name         = join("-", list(lookup(var.jobs[count.index], "job_name"), "file-tracking"))
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

  attribute {
    name = "prefix"
    type = "S"
  }
  # Not included here is an attribute 'file_type' which is either full or cdc

  local_secondary_index {
    name            = "prefix_index"
    range_key       = "prefix"
    projection_type = "ALL"
  }

  tags = {
    Name = join("-", list(lookup(var.jobs[count.index], "job_name"), "file-tracking"))
  }
}

resource "aws_dynamodb_table" "job-success" {
  count        = length(var.jobs)
  name         = join("-", list(lookup(var.jobs[count.index], "job_name"), "job-success"))
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "run_number"

  attribute {
    name = "run_number"
    type = "S"
  }
  # Not listed here is the attribute 'successful' which is a boolean

  tags = {
    Name = join("-", list(lookup(var.jobs[count.index], "job_name"), "job-success"))
  }
}