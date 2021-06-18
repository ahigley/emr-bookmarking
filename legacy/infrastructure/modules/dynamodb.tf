resource "aws_dynamodb_table" "file-tracking-table" {
  count        = length(var.jobs)
  name         = join("-", tolist([lookup(var.jobs[count.index], "job_name"), "file-tracking"]))
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
    Name = join("-", tolist([lookup(var.jobs[count.index], "job_name"), "file-tracking"]))
  }
}

resource "aws_dynamodb_table" "job-success" {
  count        = length(var.jobs)
  name         = join("-", tolist([lookup(var.jobs[count.index], "job_name"), "job-success"]))
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "run_number"

  attribute {
    name = "run_number"
    type = "S"
  }
  # Not listed here is the attribute 'successful' which is a boolean

  tags = {
    Name = join("-", tolist([lookup(var.jobs[count.index], "job_name"), "job-success"]))
  }
}

resource "aws_dynamodb_table" "job-resolution" {
  count        = length(var.jobs)
  name         = join("-", tolist([lookup(var.jobs[count.index], "job_name"), "job-resolution"]))
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "run_number"

  attribute {
    name = "run_number"
    type = "S"
  }
  # Not listed here is the attribute 'successful' which is a boolean
    # cluster emr-bookmarking-cluster
    # final_prefix s3: // ahigley - emr / sample_job / final_outputs /
    # launcher_function launcher_trigger_lambda_sample_job
    # meta_data_prefix s3: // ahigley - emr / sample_job / run_info / output /
    # resolver sample_job_resolver
    # run_info s3: // ahigley - emr / test_job / run_info / run_4.json
    # subnet subnet - 0a8066232827443de, subnet - 0424375998fc31186
    # temp_prefix s3: // ahigley - emr / sample_job / temp_outputs

  tags = {
    Name = join("-", tolist([lookup(var.jobs[count.index], "job_name"), "job-success"]))
  }
}