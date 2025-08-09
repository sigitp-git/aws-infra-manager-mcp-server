#!/usr/bin/env python3
"""
Basic usage examples for AWS Infrastructure Manager MCP Server

This script demonstrates how to use the MCP server tools for common AWS operations.
"""

import asyncio
import json
from typing import Dict, Any

# Example configurations
EXAMPLE_VPC_CONFIG = {
    "cidr_block": "10.0.0.0/16",
    "enable_dns_hostnames": True,
    "enable_dns_support": True,
    "tags": {
        "Name": "example-vpc",
        "Environment": "development",
        "Project": "mcp-demo"
    }
}

EXAMPLE_SUBNET_CONFIG = {
    "vpc_id": "vpc-12345678",  # Replace with actual VPC ID
    "cidr_block": "10.0.1.0/24",
    "availability_zone": "us-east-1a",
    "map_public_ip_on_launch": True,
    "tags": {
        "Name": "example-public-subnet",
        "Type": "public"
    }
}

EXAMPLE_SECURITY_GROUP_CONFIG = {
    "group_name": "example-web-sg",
    "description": "Security group for web servers",
    "vpc_id": "vpc-12345678",  # Replace with actual VPC ID
    "tags": {
        "Name": "example-web-sg",
        "Purpose": "web-server"
    }
}

EXAMPLE_EC2_CONFIG = {
    "image_id": "ami-0c02fb55956c7d316",  # Amazon Linux 2 AMI (us-east-1)
    "instance_type": "t3.micro",
    "key_name": "my-key-pair",  # Replace with your key pair
    "security_group_ids": ["sg-12345678"],  # Replace with actual security group ID
    "subnet_id": "subnet-12345678",  # Replace with actual subnet ID
    "user_data": """#!/bin/bash
yum update -y
yum install -y httpd
systemctl start httpd
systemctl enable httpd
echo "<h1>Hello from AWS Infrastructure Manager MCP Server!</h1>" > /var/www/html/index.html
""",
    "tags": {
        "Name": "example-web-server",
        "Environment": "development"
    }
}

EXAMPLE_RDS_CONFIG = {
    "db_instance_identifier": "example-database",
    "db_instance_class": "db.t3.micro",
    "engine": "mysql",
    "master_username": "admin",
    "master_user_password": "MySecurePassword123!",  # Use AWS Secrets Manager in production
    "allocated_storage": 20,
    "vpc_security_group_ids": ["sg-12345678"],  # Replace with actual security group ID
    "backup_retention_period": 7,
    "multi_az": False,
    "publicly_accessible": False,
    "tags": {
        "Name": "example-database",
        "Environment": "development"
    }
}

EXAMPLE_S3_CONFIG = {
    "bucket_name": "example-bucket-unique-name-12345",  # Must be globally unique
    "versioning": True,
    "public_read_access": False,
    "tags": {
        "Name": "example-bucket",
        "Environment": "development"
    }
}

EXAMPLE_LAMBDA_CONFIG = {
    "function_name": "example-hello-world",
    "runtime": "python3.9",
    "role": "arn:aws:iam::123456789012:role/lambda-execution-role",  # Replace with actual role ARN
    "handler": "lambda_function.lambda_handler",
    "code": {
        "ZipFile": b"""
import json

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Hello from AWS Infrastructure Manager MCP Server!',
            'event': event
        })
    }
"""
    },
    "description": "Example Lambda function created by MCP server",
    "timeout": 30,
    "memory_size": 128,
    "environment": {
        "ENVIRONMENT": "development",
        "PROJECT": "mcp-demo"
    },
    "tags": {
        "Name": "example-hello-world",
        "Environment": "development"
    }
}


