"""
Simple AWS Infrastructure Manager MCP Server for testing

A minimal version to test MCP functionality.
"""

import logging
from typing import Any, Dict

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

@mcp.tool()
def get_caller_identity(region: str = "us-east-1") -> Dict[str, Any]:
    """
    Get information about the current AWS caller identity.
    
    Args:
        region: AWS region
        
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
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"AWS ClientError: {error_code} - {error_message}")
        return {
            "error": True,
            "error_code": error_code,
            "error_message": error_message
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "error": True,
            "error_message": str(e)
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
    try:
        ec2 = aws_clients.get_client('ec2', region)
        response = ec2.describe_regions()
        
        return {
            "success": True,
            "regions": response['Regions']
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"AWS ClientError: {error_code} - {error_message}")
        return {
            "error": True,
            "error_code": error_code,
            "error_message": error_message
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "error": True,
            "error_message": str(e)
        }

@mcp.tool()
def list_ec2_instances(region: str = "us-east-1") -> Dict[str, Any]:
    """
    List EC2 instances.
    
    Args:
        region: AWS region to list instances from
        
    Returns:
        Dictionary containing list of instances
    """
    try:
        ec2 = aws_clients.get_client('ec2', region)
        response = ec2.describe_instances()
        
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
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"AWS ClientError: {error_code} - {error_message}")
        return {
            "error": True,
            "error_code": error_code,
            "error_message": error_message
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "error": True,
            "error_message": str(e)
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
    try:
        s3 = aws_clients.get_client('s3', region)
        response = s3.list_buckets()
        
        return {
            "success": True,
            "buckets": response['Buckets'],
            "owner": response['Owner']
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"AWS ClientError: {error_code} - {error_message}")
        return {
            "error": True,
            "error_code": error_code,
            "error_message": error_message
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "error": True,
            "error_message": str(e)
        }

if __name__ == "__main__":
    mcp.run()