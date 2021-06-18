terraform {
  backend "s3" {
    bucket               = "ahigley-terraform"
    key                  = "emr/bookmarking/terraform.tfstate"
    region               = "us-east-1"
    role_arn             = "arn:aws:iam::021110012899:role/terraform"
    workspace_key_prefix = "env"
    session_name         = "terraform"
  }
}