variable jobs {}
variable "vpc_name" {}
variable "vpc_cidr" {}
variable "vpc_availability_zones" {}
variable "vpc_public_subnet_cidrs" {}
variable "vpc_private_subnet_cidrs" {}
variable "launcher-cpu" {}
variable "launcher-memory" {}
variable resolver_cpu {}
variable "resolver_memory" {}

locals {
  job-prefix-association =flatten([
    for job_details in var.jobs : [
      for prefix in lookup(job_details, "cdc_prefixes") : {
        job    = lookup(job_details, "job_name")
        prefix = prefix
      }
        ]
          ])


  job-bucket-id-association = zipmap([
    for i, job_details in var.jobs :
    lookup
    (job_details,
      "job_name")
  ],
    [
    for i, job_details in var.jobs :
      element(aws_s3_bucket.emr-bucket.*.id,
        i)
    ]
  )
  job-bucket-arn-association = zipmap(
    [
      for i, job_details in var.jobs :
      lookup(job_details, "job_name")
    ],
    [
      for i, job_details in var.jobs :
      element(aws_s3_bucket.emr-bucket.*.arn, i)
    ]
  )
  job-lambda-role-association = zipmap(
    [
      for i, job_details in var.jobs :
      lookup(job_details, "job_name")
      ], [
      for i, job_details in var.jobs :
      element(aws_iam_role.file_tracking.*.arn, i)
    ]
  )
  job-dynamodb-table-association = zipmap(
    [
      for i, job_details in var.jobs :
      lookup(job_details, "job_name")
      ], [
      for i, job_details in var.jobs :
      element(aws_dynamodb_table.file-tracking-table.*.name, i)
    ]
  )
}