variable "name" {}
variable "cidr" {}
variable "availability_zones" {}
variable "public_subnet_cidrs" {}
variable "private_subnet_cidrs" {}


#VPC
resource "aws_vpc" "vpc" {
  cidr_block           = var.cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = var.name
  }
}

#Public Subnets
resource "aws_internet_gateway" "public-igw" {
  vpc_id = aws_vpc.vpc.id
  tags = {
    Name = "${var.name}-public-igw"
  }
}

resource "aws_subnet" "public_subnet" {
  count                   = length(split(",", var.public_subnet_cidrs))
  vpc_id                  = aws_vpc.vpc.id
  cidr_block              = element(split(",", var.public_subnet_cidrs), count.index)
  availability_zone       = element(split(",", var.availability_zones), count.index)
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.name}-public-subnet-${element(split(",", var.availability_zones), count.index)}"
  }
}

resource "aws_route_table" "public_route_table" {
  vpc_id = aws_vpc.vpc.id

  tags = {
    Name = "${var.name}-public-route-table"
  }
}

resource "aws_route" "route_public" {
  route_table_id         = aws_route_table.public_route_table.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.public-igw.id
  depends_on             = [aws_route_table.public_route_table]
}

resource "aws_route_table_association" "public_association" {
  count          = length(split(",", var.public_subnet_cidrs))
  subnet_id      = element(aws_subnet.public_subnet.*.id, count.index)
  route_table_id = aws_route_table.public_route_table.id
}

# Private Subnets
resource "aws_subnet" "private_subnet" {
  count             = var.private_subnet_cidrs == "" ? 0 : length(split(",", var.private_subnet_cidrs))
  vpc_id            = aws_vpc.vpc.id
  cidr_block        = element(split(",", var.private_subnet_cidrs), count.index)
  availability_zone = element(split(",", var.availability_zones), count.index)

  tags = {
    Name = "${var.name}-private-subnet-${element(split(",", var.availability_zones), count.index)}"
  }
}

resource "aws_eip" "gw" {
  count      = var.private_subnet_cidrs == "" ? 0 : length(split(",", var.private_subnet_cidrs))
  vpc        = true
  depends_on = [aws_internet_gateway.public-igw]
}

resource "aws_nat_gateway" "gw" {
  count         = var.private_subnet_cidrs == "" ? 0 : length(split(",", var.private_subnet_cidrs))
  subnet_id     = element(aws_subnet.public_subnet.*.id, count.index)
  allocation_id = element(aws_eip.gw.*.id, count.index)
}

resource "aws_route_table" "private_route_table" {
  vpc_id = aws_vpc.vpc.id
  count  = var.private_subnet_cidrs == "" ? 0 : length(split(",", var.private_subnet_cidrs))
  tags = {
    Name = "${var.name}-private-route-table-${element(split(",", var.availability_zones), count.index)}"
  }
}

resource "aws_route" "private-nat" {
  count                  = var.private_subnet_cidrs == "" ? 0 : length(split(",", var.private_subnet_cidrs))
  route_table_id         = element(aws_route_table.private_route_table.*.id, count.index)
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = element(aws_nat_gateway.gw.*.id, count.index)
  depends_on             = [aws_route_table.private_route_table]
}

resource "aws_route_table_association" "private-association" {
  count          = var.private_subnet_cidrs == "" ? 0 : length(split(",", var.private_subnet_cidrs))
  subnet_id      = element(aws_subnet.private_subnet.*.id, count.index)
  route_table_id = element(aws_route_table.private_route_table.*.id, count.index)
}