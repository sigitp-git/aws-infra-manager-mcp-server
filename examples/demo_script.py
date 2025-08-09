#!/usr/bin/env python3
"""
AWS Infrastructure Manager MCP Server - Demo Script

This script demonstrates the capabilities of the MCP server by creating
a complete infrastructure setup including VPC, subnets, security groups,
EC2 instances, RDS database, S3 bucket, and Lambda function.
"""

import json
import time
import sys
from typing import Dict, Any, Optional

# Import MCP server functions
from aws_infra_manager_mcp_server.server import (
    get_caller_identity,
    get_aws_regions,
    get_availability_zones,
    create_vpc,
    create_subnet,
    create_security_group,
    add_security_group_rule,
    launch_ec2_instance,
    create_rds_instance,
    create_s3_bucket,
    create_lambda_function,
    list_ec2_instances,
    list_vpcs,
    list_s3_buckets,
    terminate_ec2_instance,
    delete_s3_bucket,
    delete_lambda_function,
    VPCRequest,
    SubnetRequest,
    SecurityGroupRequest,
    SecurityGroupRuleRequest,
    EC2InstanceRequest,
    RDSInstanceRequest,
    S3BucketRequest,
    LambdaFunctionRequest
)


class InfrastructureDemo:
    """Demonstrates AWS infrastructure management using the MCP server."""
    
    def __init__(self, region: str = "us-east-1", dry_run: bool = False):
        self.region = region
        self.dry_run = dry_run
        self.created_resources = {
            'vpc_id': None,
            'subnet_id': None,
            'security_group_id': None,
            'instance_ids': [],
            'rds_instance_id': None,
            'bucket_name': None,
            'lambda_function_name': None
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def wait_for_user(self, message: str = "Press Enter to continue..."):
        """Wait for user input."""
        if not self.dry_run:
            input(f"\n{message}")
    
    def run_demo(self):
        """Run the complete infrastructure demo."""
        self.log("🚀 Starting AWS Infrastructure Manager MCP Server Demo")
        
        try:
            # Step 1: Verify AWS connection
            self.verify_connection()
            
            # Step 2: Create VPC infrastructure
            self.create_network_infrastructure()
            
            # Step 3: Create compute resources
            self.create_compute_resources()
            
            # Step 4: Create database
            self.create_database()
            
            # Step 5: Create storage
            self.create_storage()
            
            # Step 6: Create serverless function
            self.create_serverless_function()
            
            # Step 7: List all created resources
            self.list_created_resources()
            
            # Step 8: Cleanup (optional)
            self.cleanup_resources()
            
            self.log("✅ Demo completed successfully!")
            
        except KeyboardInterrupt:
            self.log("Demo interrupted by user", "WARNING")
            self.cleanup_resources()
        except Exception as e:
            self.log(f"Demo failed: {e}", "ERROR")
            self.cleanup_resources()
            raise
    
    def verify_connection(self):
        """Verify AWS connection and permissions."""
        self.log("🔍 Verifying AWS connection...")
        
        # Get caller identity
        result = get_caller_identity(self.region)
        if not result.get('success'):
            raise Exception(f"Failed to get caller identity: {result.get('error_message')}")
        
        identity = result['identity']
        self.log(f"✅ Connected to AWS Account: {identity.get('Account')}")
        self.log(f"   User/Role: {identity.get('Arn')}")
        self.log(f"   Region: {self.region}")
        
        # List available regions
        regions_result = get_aws_regions(self.region)
        if regions_result.get('success'):
            region_count = len(regions_result['regions'])
            self.log(f"   Available regions: {region_count}")
        
        # List availability zones
        az_result = get_availability_zones(self.region)
        if az_result.get('success'):
            az_count = len(az_result['availability_zones'])
            self.log(f"   Availability zones in {self.region}: {az_count}")
        
        self.wait_for_user("✅ AWS connection verified. Continue with VPC creation?")
    
    def create_network_infrastructure(self):
        """Create VPC, subnet, and security group."""
        self.log("🏗️  Creating network infrastructure...")
        
        # Create VPC
        self.log("Creating VPC...")
        if not self.dry_run:
            vpc_request = VPCRequest(
                cidr_block="10.0.0.0/16",
                enable_dns_hostnames=True,
                enable_dns_support=True,
                tags={
                    "Name": "mcp-demo-vpc",
                    "Environment": "demo",
                    "Project": "mcp-server-demo"
                }
            )
            
            vpc_result = create_vpc(vpc_request, self.region)
            if not vpc_result.get('success'):
                raise Exception(f"Failed to create VPC: {vpc_result.get('error_message')}")
            
            self.created_resources['vpc_id'] = vpc_result['vpc']['VpcId']
            self.log(f"✅ VPC created: {self.created_resources['vpc_id']}")
        else:
            self.log("✅ VPC creation (dry run)")
        
        # Create subnet
        self.log("Creating public subnet...")
        if not self.dry_run:
            # Get first availability zone
            az_result = get_availability_zones(self.region)
            if not az_result.get('success'):
                raise Exception("Failed to get availability zones")
            
            first_az = az_result['availability_zones'][0]['ZoneName']
            
            subnet_request = SubnetRequest(
                vpc_id=self.created_resources['vpc_id'],
                cidr_block="10.0.1.0/24",
                availability_zone=first_az,
                map_public_ip_on_launch=True,
                tags={
                    "Name": "mcp-demo-public-subnet",
                    "Type": "public"
                }
            )
            
            subnet_result = create_subnet(subnet_request, self.region)
            if not subnet_result.get('success'):
                raise Exception(f"Failed to create subnet: {subnet_result.get('error_message')}")
            
            self.created_resources['subnet_id'] = subnet_result['subnet']['SubnetId']
            self.log(f"✅ Subnet created: {self.created_resources['subnet_id']}")
        else:
            self.log("✅ Subnet creation (dry run)")
        
        # Create security group
        self.log("Creating security group...")
        if not self.dry_run:
            sg_request = SecurityGroupRequest(
                group_name="mcp-demo-web-sg",
                description="Security group for MCP demo web servers",
                vpc_id=self.created_resources['vpc_id'],
                tags={
                    "Name": "mcp-demo-web-sg",
                    "Purpose": "web-server"
                }
            )
            
            sg_result = create_security_group(sg_request, self.region)
            if not sg_result.get('success'):
                raise Exception(f"Failed to create security group: {sg_result.get('error_message')}")
            
            self.created_resources['security_group_id'] = sg_result['group_id']
            self.log(f"✅ Security group created: {self.created_resources['security_group_id']}")
            
            # Add HTTP rule
            self.log("Adding HTTP inbound rule...")
            http_rule = SecurityGroupRuleRequest(
                group_id=self.created_resources['security_group_id'],
                ip_protocol="tcp",
                from_port=80,
                to_port=80,
                cidr_blocks=["0.0.0.0/0"],
                rule_type="ingress"
            )
            
            rule_result = add_security_group_rule(http_rule, self.region)
            if rule_result.get('success'):
                self.log("✅ HTTP rule added to security group")
            
            # Add HTTPS rule
            self.log("Adding HTTPS inbound rule...")
            https_rule = SecurityGroupRuleRequest(
                group_id=self.created_resources['security_group_id'],
                ip_protocol="tcp",
                from_port=443,
                to_port=443,
                cidr_blocks=["0.0.0.0/0"],
                rule_type="ingress"
            )
            
            rule_result = add_security_group_rule(https_rule, self.region)
            if rule_result.get('success'):
                self.log("✅ HTTPS rule added to security group")
        else:
            self.log("✅ Security group creation (dry run)")
        
        self.wait_for_user("✅ Network infrastructure created. Continue with compute resources?")
    
    def create_compute_resources(self):
        """Create EC2 instances."""
        self.log("💻 Creating compute resources...")
        
        if not self.dry_run:
            # Launch EC2 instance
            self.log("Launching EC2 instance...")
            
            user_data_script = """#!/bin/bash
yum update -y
yum install -y httpd
systemctl start httpd
systemctl enable httpd
echo "<h1>Hello from AWS Infrastructure Manager MCP Server!</h1>" > /var/www/html/index.html
echo "<p>This server was created using the MCP server demo.</p>" >> /var/www/html/index.html
echo "<p>Instance ID: $(curl -s http://169.254.169.254/latest/meta-data/instance-id)</p>" >> /var/www/html/index.html
"""
            
            ec2_request = EC2InstanceRequest(
                image_id="ami-0c02fb55956c7d316",  # Amazon Linux 2 AMI (us-east-1)
                instance_type="t3.micro",
                security_group_ids=[self.created_resources['security_group_id']],
                subnet_id=self.created_resources['subnet_id'],
                user_data=user_data_script,
                tags={
                    "Name": "mcp-demo-web-server",
                    "Environment": "demo",
                    "Purpose": "web-server"
                }
            )
            
            ec2_result = launch_ec2_instance(ec2_request, self.region)
            if not ec2_result.get('success'):
                raise Exception(f"Failed to launch EC2 instance: {ec2_result.get('error_message')}")
            
            self.created_resources['instance_ids'] = ec2_result['instance_ids']
            self.log(f"✅ EC2 instance launched: {self.created_resources['instance_ids'][0]}")
            
            # Wait a moment for instance to initialize
            self.log("Waiting for instance to initialize...")
            time.sleep(10)
            
        else:
            self.log("✅ EC2 instance launch (dry run)")
        
        self.wait_for_user("✅ Compute resources created. Continue with database?")
    
    def create_database(self):
        """Create RDS database instance."""
        self.log("🗄️  Creating database...")
        
        if not self.dry_run:
            rds_request = RDSInstanceRequest(
                db_instance_identifier="mcp-demo-database",
                db_instance_class="db.t3.micro",
                engine="mysql",
                master_username="admin",
                master_user_password="McpDemo123!",  # In production, use AWS Secrets Manager
                allocated_storage=20,
                vpc_security_group_ids=[self.created_resources['security_group_id']],
                backup_retention_period=1,  # Minimal for demo
                multi_az=False,
                publicly_accessible=False,
                tags={
                    "Name": "mcp-demo-database",
                    "Environment": "demo"
                }
            )
            
            rds_result = create_rds_instance(rds_request, self.region)
            if not rds_result.get('success'):
                # RDS creation might fail due to subnet group requirements
                self.log(f"⚠️  RDS creation skipped: {rds_result.get('error_message')}", "WARNING")
            else:
                self.created_resources['rds_instance_id'] = rds_result['db_instance']['DBInstanceIdentifier']
                self.log(f"✅ RDS instance created: {self.created_resources['rds_instance_id']}")
        else:
            self.log("✅ RDS instance creation (dry run)")
        
        self.wait_for_user("Database creation attempted. Continue with storage?")
    
    def create_storage(self):
        """Create S3 bucket."""
        self.log("🪣 Creating storage...")
        
        if not self.dry_run:
            # Generate unique bucket name
            import random
            import string
            suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            bucket_name = f"mcp-demo-bucket-{suffix}"
            
            s3_request = S3BucketRequest(
                bucket_name=bucket_name,
                versioning=True,
                public_read_access=False,
                tags={
                    "Name": "mcp-demo-bucket",
                    "Environment": "demo",
                    "Purpose": "application-data"
                }
            )
            
            s3_result = create_s3_bucket(s3_request, self.region)
            if not s3_result.get('success'):
                raise Exception(f"Failed to create S3 bucket: {s3_result.get('error_message')}")
            
            self.created_resources['bucket_name'] = bucket_name
            self.log(f"✅ S3 bucket created: {bucket_name}")
        else:
            self.log("✅ S3 bucket creation (dry run)")
        
        self.wait_for_user("✅ Storage created. Continue with serverless function?")
    
    def create_serverless_function(self):
        """Create Lambda function."""
        self.log("⚡ Creating serverless function...")
        
        if not self.dry_run:
            # Simple Lambda function code
            lambda_code = b"""
import json
import boto3
from datetime import datetime

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': 'Hello from AWS Infrastructure Manager MCP Server Lambda!',
            'timestamp': datetime.utcnow().isoformat(),
            'event': event,
            'demo': 'This function was created by the MCP server demo'
        })
    }
"""
            
            # Note: In a real scenario, you'd need to create an IAM role for Lambda
            # For this demo, we'll skip Lambda creation if no role is available
            try:
                lambda_request = LambdaFunctionRequest(
                    function_name="mcp-demo-function",
                    runtime="python3.9",
                    role="arn:aws:iam::123456789012:role/lambda-execution-role",  # Placeholder
                    handler="lambda_function.lambda_handler",
                    code={"ZipFile": lambda_code},
                    description="Demo Lambda function created by MCP server",
                    timeout=30,
                    memory_size=128,
                    environment={
                        "ENVIRONMENT": "demo",
                        "PROJECT": "mcp-server-demo"
                    },
                    tags={
                        "Name": "mcp-demo-function",
                        "Environment": "demo"
                    }
                )
                
                lambda_result = create_lambda_function(lambda_request, self.region)
                if lambda_result.get('success'):
                    self.created_resources['lambda_function_name'] = "mcp-demo-function"
                    self.log("✅ Lambda function created: mcp-demo-function")
                else:
                    self.log(f"⚠️  Lambda creation skipped: {lambda_result.get('error_message')}", "WARNING")
                    
            except Exception as e:
                self.log(f"⚠️  Lambda creation skipped: {e}", "WARNING")
        else:
            self.log("✅ Lambda function creation (dry run)")
        
        self.wait_for_user("Serverless function creation attempted. Continue with resource listing?")
    
    def list_created_resources(self):
        """List all created resources."""
        self.log("📋 Listing created resources...")
        
        if not self.dry_run:
            # List EC2 instances
            self.log("EC2 Instances:")
            ec2_result = list_ec2_instances(self.region)
            if ec2_result.get('success'):
                for instance in ec2_result['instances']:
                    if instance['InstanceId'] in self.created_resources['instance_ids']:
                        self.log(f"  - {instance['InstanceId']} ({instance['State']}) - {instance.get('PublicIpAddress', 'No public IP')}")
            
            # List VPCs
            self.log("VPCs:")
            vpc_result = list_vpcs(self.region)
            if vpc_result.get('success'):
                for vpc in vpc_result['vpcs']:
                    if vpc['VpcId'] == self.created_resources['vpc_id']:
                        self.log(f"  - {vpc['VpcId']} ({vpc['CidrBlock']}) - {vpc['State']}")
            
            # List S3 buckets
            self.log("S3 Buckets:")
            s3_result = list_s3_buckets(self.region)
            if s3_result.get('success'):
                for bucket in s3_result['buckets']:
                    if bucket['Name'] == self.created_resources['bucket_name']:
                        self.log(f"  - {bucket['Name']} (created: {bucket['CreationDate']})")
        else:
            self.log("Resource listing (dry run)")
        
        self.wait_for_user("✅ Resources listed. Proceed with cleanup?")
    
    def cleanup_resources(self):
        """Clean up all created resources."""
        self.log("🧹 Cleaning up resources...")
        
        if self.dry_run:
            self.log("Cleanup (dry run)")
            return
        
        cleanup_confirm = input("⚠️  This will delete all created resources. Are you sure? (yes/no): ")
        if cleanup_confirm.lower() != 'yes':
            self.log("Cleanup cancelled by user")
            return
        
        # Terminate EC2 instances
        for instance_id in self.created_resources['instance_ids']:
            if instance_id:
                self.log(f"Terminating EC2 instance: {instance_id}")
                try:
                    result = terminate_ec2_instance(instance_id, self.region)
                    if result.get('success'):
                        self.log(f"✅ Instance {instance_id} termination initiated")
                    else:
                        self.log(f"❌ Failed to terminate instance {instance_id}: {result.get('error_message')}")
                except Exception as e:
                    self.log(f"❌ Error terminating instance {instance_id}: {e}")
        
        # Delete Lambda function
        if self.created_resources['lambda_function_name']:
            self.log(f"Deleting Lambda function: {self.created_resources['lambda_function_name']}")
            try:
                result = delete_lambda_function(self.created_resources['lambda_function_name'], self.region)
                if result.get('success'):
                    self.log("✅ Lambda function deleted")
                else:
                    self.log(f"❌ Failed to delete Lambda function: {result.get('error_message')}")
            except Exception as e:
                self.log(f"❌ Error deleting Lambda function: {e}")
        
        # Delete S3 bucket
        if self.created_resources['bucket_name']:
            self.log(f"Deleting S3 bucket: {self.created_resources['bucket_name']}")
            try:
                result = delete_s3_bucket(self.created_resources['bucket_name'], force=True, region=self.region)
                if result.get('success'):
                    self.log("✅ S3 bucket deleted")
                else:
                    self.log(f"❌ Failed to delete S3 bucket: {result.get('error_message')}")
            except Exception as e:
                self.log(f"❌ Error deleting S3 bucket: {e}")
        
        self.log("⚠️  Note: VPC, subnet, and security group cleanup requires manual deletion")
        self.log("   This is to prevent accidental deletion of shared resources")
        
        self.log("🧹 Cleanup completed")


def main():
    """Main entry point for the demo script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='AWS Infrastructure Manager MCP Server Demo')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without creating resources')
    
    args = parser.parse_args()
    
    print("🚀 AWS Infrastructure Manager MCP Server Demo")
    print("=" * 60)
    print()
    print("This demo will create a complete AWS infrastructure including:")
    print("• VPC with public subnet and security group")
    print("• EC2 instance with web server")
    print("• RDS MySQL database (if possible)")
    print("• S3 bucket with versioning")
    print("• Lambda function (if IAM role available)")
    print()
    
    if args.dry_run:
        print("🔍 Running in DRY RUN mode - no resources will be created")
    else:
        print("⚠️  This will create real AWS resources that may incur charges!")
        confirm = input("Do you want to continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Demo cancelled")
            return 1
    
    print()
    
    try:
        demo = InfrastructureDemo(region=args.region, dry_run=args.dry_run)
        demo.run_demo()
        return 0
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
        return 1
    except Exception as e:
        print(f"\nDemo failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())