def print_example_usage():
    """Print example usage instructions."""
    print("AWS Infrastructure Manager MCP Server - Example Usage")
    print("=" * 60)
    print()
    
    print("1. Basic Infrastructure Setup:")
    print("   - Create VPC")
    print("   - Create Subnet")
    print("   - Create Security Group")
    print("   - Launch EC2 Instance")
    print()
    
    print("2. Database Setup:")
    print("   - Create RDS Instance")
    print()
    
    print("3. Storage Setup:")
    print("   - Create S3 Bucket")
    print()
    
    print("4. Serverless Setup:")
    print("   - Create Lambda Function")
    print()
    
    print("Example MCP Tool Calls:")
    print("-" * 30)
    
    # VPC Creation
    print("\n# Create VPC")
    print("Tool: create_vpc")
    print("Parameters:")
    print(json.dumps(EXAMPLE_VPC_CONFIG, indent=2))
    
    # EC2 Instance Launch
    print("\n# Launch EC2 Instance")
    print("Tool: launch_ec2_instance")
    print("Parameters:")
    print(json.dumps(EXAMPLE_EC2_CONFIG, indent=2))
    
    # S3 Bucket Creation
    print("\n# Create S3 Bucket")
    print("Tool: create_s3_bucket")
    print("Parameters:")
    print(json.dumps(EXAMPLE_S3_CONFIG, indent=2))
    
    # Lambda Function Creation
    print("\n# Create Lambda Function")
    print("Tool: create_lambda_function")
    print("Parameters:")
    lambda_config_display = EXAMPLE_LAMBDA_CONFIG.copy()
    lambda_config_display["code"] = {"ZipFile": "# Python code here..."}
    print(json.dumps(lambda_config_display, indent=2))
    
    print("\n" + "=" * 60)
    print("Note: Replace placeholder values (IDs, ARNs, etc.) with actual values from your AWS account.")
    print("Ensure you have proper AWS credentials configured before using these tools.")


def print_workflow_example():
    """Print a complete workflow example."""
    print("\nComplete Infrastructure Workflow Example:")
    print("=" * 50)
    print()
    
    workflow_steps = [
        {
            "step": 1,
            "description": "Get caller identity to verify AWS credentials",
            "tool": "get_caller_identity",
            "parameters": {}
        },
        {
            "step": 2,
            "description": "List available regions",
            "tool": "get_aws_regions",
            "parameters": {}
        },
        {
            "step": 3,
            "description": "Create VPC for the infrastructure",
            "tool": "create_vpc",
            "parameters": EXAMPLE_VPC_CONFIG
        },
        {
            "step": 4,
            "description": "Create public subnet in the VPC",
            "tool": "create_subnet",
            "parameters": EXAMPLE_SUBNET_CONFIG
        },
        {
            "step": 5,
            "description": "Create security group for web servers",
            "tool": "create_security_group",
            "parameters": EXAMPLE_SECURITY_GROUP_CONFIG
        },
        {
            "step": 6,
            "description": "Add HTTP inbound rule to security group",
            "tool": "add_security_group_rule",
            "parameters": {
                "group_id": "sg-12345678",
                "ip_protocol": "tcp",
                "from_port": 80,
                "to_port": 80,
                "cidr_blocks": ["0.0.0.0/0"],
                "rule_type": "ingress"
            }
        },
        {
            "step": 7,
            "description": "Launch EC2 instance in the subnet",
            "tool": "launch_ec2_instance",
            "parameters": EXAMPLE_EC2_CONFIG
        },
        {
            "step": 8,
            "description": "Create S3 bucket for application data",
            "tool": "create_s3_bucket",
            "parameters": EXAMPLE_S3_CONFIG
        },
        {
            "step": 9,
            "description": "List all created resources",
            "tool": "list_ec2_instances",
            "parameters": {}
        }
    ]
    
    for step in workflow_steps:
        print(f"Step {step['step']}: {step['description']}")
        print(f"Tool: {step['tool']}")
        if step['parameters']:
            print("Parameters:")
            print(json.dumps(step['parameters'], indent=2))
        print()


def print_cleanup_example():
    """Print cleanup workflow example."""
    print("\nCleanup Workflow Example:")
    print("=" * 30)
    print()
    
    cleanup_steps = [
        "1. Terminate EC2 instances: terminate_ec2_instance",
        "2. Delete RDS instances: delete_rds_instance",
        "3. Delete Lambda functions: delete_lambda_function",
        "4. Delete S3 buckets: delete_s3_bucket (with force=True)",
        "5. Delete security groups (after instances are terminated)",
        "6. Delete subnets (after all resources are removed)",
        "7. Delete VPC (after all subnets and resources are removed)"
    ]
    
    for step in cleanup_steps:
        print(step)
    
    print("\nNote: Always clean up resources in the correct order to avoid dependency errors.")


if __name__ == "__main__":
    print_example_usage()
    print_workflow_example()
    print_cleanup_example()