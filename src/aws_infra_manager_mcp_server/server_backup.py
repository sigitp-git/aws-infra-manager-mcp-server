"""
AWS Infrastructure Manager MCP Server

A comprehensive MCP server for managing AWS infrastructure including EC2, VPC, 
RDS, Lambda, S3, IAM, and more using the FastMCP SDK.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for request validation
class EC2InstanceRequest(BaseModel):
    """Request model for EC2 instance operations."""
    image_id: str = Field(description="AMI ID for the instance")
    instance_type: str = Field(default="t3.micro", description="Instance type")
    key_name: Optional[str] = Field(default=None, description="Key pair name")
    security_group_ids: Optional[List[str]] = Field(default=None, description="Security group IDs")
    subnet_id: Optional[str] = Field(default=None, description="Subnet ID")
    user_data: Optional[str] = Field(default=None, description="User data script")
    tags: Optional[Dict[str, str]] = Field(default=None, description="Instance tags")
    min_count: int = Field(default=1, description="Minimum number of instances")
    max_count: int = Field(default=1, description="Maximum number of instances")

class VPCRequest(BaseModel):
    """Request model for VPC operations."""
    cidr_block: str = Field(description="CIDR block for the VPC")
    enable_dns_hostnames: bool = Field(default=True, description="Enable DNS hostnames")
    enable_dns_support: bool = Field(default=True, description="Enable DNS support")
    tags: Optional[Dict[str, str]] = Field(default=None, description="VPC tags")

class SubnetRequest(BaseModel):
    """Request model for subnet operations."""
    vpc_id: str = Field(description="VPC ID")
    cidr_block: str = Field(description="CIDR block for the subnet")
    availability_zone: Optional[str] = Field(default=None, description="Availability zone")
    map_public_ip_on_launch: bool = Field(default=False, description="Map public IP on launch")
    tags: Optional[Dict[str, str]] = Field(default=None, description="Subnet tags")

class SecurityGroupRequest(BaseModel):
    """Request model for security group operations."""
    group_name: str = Field(description="Security group name")
    description: str = Field(description="Security group description")
    vpc_id: str = Field(description="VPC ID")
    tags: Optional[Dict[str, str]] = Field(default=None, description="Security group tags")

class SecurityGroupRuleRequest(BaseModel):
    """Request model for security group rule operations."""
    group_id: str = Field(description="Security group ID")
    ip_protocol: str = Field(description="IP protocol (tcp, udp, icmp, -1 for all)")
    from_port: Optional[int] = Field(default=None, description="From port")
    to_port: Optional[int] = Field(default=None, description="To port")
    cidr_blocks: Optional[List[str]] = Field(default=None, description="CIDR blocks")
    source_security_group_id: Optional[str] = Field(default=None, description="Source security group ID")
    rule_type: str = Field(default="ingress", description="Rule type (ingress or egress)")

class RDSInstanceRequest(BaseModel):
    """Request model for RDS instance operations."""
    db_instance_identifier: str = Field(description="Database instance identifier")
    db_instance_class: str = Field(default="db.t3.micro", description="Database instance class")
    engine: str = Field(description="Database engine")
    master_username: str = Field(description="Master username")
    master_user_password: str = Field(description="Master user password")
    allocated_storage: int = Field(default=20, description="Allocated storage in GB")
    vpc_security_group_ids: Optional[List[str]] = Field(default=None, description="VPC security group IDs")
    db_subnet_group_name: Optional[str] = Field(default=None, description="DB subnet group name")
    backup_retention_period: int = Field(default=7, description="Backup retention period")
    multi_az: bool = Field(default=False, description="Multi-AZ deployment")
    publicly_accessible: bool = Field(default=False, description="Publicly accessible")
    tags: Optional[Dict[str, str]] = Field(default=None, description="RDS tags")

class S3BucketRequest(BaseModel):
    """Request model for S3 bucket operations."""
    bucket_name: str = Field(description="S3 bucket name")
    region: Optional[str] = Field(default=None, description="AWS region")
    versioning: bool = Field(default=False, description="Enable versioning")
    public_read_access: bool = Field(default=False, description="Enable public read access")
    tags: Optional[Dict[str, str]] = Field(default=None, description="Bucket tags")

class LambdaFunctionRequest(BaseModel):
    """Request model for Lambda function operations."""
    function_name: str = Field(description="Lambda function name")
    runtime: str = Field(description="Runtime environment")
    role: str = Field(description="IAM role ARN")
    handler: str = Field(description="Function handler")
    code: Dict[str, Any] = Field(description="Function code")
    description: Optional[str] = Field(default=None, description="Function description")
    timeout: int = Field(default=30, description="Function timeout in seconds")
    memory_size: int = Field(default=128, description="Memory size in MB")
    environment: Optional[Dict[str, str]] = Field(default=None, description="Environment variables")
    tags: Optional[Dict[str, str]] = Field(default=None, description="Function tags")

# Initialize FastMCP
mcp = FastMCP("AWS Infrastructure Manager")

class AWSClientManager:
    """Manages AWS service clients with proper error handling."""
    
    def __init__(self):
        self._clients = {}
        self._session = None
    
    def get_session(self) -> boto3.Session:
        """Get or create boto3 session."""
        if not self._session:
            try:
                self._session = boto3.Session()
                # Test credentials
                sts = self._session.client('sts')
                sts.get_caller_identity()
            except NoCredentialsError:
                raise Exception("AWS credentials not configured. Please configure AWS CLI or set environment variables.")
            except Exception as e:
                raise Exception(f"Failed to initialize AWS session: {str(e)}")
        return self._session
    
    def get_client(self, service_name: str, region: str = None):
        """Get AWS service client."""
        key = f"{service_name}_{region or 'default'}"
        if key not in self._clients:
            session = self.get_session()
            self._clients[key] = session.client(service_name, region_name=region)
        return self._clients[key]

# Global client manager
aws_clients = AWSClientManager()

def handle_aws_error_inline(operation_name: str, e: Exception) -> Dict[str, Any]:
    """Handle AWS errors consistently - for inline use."""
    if isinstance(e, ClientError):
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"AWS ClientError in {operation_name}: {error_code} - {error_message}")
        return {
            "error": True,
            "error_code": error_code,
            "error_message": error_message,
            "details": str(e)
        }
    else:
        logger.error(f"Unexpected error in {operation_name}: {str(e)}")
        return {
            "error": True,
            "error_message": str(e)
        }

# Note: FastMCP doesn't support decorators with *args, so we use inline error handling

# EC2 Management Tools
@mcp.tool()
def launch_ec2_instance(request: EC2InstanceRequest, region: str = "us-east-1") -> Dict[str, Any]:
    """
    Launch a new EC2 instance.
    
    Args:
        request: EC2 instance configuration
        region: AWS region to launch the instance in
        
    Returns:
        Dictionary containing instance details or error information
    """
    try:
        ec2 = aws_clients.get_client('ec2', region)
        
        launch_params = {
            'ImageId': request.image_id,
            'MinCount': request.min_count,
            'MaxCount': request.max_count,
            'InstanceType': request.instance_type
        }
        
        if request.key_name:
            launch_params['KeyName'] = request.key_name
        if request.security_group_ids:
            launch_params['SecurityGroupIds'] = request.security_group_ids
        if request.subnet_id:
            launch_params['SubnetId'] = request.subnet_id
        if request.user_data:
            launch_params['UserData'] = request.user_data
        
        response = ec2.run_instances(**launch_params)
        
        # Add tags if provided
        if request.tags and response['Instances']:
            instance_ids = [instance['InstanceId'] for instance in response['Instances']]
            tag_list = [{'Key': k, 'Value': v} for k, v in request.tags.items()]
            ec2.create_tags(Resources=instance_ids, Tags=tag_list)
        
        return {
            "success": True,
            "instances": response['Instances'],
            "instance_ids": [instance['InstanceId'] for instance in response['Instances']]
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"AWS ClientError in launch_ec2_instance: {error_code} - {error_message}")
        return {
            "error": True,
            "error_code": error_code,
            "error_message": error_message,
            "details": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error in launch_ec2_instance: {str(e)}")
        return {
            "error": True,
            "error_message": str(e)
        }

@mcp.tool()
def list_ec2_instances(region: str = "us-east-1", filters: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
    """
    List EC2 instances with optional filtering.
    
    Args:
        region: AWS region to list instances from
        filters: Optional filters to apply (e.g., {"instance-state-name": ["running"]})
        
    Returns:
        Dictionary containing list of instances
    """
    ec2 = aws_clients.get_client('ec2', region)
    
    describe_params = {}
    if filters:
        describe_params['Filters'] = [
            {'Name': name, 'Values': values} for name, values in filters.items()
        ]
    
    response = ec2.describe_instances(**describe_params)
    
    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instances.append({
                'InstanceId': instance['InstanceId'],
                'InstanceType': instance['InstanceType'],
                'State': instance['State']['Name'],
                'LaunchTime': instance['LaunchTime'].isoformat(),
                'PublicIpAddress': instance.get('PublicIpAddress'),
                'PrivateIpAddress': instance.get('PrivateIpAddress'),
                'Tags': instance.get('Tags', [])
            })
    
    return {
        "success": True,
        "instances": instances,
        "count": len(instances)
    }

@mcp.tool()
def terminate_ec2_instance(instance_id: str, region: str = "us-east-1") -> Dict[str, Any]:
    """
    Terminate an EC2 instance.
    
    Args:
        instance_id: ID of the instance to terminate
        region: AWS region where the instance is located
        
    Returns:
        Dictionary containing termination status
    """
    ec2 = aws_clients.get_client('ec2', region)
    
    response = ec2.terminate_instances(InstanceIds=[instance_id])
    
    return {
        "success": True,
        "terminating_instances": response['TerminatingInstances']
    }

@mcp.tool()
def get_ec2_instance_details(instance_id: str, region: str = "us-east-1") -> Dict[str, Any]:
    """
    Get detailed information about a specific EC2 instance.
    
    Args:
        instance_id: ID of the instance
        region: AWS region where the instance is located
        
    Returns:
        Dictionary containing detailed instance information
    """
    ec2 = aws_clients.get_client('ec2', region)
    
    response = ec2.describe_instances(InstanceIds=[instance_id])
    
    if not response['Reservations']:
        return {"error": True, "error_message": f"Instance {instance_id} not found"}
    
    instance = response['Reservations'][0]['Instances'][0]
    
    return {
        "success": True,
        "instance": instance
    }

# VPC Management Tools
@mcp.tool()
def create_vpc(request: VPCRequest, region: str = "us-east-1") -> Dict[str, Any]:
    """
    Create a new VPC.
    
    Args:
        request: VPC configuration
        region: AWS region to create the VPC in
        
    Returns:
        Dictionary containing VPC details
    """
    ec2 = aws_clients.get_client('ec2', region)
    
    response = ec2.create_vpc(CidrBlock=request.cidr_block)
    vpc_id = response['Vpc']['VpcId']
    
    # Enable DNS hostnames and support if requested
    if request.enable_dns_hostnames:
        ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})
    if request.enable_dns_support:
        ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={'Value': True})
    
    # Add tags if provided
    if request.tags:
        tag_list = [{'Key': k, 'Value': v} for k, v in request.tags.items()]
        ec2.create_tags(Resources=[vpc_id], Tags=tag_list)
    
    return {
        "success": True,
        "vpc": response['Vpc']
    }

@mcp.tool()
def list_vpcs(region: str = "us-east-1") -> Dict[str, Any]:
    """
    List all VPCs in the specified region.
    
    Args:
        region: AWS region to list VPCs from
        
    Returns:
        Dictionary containing list of VPCs
    """
    ec2 = aws_clients.get_client('ec2', region)
    
    response = ec2.describe_vpcs()
    
    return {
        "success": True,
        "vpcs": response['Vpcs']
    }

@mcp.tool()
def create_subnet(request: SubnetRequest, region: str = "us-east-1") -> Dict[str, Any]:
    """
    Create a new subnet in a VPC.
    
    Args:
        request: Subnet configuration
        region: AWS region to create the subnet in
        
    Returns:
        Dictionary containing subnet details
    """
    ec2 = aws_clients.get_client('ec2', region)
    
    create_params = {
        'VpcId': request.vpc_id,
        'CidrBlock': request.cidr_block
    }
    
    if request.availability_zone:
        create_params['AvailabilityZone'] = request.availability_zone
    
    response = ec2.create_subnet(**create_params)
    subnet_id = response['Subnet']['SubnetId']
    
    # Configure public IP mapping if requested
    if request.map_public_ip_on_launch:
        ec2.modify_subnet_attribute(
            SubnetId=subnet_id,
            MapPublicIpOnLaunch={'Value': True}
        )
    
    # Add tags if provided
    if request.tags:
        tag_list = [{'Key': k, 'Value': v} for k, v in request.tags.items()]
        ec2.create_tags(Resources=[subnet_id], Tags=tag_list)
    
    return {
        "success": True,
        "subnet": response['Subnet']
    }

# Security Group Management Tools
@mcp.tool()
def create_security_group(request: SecurityGroupRequest, region: str = "us-east-1") -> Dict[str, Any]:
    """
    Create a new security group.
    
    Args:
        request: Security group configuration
        region: AWS region to create the security group in
        
    Returns:
        Dictionary containing security group details
    """
    ec2 = aws_clients.get_client('ec2', region)
    
    response = ec2.create_security_group(
        GroupName=request.group_name,
        Description=request.description,
        VpcId=request.vpc_id
    )
    
    group_id = response['GroupId']
    
    # Add tags if provided
    if request.tags:
        tag_list = [{'Key': k, 'Value': v} for k, v in request.tags.items()]
        ec2.create_tags(Resources=[group_id], Tags=tag_list)
    
    return {
        "success": True,
        "group_id": group_id,
        "security_group": response
    }

@mcp.tool()
def add_security_group_rule(request: SecurityGroupRuleRequest, region: str = "us-east-1") -> Dict[str, Any]:
    """
    Add a rule to a security group.
    
    Args:
        request: Security group rule configuration
        region: AWS region where the security group is located
        
    Returns:
        Dictionary containing rule addition status
    """
    ec2 = aws_clients.get_client('ec2', region)
    
    rule_params = {
        'GroupId': request.group_id,
        'IpProtocol': request.ip_protocol
    }
    
    if request.from_port is not None:
        rule_params['FromPort'] = request.from_port
    if request.to_port is not None:
        rule_params['ToPort'] = request.to_port
    
    if request.cidr_blocks:
        rule_params['CidrIp'] = request.cidr_blocks[0]  # EC2 API takes single CIDR
    elif request.source_security_group_id:
        rule_params['SourceSecurityGroupId'] = request.source_security_group_id
    
    if request.rule_type == "ingress":
        response = ec2.authorize_security_group_ingress(**rule_params)
    else:
        response = ec2.authorize_security_group_egress(**rule_params)
    
    return {
        "success": True,
        "response": response
    }

@mcp.tool()
def list_security_groups(vpc_id: Optional[str] = None, region: str = "us-east-1") -> Dict[str, Any]:
    """
    List security groups, optionally filtered by VPC.
    
    Args:
        vpc_id: Optional VPC ID to filter by
        region: AWS region to list security groups from
        
    Returns:
        Dictionary containing list of security groups
    """
    ec2 = aws_clients.get_client('ec2', region)
    
    describe_params = {}
    if vpc_id:
        describe_params['Filters'] = [{'Name': 'vpc-id', 'Values': [vpc_id]}]
    
    response = ec2.describe_security_groups(**describe_params)
    
    return {
        "success": True,
        "security_groups": response['SecurityGroups']
    }

# RDS Management Tools
@mcp.tool()
def create_rds_instance(request: RDSInstanceRequest, region: str = "us-east-1") -> Dict[str, Any]:
    """
    Create a new RDS database instance.
    
    Args:
        request: RDS instance configuration
        region: AWS region to create the instance in
        
    Returns:
        Dictionary containing RDS instance details
    """
    rds = aws_clients.get_client('rds', region)
    
    create_params = {
        'DBInstanceIdentifier': request.db_instance_identifier,
        'DBInstanceClass': request.db_instance_class,
        'Engine': request.engine,
        'MasterUsername': request.master_username,
        'MasterUserPassword': request.master_user_password,
        'AllocatedStorage': request.allocated_storage,
        'BackupRetentionPeriod': request.backup_retention_period,
        'MultiAZ': request.multi_az,
        'PubliclyAccessible': request.publicly_accessible
    }
    
    if request.vpc_security_group_ids:
        create_params['VpcSecurityGroupIds'] = request.vpc_security_group_ids
    if request.db_subnet_group_name:
        create_params['DBSubnetGroupName'] = request.db_subnet_group_name
    
    response = rds.create_db_instance(**create_params)
    
    # Add tags if provided
    if request.tags:
        db_instance_arn = response['DBInstance']['DBInstanceArn']
        tag_list = [{'Key': k, 'Value': v} for k, v in request.tags.items()]
        rds.add_tags_to_resource(ResourceName=db_instance_arn, Tags=tag_list)
    
    return {
        "success": True,
        "db_instance": response['DBInstance']
    }

@mcp.tool()
def list_rds_instances(region: str = "us-east-1") -> Dict[str, Any]:
    """
    List all RDS database instances.
    
    Args:
        region: AWS region to list instances from
        
    Returns:
        Dictionary containing list of RDS instances
    """
    rds = aws_clients.get_client('rds', region)
    
    response = rds.describe_db_instances()
    
    instances = []
    for db_instance in response['DBInstances']:
        instances.append({
            'DBInstanceIdentifier': db_instance['DBInstanceIdentifier'],
            'DBInstanceClass': db_instance['DBInstanceClass'],
            'Engine': db_instance['Engine'],
            'DBInstanceStatus': db_instance['DBInstanceStatus'],
            'Endpoint': db_instance.get('Endpoint', {}).get('Address'),
            'Port': db_instance.get('Endpoint', {}).get('Port'),
            'AllocatedStorage': db_instance['AllocatedStorage'],
            'MultiAZ': db_instance['MultiAZ']
        })
    
    return {
        "success": True,
        "db_instances": instances
    }

@mcp.tool()
def delete_rds_instance(db_instance_identifier: str, skip_final_snapshot: bool = True, region: str = "us-east-1") -> Dict[str, Any]:
    """
    Delete an RDS database instance.
    
    Args:
        db_instance_identifier: Database instance identifier
        skip_final_snapshot: Whether to skip final snapshot
        region: AWS region where the instance is located
        
    Returns:
        Dictionary containing deletion status
    """
    rds = aws_clients.get_client('rds', region)
    
    delete_params = {
        'DBInstanceIdentifier': db_instance_identifier,
        'SkipFinalSnapshot': skip_final_snapshot
    }
    
    if not skip_final_snapshot:
        delete_params['FinalDBSnapshotIdentifier'] = f"{db_instance_identifier}-final-snapshot-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    response = rds.delete_db_instance(**delete_params)
    
    return {
        "success": True,
        "db_instance": response['DBInstance']
    }

# S3 Management Tools
@mcp.tool()
def create_s3_bucket(request: S3BucketRequest, region: str = "us-east-1") -> Dict[str, Any]:
    """
    Create a new S3 bucket.
    
    Args:
        request: S3 bucket configuration
        region: AWS region to create the bucket in
        
    Returns:
        Dictionary containing bucket creation status
    """
    s3 = aws_clients.get_client('s3', region)
    
    create_params = {'Bucket': request.bucket_name}
    
    # Add region constraint if not us-east-1
    if region != 'us-east-1':
        create_params['CreateBucketConfiguration'] = {'LocationConstraint': region}
    
    response = s3.create_bucket(**create_params)
    
    # Configure versioning if requested
    if request.versioning:
        s3.put_bucket_versioning(
            Bucket=request.bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
    
    # Configure public access if requested
    if request.public_read_access:
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{request.bucket_name}/*"
                }
            ]
        }
        s3.put_bucket_policy(
            Bucket=request.bucket_name,
            Policy=json.dumps(bucket_policy)
        )
    
    # Add tags if provided
    if request.tags:
        tag_set = [{'Key': k, 'Value': v} for k, v in request.tags.items()]
        s3.put_bucket_tagging(
            Bucket=request.bucket_name,
            Tagging={'TagSet': tag_set}
        )
    
    return {
        "success": True,
        "bucket_name": request.bucket_name,
        "location": response.get('Location'),
        "region": region
    }

@mcp.tool()
def list_s3_buckets(region: str = "us-east-1") -> Dict[str, Any]:
    """
    List all S3 buckets.
    
    Args:
        region: AWS region (S3 is global but client needs region)
        
    Returns:
        Dictionary containing list of S3 buckets
    """
    s3 = aws_clients.get_client('s3', region)
    
    response = s3.list_buckets()
    
    return {
        "success": True,
        "buckets": response['Buckets'],
        "owner": response['Owner']
    }

@mcp.tool()
def delete_s3_bucket(bucket_name: str, force: bool = False, region: str = "us-east-1") -> Dict[str, Any]:
    """
    Delete an S3 bucket.
    
    Args:
        bucket_name: Name of the bucket to delete
        force: Whether to force delete (removes all objects first)
        region: AWS region where the bucket is located
        
    Returns:
        Dictionary containing deletion status
    """
    s3 = aws_clients.get_client('s3', region)
    
    if force:
        # Delete all objects first
        try:
            # List and delete all objects
            paginator = s3.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=bucket_name):
                if 'Contents' in page:
                    objects = [{'Key': obj['Key']} for obj in page['Contents']]
                    s3.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': objects}
                    )
            
            # List and delete all object versions if versioning is enabled
            paginator = s3.get_paginator('list_object_versions')
            for page in paginator.paginate(Bucket=bucket_name):
                objects = []
                if 'Versions' in page:
                    objects.extend([{'Key': obj['Key'], 'VersionId': obj['VersionId']} for obj in page['Versions']])
                if 'DeleteMarkers' in page:
                    objects.extend([{'Key': obj['Key'], 'VersionId': obj['VersionId']} for obj in page['DeleteMarkers']])
                
                if objects:
                    s3.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': objects}
                    )
        except ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchBucket':
                raise
    
    # Delete the bucket
    s3.delete_bucket(Bucket=bucket_name)
    
    return {
        "success": True,
        "message": f"Bucket {bucket_name} deleted successfully"
    }

# Lambda Management Tools
@mcp.tool()
def create_lambda_function(request: LambdaFunctionRequest, region: str = "us-east-1") -> Dict[str, Any]:
    """
    Create a new Lambda function.
    
    Args:
        request: Lambda function configuration
        region: AWS region to create the function in
        
    Returns:
        Dictionary containing Lambda function details
    """
    lambda_client = aws_clients.get_client('lambda', region)
    
    create_params = {
        'FunctionName': request.function_name,
        'Runtime': request.runtime,
        'Role': request.role,
        'Handler': request.handler,
        'Code': request.code,
        'Timeout': request.timeout,
        'MemorySize': request.memory_size
    }
    
    if request.description:
        create_params['Description'] = request.description
    if request.environment:
        create_params['Environment'] = {'Variables': request.environment}
    if request.tags:
        create_params['Tags'] = request.tags
    
    response = lambda_client.create_function(**create_params)
    
    return {
        "success": True,
        "function": response
    }

@mcp.tool()
def list_lambda_functions(region: str = "us-east-1") -> Dict[str, Any]:
    """
    List all Lambda functions.
    
    Args:
        region: AWS region to list functions from
        
    Returns:
        Dictionary containing list of Lambda functions
    """
    lambda_client = aws_clients.get_client('lambda', region)
    
    response = lambda_client.list_functions()
    
    return {
        "success": True,
        "functions": response['Functions']
    }

@mcp.tool()
def invoke_lambda_function(function_name: str, payload: Optional[Dict[str, Any]] = None, region: str = "us-east-1") -> Dict[str, Any]:
    """
    Invoke a Lambda function.
    
    Args:
        function_name: Name of the Lambda function
        payload: Optional payload to send to the function
        region: AWS region where the function is located
        
    Returns:
        Dictionary containing invocation response
    """
    lambda_client = aws_clients.get_client('lambda', region)
    
    invoke_params = {'FunctionName': function_name}
    if payload:
        invoke_params['Payload'] = json.dumps(payload)
    
    response = lambda_client.invoke(**invoke_params)
    
    # Read the response payload
    response_payload = response['Payload'].read()
    if response_payload:
        try:
            response_payload = json.loads(response_payload.decode('utf-8'))
        except json.JSONDecodeError:
            response_payload = response_payload.decode('utf-8')
    
    return {
        "success": True,
        "status_code": response['StatusCode'],
        "payload": response_payload,
        "execution_result": response.get('ExecutedVersion'),
        "log_result": response.get('LogResult')
    }

@mcp.tool()
def delete_lambda_function(function_name: str, region: str = "us-east-1") -> Dict[str, Any]:
    """
    Delete a Lambda function.
    
    Args:
        function_name: Name of the Lambda function to delete
        region: AWS region where the function is located
        
    Returns:
        Dictionary containing deletion status
    """
    lambda_client = aws_clients.get_client('lambda', region)
    
    lambda_client.delete_function(FunctionName=function_name)
    
    return {
        "success": True,
        "message": f"Lambda function {function_name} deleted successfully"
    }

# IAM Management Tools
@mcp.tool()
def list_iam_roles(region: str = "us-east-1") -> Dict[str, Any]:
    """
    List all IAM roles.
    
    Args:
        region: AWS region (IAM is global but client needs region)
        
    Returns:
        Dictionary containing list of IAM roles
    """
    iam = aws_clients.get_client('iam', region)
    
    response = iam.list_roles()
    
    return {
        "success": True,
        "roles": response['Roles']
    }

@mcp.tool()
def create_iam_role(role_name: str, assume_role_policy_document: Dict[str, Any], 
                   description: Optional[str] = None, tags: Optional[Dict[str, str]] = None,
                   region: str = "us-east-1") -> Dict[str, Any]:
    """
    Create a new IAM role.
    
    Args:
        role_name: Name of the IAM role
        assume_role_policy_document: Trust policy document
        description: Optional description for the role
        tags: Optional tags for the role
        region: AWS region (IAM is global but client needs region)
        
    Returns:
        Dictionary containing role details
    """
    iam = aws_clients.get_client('iam', region)
    
    create_params = {
        'RoleName': role_name,
        'AssumeRolePolicyDocument': json.dumps(assume_role_policy_document)
    }
    
    if description:
        create_params['Description'] = description
    if tags:
        create_params['Tags'] = [{'Key': k, 'Value': v} for k, v in tags.items()]
    
    response = iam.create_role(**create_params)
    
    return {
        "success": True,
        "role": response['Role']
    }

@mcp.tool()
def attach_role_policy(role_name: str, policy_arn: str, region: str = "us-east-1") -> Dict[str, Any]:
    """
    Attach a managed policy to an IAM role.
    
    Args:
        role_name: Name of the IAM role
        policy_arn: ARN of the policy to attach
        region: AWS region (IAM is global but client needs region)
        
    Returns:
        Dictionary containing attachment status
    """
    iam = aws_clients.get_client('iam', region)
    
    iam.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
    
    return {
        "success": True,
        "message": f"Policy {policy_arn} attached to role {role_name}"
    }

# Utility Tools
@mcp.tool()
def get_caller_identity(region: str = "us-east-1") -> Dict[str, Any]:
    """
    Get information about the AWS caller identity.
    
    Args:
        region: AWS region
        
    Returns:
        Dictionary containing caller identity information
    """
    sts = aws_clients.get_client('sts', region)
    
    response = sts.get_caller_identity()
    
    return {
        "success": True,
        "identity": response
    }

@mcp.tool()
def get_aws_regions(region: str = "us-east-1") -> Dict[str, Any]:
    """
    Get list of available AWS regions.
    
    Args:
        region: AWS region to use for the API call
        
    Returns:
        Dictionary containing list of AWS regions
    """
    ec2 = aws_clients.get_client('ec2', region)
    
    response = ec2.describe_regions()
    
    return {
        "success": True,
        "regions": response['Regions']
    }

@mcp.tool()
@handle_aws_error
def get_availability_zones(region: str = "us-east-1") -> Dict[str, Any]:
    """
    Get list of availability zones in a region.
    
    Args:
        region: AWS region to get availability zones for
        
    Returns:
        Dictionary containing list of availability zones
    """
    ec2 = aws_clients.get_client('ec2', region)
    
    response = ec2.describe_availability_zones()
    
    return {
        "success": True,
        "availability_zones": response['AvailabilityZones']
    }

@mcp.tool()
@handle_aws_error
def get_account_attributes(region: str = "us-east-1") -> Dict[str, Any]:
    """
    Get AWS account attributes and limits.
    
    Args:
        region: AWS region
        
    Returns:
        Dictionary containing account attributes
    """
    ec2 = aws_clients.get_client('ec2', region)
    
    response = ec2.describe_account_attributes()
    
    return {
        "success": True,
        "account_attributes": response['AccountAttributes']
    }

# CloudWatch Management Tools
@mcp.tool()
@handle_aws_error
def list_cloudwatch_alarms(region: str = "us-east-1", state_value: Optional[str] = None) -> Dict[str, Any]:
    """
    List CloudWatch alarms.
    
    Args:
        region: AWS region
        state_value: Optional state filter (OK, ALARM, INSUFFICIENT_DATA)
        
    Returns:
        Dictionary containing list of alarms
    """
    cloudwatch = aws_clients.get_client('cloudwatch', region)
    
    describe_params = {}
    if state_value:
        describe_params['StateValue'] = state_value
    
    response = cloudwatch.describe_alarms(**describe_params)
    
    return {
        "success": True,
        "alarms": response['MetricAlarms']
    }

@mcp.tool()
@handle_aws_error
def get_cloudwatch_metrics(namespace: str, region: str = "us-east-1") -> Dict[str, Any]:
    """
    List CloudWatch metrics for a namespace.
    
    Args:
        namespace: CloudWatch namespace (e.g., AWS/EC2, AWS/RDS)
        region: AWS region
        
    Returns:
        Dictionary containing list of metrics
    """
    cloudwatch = aws_clients.get_client('cloudwatch', region)
    
    response = cloudwatch.list_metrics(Namespace=namespace)
    
    return {
        "success": True,
        "metrics": response['Metrics']
    }

# Auto Scaling Management Tools
@mcp.tool()
@handle_aws_error
def list_auto_scaling_groups(region: str = "us-east-1") -> Dict[str, Any]:
    """
    List Auto Scaling groups.
    
    Args:
        region: AWS region
        
    Returns:
        Dictionary containing list of Auto Scaling groups
    """
    autoscaling = aws_clients.get_client('autoscaling', region)
    
    response = autoscaling.describe_auto_scaling_groups()
    
    return {
        "success": True,
        "auto_scaling_groups": response['AutoScalingGroups']
    }

# ELB Management Tools
@mcp.tool()
@handle_aws_error
def list_load_balancers(region: str = "us-east-1") -> Dict[str, Any]:
    """
    List Elastic Load Balancers (Application and Network Load Balancers).
    
    Args:
        region: AWS region
        
    Returns:
        Dictionary containing list of load balancers
    """
    elbv2 = aws_clients.get_client('elbv2', region)
    
    response = elbv2.describe_load_balancers()
    
    return {
        "success": True,
        "load_balancers": response['LoadBalancers']
    }

# Route 53 Management Tools
@mcp.tool()
@handle_aws_error
def list_hosted_zones(region: str = "us-east-1") -> Dict[str, Any]:
    """
    List Route 53 hosted zones.
    
    Args:
        region: AWS region (Route 53 is global but client needs region)
        
    Returns:
        Dictionary containing list of hosted zones
    """
    route53 = aws_clients.get_client('route53', region)
    
    response = route53.list_hosted_zones()
    
    return {
        "success": True,
        "hosted_zones": response['HostedZones']
    }

@mcp.tool()
@handle_aws_error
def get_iam_role(role_name: str, region: str = "us-east-1") -> Dict[str, Any]:
    """
    Get details of a specific IAM role.
    
    Args:
        role_name: Name of the IAM role
        region: AWS region (IAM is global but client needs region)
        
    Returns:
        Dictionary containing IAM role details
    """
    iam = aws_clients.get_client('iam', region)
    
    response = iam.get_role(RoleName=role_name)
    
    return {
        "success": True,
        "role": response['Role']
    }

# CloudFormation Management Tools
@mcp.tool()
@handle_aws_error
def list_cloudformation_stacks(region: str = "us-east-1") -> Dict[str, Any]:
    """
    List all CloudFormation stacks.
    
    Args:
        region: AWS region to list stacks from
        
    Returns:
        Dictionary containing list of CloudFormation stacks
    """
    cf = aws_clients.get_client('cloudformation', region)
    
    response = cf.list_stacks()
    
    return {
        "success": True,
        "stacks": response['StackSummaries']
    }

@mcp.tool()
@handle_aws_error
def get_cloudformation_stack(stack_name: str, region: str = "us-east-1") -> Dict[str, Any]:
    """
    Get details of a specific CloudFormation stack.
    
    Args:
        stack_name: Name of the CloudFormation stack
        region: AWS region where the stack is located
        
    Returns:
        Dictionary containing CloudFormation stack details
    """
    cf = aws_clients.get_client('cloudformation', region)
    
    response = cf.describe_stacks(StackName=stack_name)
    
    return {
        "success": True,
        "stacks": response['Stacks']
    }

# Utility Tools
@mcp.tool()
@handle_aws_error
def get_aws_regions() -> Dict[str, Any]:
    """
    Get list of all AWS regions.
    
    Returns:
        Dictionary containing list of AWS regions
    """
    ec2 = aws_clients.get_client('ec2', 'us-east-1')
    
    response = ec2.describe_regions()
    
    return {
        "success": True,
        "regions": response['Regions']
    }

@mcp.tool()
@handle_aws_error
def get_availability_zones(region: str = "us-east-1") -> Dict[str, Any]:
    """
    Get list of availability zones for a region.
    
    Args:
        region: AWS region to get availability zones for
        
    Returns:
        Dictionary containing list of availability zones
    """
    ec2 = aws_clients.get_client('ec2', region)
    
    response = ec2.describe_availability_zones()
    
    return {
        "success": True,
        "availability_zones": response['AvailabilityZones']
    }

@mcp.tool()
@handle_aws_error
def get_caller_identity(region: str = "us-east-1") -> Dict[str, Any]:
    """
    Get information about the current AWS caller identity.
    
    Args:
        region: AWS region for the STS client
        
    Returns:
        Dictionary containing caller identity information
    """
    sts = aws_clients.get_client('sts', region)
    
    response = sts.get_caller_identity()
    
    return {
        "success": True,
        "identity": response
    }

def main():
    """Main entry point for the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()