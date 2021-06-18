launcher_cpu    = 256
launcher_memory = 512

resolver_cpu    = 256
resolver_memory = 512

vpc_name                 = "main"
vpc_cidr                 = "172.16.0.0/16"
vpc_availability_zones   = "us-east-1c,us-east-1d"
vpc_public_subnet_cidrs  = "172.16.0.0/24,172.16.1.0/24"
vpc_private_subnet_cidrs = ""

jobs = [
  {
    job_name         = "sample_job"
    bucket_name      = "ahigley-emr"
    meta_data_prefix = "s3://ahigley-emr/sample_job/run_info/output/"
    cdc_prefixes = [
      "sample_data/"]
  }
]