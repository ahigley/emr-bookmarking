resource "aws_ecr_repository" "emr-launcher" {
  count                = length(var.jobs)
  name                 = join("-", tolist([lookup(var.jobs[count.index], "job_name"), "emr-launcher"]))
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "emr-resolver" {
  count                = length(var.jobs)
  name                 = join("-", tolist([lookup(var.jobs[count.index], "job_name"), "emr-resolver"]))
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}