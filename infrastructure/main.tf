provider "aws" {
  region  = "us-east-1"
  version = ">= 2.39"
  assume_role {
    role_arn = "arn:aws:iam::021110012899:role/terraform"
  }
}
variable "vpc_name" {}
variable "vpc_cidr" {}
variable "vpc_availability_zones" {}
variable "vpc_public_subnet_cidrs" {}
variable "vpc_private_subnet_cidrs" {}
variable jobs {}
variable launcher_cpu {}
variable launcher_memory {}
variable resolver_cpu {}
variable "resolver_memory" {}

module "launcher" {
  source                   = "./modules/"
  vpc_name                 = var.vpc_name
  vpc_cidr                 = var.vpc_cidr
  vpc_availability_zones   = var.vpc_availability_zones
  vpc_public_subnet_cidrs  = var.vpc_public_subnet_cidrs
  vpc_private_subnet_cidrs = var.vpc_private_subnet_cidrs
  jobs                     = var.jobs
  launcher-cpu             = var.launcher_cpu
  launcher-memory          = var.launcher_memory
  resolver_cpu             = var.resolver_cpu
  resolver_memory          = var.resolver_memory
}