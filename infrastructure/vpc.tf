module "vpc" {
  source               = "./modules/"
  name                 = "main"
  cidr                 = "172.16.0.0/16"
  availability_zones   = "us-east-1c,us-east-1d"
  public_subnet_cidrs  = "172.16.0.0/24,172.16.1.0/24"
  private_subnet_cidrs = ""
}