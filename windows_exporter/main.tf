provider "aws" {
  region = "us-east-1"	
}

resource "aws_lambda_function" "disk_lambda" {
  filename      = "get-disk-package.zip"
  function_name = "get-disk-utilization-function"
  role          = "arn:aws:iam::123456789:role/service-role/getmetrics-role-abcd"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.8"
  timeout       = "30"
  source_code_hash = filebase64sha256("get-disk-package.zip")

  environment {
    variables = {
      bucket_name = "<buckcet-name>"
    }
  }
}
