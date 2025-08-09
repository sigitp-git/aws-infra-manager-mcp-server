# AWS Infrastructure Manager MCP Server - API Reference

This document provides a comprehensive reference for all available tools in the AWS Infrastructure Manager MCP Server.

## Table of Contents

- [EC2 Management](#ec2-management)
- [VPC Management](#vpc-management)
- [RDS Management](#rds-management)
- [S3 Management](#s3-management)
- [Lambda Management](#lambda-management)
- [IAM Management](#iam-management)
- [CloudFormation Management](#cloudformation-management)
- [CloudWatch Management](#cloudwatch-management)
- [Auto Scaling Management](#auto-scaling-management)
- [Load Balancer Management](#load-balancer-management)
- [Route 53 Management](#route-53-management)
- [Utility Tools](#utility-tools)

## EC2 Management

### launch_ec2_instance

Launch a new EC2 instance with comprehensive configuration options.

**Parameters:**
- `request` (EC2InstanceRequest): Instance configuration
- `region` (str, optional): AWS region (default: "us-east-1")

**Request Schema:**
```json
{
  "image_id": "ami-12345678",
  "instance_type": "t3.micro",
  "key_name": "my-key-pair",
  "security_group_ids": ["sg-12345678"],
  "subnet_id": "subnet-12345678",
  "user_data": "#!/bin/bash\necho 'Hello World'",
  "tags": {
    "Name": "my-instance",
    "Environment": "production"
  },
  "min_count": 1,
  "max_count": 1
}
```

**Response:**
```json
{
  "success": true,
  "instances": [...],
  "instance_ids": ["i-1234567890abcdef0"]
}
```

### list_ec2_instances

List EC2 instances with optional filtering capabilities.

**Parameters:**
- `region` (str, optional): AWS region (default: "us-east-1")
- `filters` (dict, optional): EC2 filters (e.g., {"instance-state-name": ["running"]})

**Response:**
```json
{
  "success": true,
  "instances": [
    {
      "InstanceId": "i-1234567890abcdef0",
      "InstanceType": "t3.micro",
      "State": "running",
      "LaunchTime": "2024-01-01T00:00:00Z",
      "PublicIpAddress": "1.2.3.4",
      "PrivateIpAddress": "10.0.1.100",
      "Tags": [{"Key": "Name", "Value": "my-instance"}]
    }
  ],
  "count": 1
}
```

### terminate_ec2_instance

Terminate a specific EC2 instance.

**Parameters:**
- `instance_id` (str): ID of the instance to terminate
- `region` (str, optional): AWS region (default: "us-east-1")

**Response:**
```json
{
  "success": true,
  "terminating_instances": [...]
}
```

### get_ec2_instance_details

Get detailed information about a specific EC2 instance.

**Parameters:**
- `instance_id` (str): ID of the instance
- `region` (str, optional): AWS region (default: "us-east-1")

**Response:**
```json
{
  "success": true,
  "instance": {
    "InstanceId": "i-1234567890abcdef0",
    "ImageId": "ami-12345678",
    "State": {"Name": "running"},
    "InstanceType": "t3.micro",
    "LaunchTime": "2024-01-01T00:00:00Z",
    "Placement": {"AvailabilityZone": "us-east-1a"},
    "SecurityGroups": [...],
    "Tags": [...]
  }
}
```

## VPC Management

### create_vpc

Create a new Virtual Private Cloud (VPC).

**Parameters:**
- `request` (VPCRequest): VPC configuration
- `region` (str, optional): AWS region (default: "us-east-1")

**Request Schema:**
```json
{
  "cidr_block": "10.0.0.0/16",
  "enable_dns_hostnames": true,
  "enable_dns_support": true,
  "tags": {
    "Name": "my-vpc",
    "Environment": "production"
  }
}
```

**Response:**
```json
{
  "success": true,
  "vpc": {
    "VpcId": "vpc-12345678",
    "CidrBlock": "10.0.0.0/16",
    "State": "available"
  }
}
```

### list_vpcs

List all VPCs in the specified region.

**Parameters:**
- `region` (str, optional): AWS region (default: "us-east-1")

**Response:**
```json
{
  "success": true,
  "vpcs": [
    {
      "VpcId": "vpc-12345678",
      "CidrBlock": "10.0.0.0/16",
      "State": "available",
      "Tags": [...]
    }
  ]
}
```

### create_subnet

Create a new subnet within a VPC.

**Parameters:**
- `request` (SubnetRequest): Subnet configuration
- `region` (str, optional): AWS region (default: "us-east-1")

**Request Schema:**
```json
{
  "vpc_id": "vpc-12345678",
  "cidr_block": "10.0.1.0/24",
  "availability_zone": "us-east-1a",
  "map_public_ip_on_launch": true,
  "tags": {
    "Name": "public-subnet-1a",
    "Type": "public"
  }
}
```

### create_security_group

Create a new security group.

**Parameters:**
- `request` (SecurityGroupRequest): Security group configuration
- `region` (str, optional): AWS region (default: "us-east-1")

**Request Schema:**
```json
{
  "group_name": "web-servers-sg",
  "description": "Security group for web servers",
  "vpc_id": "vpc-12345678",
  "tags": {
    "Name": "web-servers-sg",
    "Purpose": "web-traffic"
  }
}
```

### add_security_group_rule

Add an ingress or egress rule to a security group.

**Parameters:**
- `request` (SecurityGroupRuleRequest): Rule configuration
- `region` (str, optional): AWS region (default: "us-east-1")

**Request Schema:**
```json
{
  "group_id": "sg-12345678",
  "ip_protocol": "tcp",
  "from_port": 80,
  "to_port": 80,
  "cidr_blocks": ["0.0.0.0/0"],
  "rule_type": "ingress"
}
```

### list_security_groups

List security groups, optionally filtered by VPC.

**Parameters:**
- `vpc_id` (str, optional): VPC ID to filter by
- `region` (str, optional): AWS region (default: "us-east-1")

## RDS Management

### create_rds_instance

Create a new RDS database instance.

**Parameters:**
- `request` (RDSInstanceRequest): RDS configuration
- `region` (str, optional): AWS region (default: "us-east-1")

**Request Schema:**
```json
{
  "db_instance_identifier": "production-db",
  "db_instance_class": "db.t3.micro",
  "engine": "mysql",
  "master_username": "admin",
  "master_user_password": "SecurePassword123!",
  "allocated_storage": 20,
  "vpc_security_group_ids": ["sg-12345678"],
  "backup_retention_period": 7,
  "multi_az": true,
  "publicly_accessible": false,
  "tags": {
    "Name": "production-database",
    "Environment": "production"
  }
}
```

### list_rds_instances

List all RDS database instances.

**Parameters:**
- `region` (str, optional): AWS region (default: "us-east-1")

### delete_rds_instance

Delete an RDS database instance.

**Parameters:**
- `db_instance_identifier` (str): Database instance identifier
- `skip_final_snapshot` (bool, optional): Skip final snapshot (default: true)
- `region` (str, optional): AWS region (default: "us-east-1")

## S3 Management

### create_s3_bucket

Create a new S3 bucket with optional versioning and access control.

**Parameters:**
- `request` (S3BucketRequest): S3 bucket configuration
- `region` (str, optional): AWS region (default: "us-east-1")

**Request Schema:**
```json
{
  "bucket_name": "my-app-data-bucket-12345",
  "versioning": true,
  "public_read_access": false,
  "tags": {
    "Name": "application-data",
    "Environment": "production"
  }
}
```

### list_s3_buckets

List all S3 buckets in the account.

**Parameters:**
- `region` (str, optional): AWS region (default: "us-east-1")

### delete_s3_bucket

Delete an S3 bucket with optional force deletion of all objects.

**Parameters:**
- `bucket_name` (str): Name of the bucket to delete
- `force` (bool, optional): Force delete all objects first (default: false)
- `region` (str, optional): AWS region (default: "us-east-1")

## Lambda Management

### create_lambda_function

Create a new Lambda function.

**Parameters:**
- `request` (LambdaFunctionRequest): Lambda function configuration
- `region` (str, optional): AWS region (default: "us-east-1")

**Request Schema:**
```json
{
  "function_name": "data-processor",
  "runtime": "python3.9",
  "role": "arn:aws:iam::123456789012:role/lambda-execution-role",
  "handler": "lambda_function.lambda_handler",
  "code": {
    "ZipFile": "base64-encoded-zip-content"
  },
  "description": "Processes incoming data",
  "timeout": 30,
  "memory_size": 256,
  "environment": {
    "ENVIRONMENT": "production",
    "LOG_LEVEL": "INFO"
  },
  "tags": {
    "Name": "data-processor",
    "Team": "data-engineering"
  }
}
```

### list_lambda_functions

List all Lambda functions in the region.

**Parameters:**
- `region` (str, optional): AWS region (default: "us-east-1")

### invoke_lambda_function

Invoke a Lambda function with optional payload.

**Parameters:**
- `function_name` (str): Name of the Lambda function
- `payload` (dict, optional): Payload to send to the function
- `region` (str, optional): AWS region (default: "us-east-1")

### delete_lambda_function

Delete a Lambda function.

**Parameters:**
- `function_name` (str): Name of the Lambda function to delete
- `region` (str, optional): AWS region (default: "us-east-1")

## IAM Management

### list_iam_roles

List all IAM roles in the account.

**Parameters:**
- `region` (str, optional): AWS region (default: "us-east-1")

### create_iam_role

Create a new IAM role with trust policy.

**Parameters:**
- `role_name` (str): Name of the IAM role
- `assume_role_policy_document` (dict): Trust policy document
- `description` (str, optional): Role description
- `tags` (dict, optional): Role tags
- `region` (str, optional): AWS region (default: "us-east-1")

### attach_role_policy

Attach a managed policy to an IAM role.

**Parameters:**
- `role_name` (str): Name of the IAM role
- `policy_arn` (str): ARN of the policy to attach
- `region` (str, optional): AWS region (default: "us-east-1")

## CloudFormation Management

### list_cloudformation_stacks

List all CloudFormation stacks.

**Parameters:**
- `region` (str, optional): AWS region (default: "us-east-1")

### get_cloudformation_stack

Get details of a specific CloudFormation stack.

**Parameters:**
- `stack_name` (str): Name of the CloudFormation stack
- `region` (str, optional): AWS region (default: "us-east-1")

## CloudWatch Management

### list_cloudwatch_alarms

List CloudWatch alarms with optional state filtering.

**Parameters:**
- `region` (str, optional): AWS region (default: "us-east-1")
- `state_value` (str, optional): State filter (OK, ALARM, INSUFFICIENT_DATA)

### get_cloudwatch_metrics

List CloudWatch metrics for a specific namespace.

**Parameters:**
- `namespace` (str): CloudWatch namespace (e.g., AWS/EC2, AWS/RDS)
- `region` (str, optional): AWS region (default: "us-east-1")

## Auto Scaling Management

### list_auto_scaling_groups

List all Auto Scaling groups.

**Parameters:**
- `region` (str, optional): AWS region (default: "us-east-1")

## Load Balancer Management

### list_load_balancers

List Elastic Load Balancers (Application and Network Load Balancers).

**Parameters:**
- `region` (str, optional): AWS region (default: "us-east-1")

## Route 53 Management

### list_hosted_zones

List Route 53 hosted zones.

**Parameters:**
- `region` (str, optional): AWS region (default: "us-east-1")

## Utility Tools

### get_caller_identity

Get information about the current AWS caller identity.

**Parameters:**
- `region` (str, optional): AWS region (default: "us-east-1")

**Response:**
```json
{
  "success": true,
  "identity": {
    "UserId": "AIDACKCEVSQ6C2EXAMPLE",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/test-user"
  }
}
```

### get_aws_regions

Get list of all available AWS regions.

**Parameters:**
- `region` (str, optional): AWS region for the API call (default: "us-east-1")

**Response:**
```json
{
  "success": true,
  "regions": [
    {
      "RegionName": "us-east-1",
      "Endpoint": "ec2.us-east-1.amazonaws.com"
    }
  ]
}
```

### get_availability_zones

Get list of availability zones for a specific region.

**Parameters:**
- `region` (str, optional): AWS region (default: "us-east-1")

**Response:**
```json
{
  "success": true,
  "availability_zones": [
    {
      "ZoneName": "us-east-1a",
      "State": "available",
      "RegionName": "us-east-1"
    }
  ]
}
```

### get_account_attributes

Get AWS account attributes and limits.

**Parameters:**
- `region` (str, optional): AWS region (default: "us-east-1")

## Error Handling

All tools return consistent error responses when AWS operations fail:

```json
{
  "error": true,
  "error_code": "AccessDenied",
  "error_message": "User is not authorized to perform this action",
  "details": "Full error details..."
}
```

Common error codes include:
- `AccessDenied`: Insufficient permissions
- `InvalidParameterValue`: Invalid parameter provided
- `ResourceNotFound`: Requested resource doesn't exist
- `LimitExceeded`: AWS service limits exceeded
- `ThrottlingException`: API rate limits exceeded

## Rate Limiting

The server implements automatic retry logic for rate-limited operations. If you encounter persistent rate limiting issues, consider:

1. Reducing the frequency of API calls
2. Implementing exponential backoff in your client
3. Using AWS service-specific pagination for large result sets

## Best Practices

1. **Always specify regions** explicitly for better performance and predictability
2. **Use filters** when listing resources to reduce response size and improve performance
3. **Implement proper error handling** in your client applications
4. **Tag all resources** consistently for better organization and cost tracking
5. **Use least privilege IAM policies** for security
6. **Monitor API usage** to avoid hitting service limits