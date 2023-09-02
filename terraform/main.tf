terraform {
    required_version = ">= 1.2.0"

    required_providers {
        aws = {
            source = "hashicorp/aws"
            version = "~> 4.16"
        }
    }
}

# Configure AWS provider
provider "aws" {
    region = var.aws_region
    profile  = "default"
}

# Configure redshift cluster. This will fall under free tier as of June 2022.
resource "aws_redshift_cluster" "redshift" {
  cluster_identifier = "toronto-real-estate-cluster-pipeline"
  skip_final_snapshot = true # must be set so we can destroy redshift with terraform destroy
  database_name = "stage"
  master_username    = "root"
  master_password    = var.db_password
  node_type          = "dc2.large"
  cluster_type       = "single-node"
  publicly_accessible = "true"
  iam_roles = [aws_iam_role.redshift_role.arn]
  vpc_security_group_ids = [aws_security_group.sg_redshift.id]
  
}

# Confuge security group for Redshift allowing all inbound/outbound traffic
 resource "aws_security_group" "sg_redshift" {
  name        = "sg_redshift"
  ingress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
  }
  egress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
  }
}

# Create S3 Read only access role. This is assigned to Redshift cluster so that it can read data from S3
resource "aws_iam_role" "redshift_role" {
  name = "RedShiftLoadRole"
  managed_policy_arns = ["arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"]
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "redshift.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_s3_bucket" "realestate_bucket" {
  bucket = var.s3_bucket
  force_destroy = true # will delete contents of bucket when we run terraform destroy
}

resource "aws_s3_bucket_ownership_controls" "acl" {
  bucket = aws_s3_bucket.realestate_bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "acl_control" {
  depends_on = [aws_s3_bucket_ownership_controls.acl]

  bucket = aws_s3_bucket.realestate_bucket.id
  acl    = "private"
}


resource "aws_s3_object" "transformed" {
  bucket = aws_s3_bucket.realestate_bucket.id
  key    = "transformed/"
  
}

resource "aws_s3_object" "data" {
  bucket = aws_s3_bucket.realestate_bucket.id
  key    = "data/"
  
}
     
      

resource "aws_budgets_budget" "cost" {
  name = "overall-cost-cap"
  budget_type = "COST"
  limit_amount = "10"
  limit_unit = "USD"
  time_unit = "MONTHLY"
}