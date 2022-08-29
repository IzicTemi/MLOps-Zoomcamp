resource "aws_s3_bucket" "s3_bucket" {
  bucket = var.bucket_name
}

resource "aws_s3_bucket_acl" "bucket_acl" {
  bucket = aws_s3_bucket.s3_bucket.id
  acl    = "private"
}

output "name_bucket" {
  value = aws_s3_bucket.s3_bucket.bucket
}