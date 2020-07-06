provider "aws" {
  region  = "us-east-1"
  version = ">= 2.39"
  assume_role {
    role_arn = "arn:aws:iam::021110012899:role/terraform"
  }
}