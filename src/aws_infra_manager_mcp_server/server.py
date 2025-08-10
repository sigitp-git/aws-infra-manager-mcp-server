"""
AWS Infrastructure Manager MCP Server - Clean Version

A minimal MCP server for managing AWS infrastructure using the FastMCP SDK.
"""

import logging
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    """Handle AWS errors consistently."""
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

# Essential AWS Tools
@mcp.tool()
def get_caller_identity(region: str = "us-east-1") -> Dict[str, Any]:
    """
    Get information about the current AWS caller identity.
    
    Args:
        region: AWS region for the STS client
        
    Returns:
        Dictionary containing caller identity information
    """
    try:
        sts = aws_clients.get_client('sts', region)
        response = sts.get_caller_identity()
        
        return {
            "success": True,
            "identity": response
        }
    except Exception as e:
        return handle_aws_error_inline("get_caller_identity", e)

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
    try:
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
    except Exception as e:
        return handle_aws_error_inline("list_ec2_instances", e)

@mcp.tool()
def list_vpcs(region: str = "us-east-1") -> Dict[str, Any]:
    """
    List all VPCs in the specified region.
    
    Args:
        region: AWS region to list VPCs from
        
    Returns:
        Dictionary containing list of VPCs
    """
    try:
        ec2 = aws_clients.get_client('ec2', region)
        response = ec2.describe_vpcs()
        
        return {
            "success": True,
            "vpcs": response['Vpcs']
        }
    except Exception as e:
        return handle_aws_error_inline("list_vpcs", e)

@mcp.tool()
def list_s3_buckets(region: str = "us-east-1") -> Dict[str, Any]:
    """
    List all S3 buckets.
    
    Args:
        region: AWS region (S3 is global but client needs region)
        
    Returns:
        Dictionary containing list of S3 buckets
    """
    try:
        s3 = aws_clients.get_client('s3', region)
        response = s3.list_buckets()
        
        return {
            "success": True,
            "buckets": response['Buckets'],
            "owner": response['Owner']
        }
    except Exception as e:
        return handle_aws_error_inline("list_s3_buckets", e)

@mcp.tool()
def list_rds_instances(region: str = "us-east-1") -> Dict[str, Any]:
    """
    List all RDS database instances.
    
    Args:
        region: AWS region to list instances from
        
    Returns:
        Dictionary containing list of RDS instances
    """
    try:
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
    except Exception as e:
        return handle_aws_error_inline("list_rds_instances", e)

@mcp.tool()
def list_lambda_functions(region: str = "us-east-1") -> Dict[str, Any]:
    """
    List all Lambda functions.
    
    Args:
        region: AWS region to list functions from
        
    Returns:
        Dictionary containing list of Lambda functions
    """
    try:
        lambda_client = aws_clients.get_client('lambda', region)
        response = lambda_client.list_functions()
        
        return {
            "success": True,
            "functions": response['Functions']
        }
    except Exception as e:
        return handle_aws_error_inline("list_lambda_functions", e)

@mcp.tool()
def get_aws_regions() -> Dict[str, Any]:
    """
    Get list of all AWS regions.
    
    Returns:
        Dictionary containing list of AWS regions
    """
    try:
        ec2 = aws_clients.get_client('ec2', 'us-east-1')
        response = ec2.describe_regions()
        
        return {
            "success": True,
            "regions": response['Regions']
        }
    except Exception as e:
        return handle_aws_error_inline("get_aws_regions", e)

def main():
    """Main entry point for the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()