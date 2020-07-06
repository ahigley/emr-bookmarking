resource "aws_s3_bucket" "emr-bucket" {
  bucket = "ahigley-emr"
  acl    = "private"
  region = "us-east-1"
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}

resource "aws_s3_bucket_public_access_block" "emr-bucket-block" {
  bucket = aws_s3_bucket.emr-bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

}
