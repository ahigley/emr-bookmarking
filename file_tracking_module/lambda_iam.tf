data "aws_iam_policy_document" "tracking_lambda_trusted_entities" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type = "Service"
      identifiers = [
        "lambda.amazonaws.com"
      ]
    }
    effect = "Allow"
  }
}

resource "aws_iam_role" "tracking_lambda_role" {
  for_each           = var.job_tracked_prefixes
  name               = "${each.value.job_name}_tracking_lambda_role"
  assume_role_policy = data.aws_iam_policy_document.tracking_lambda_trusted_entities.json
  inline_policy {
    name   = "allow-access-dynamodb"
    policy = data.aws_iam_policy_document.allow_modify_dynamodb_file_tracking.json
  }

  inline_policy {
    name   = "allow-read-s3"
    policy = data.aws_iam_policy_document.s3_read_only.json
  }

}
resource "aws_iam_role_policy_attachment" "data_engineer_administrator_access_attached_policy" {
  role       = aws_iam_role.tracking_lambda_role
  policy_arn = data.aws_iam_policy.allow_cloudwatch_full.arn
}
data "aws_iam_policy" "allow_cloudwatch_full" {
  arn = "arn:aws:iam::aws:policy/CloudWatchFullAccess"
}