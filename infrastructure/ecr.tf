resource "aws_ecr_repository" "emr-launcher" {
  name                 = "emr-bookmarking"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}