resource "aws_ecr_repository" "first_run_or_reset" {
  for_each             = var.job_tracked_prefixes
  name                 = join("-", tolist([each.value.job_name, "reset-or-start"]))
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "job_rewind" {
  for_each             = var.job_tracked_prefixes
  name                 = join("-", tolist([each.value.job_name, "rewind"]))
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}