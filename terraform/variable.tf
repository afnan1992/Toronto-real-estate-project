variable "db_password" {
  description = "Password for Redshift master DB user"
  type        = string
  default     = ""
  sensitive = true
} # need to specify

variable "s3_bucket" {
  description = "Bucket name for S3"
  type        = string
  default     = "afnan1992-toronto-real-estate-listings"
}

variable "aws_region" {
  description = "Region for AWS"
  type        = string
  default     = "us-east-1"
}

