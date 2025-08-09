"""
Tests for AWS Infrastructure Manager MCP Server
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from botocore.exceptions import ClientError

from aws_infra_manager_mcp_server.server import (
    AWSClientManager,
    launch_ec2_instance,
    list_ec2_instances,
    create_vpc,
    create_s3_bucket,
    list_s3_buckets,
    get_caller_identity,
    EC2InstanceRequest,
    VPCRequest,
    S3BucketRequest
)


class TestAWSClientManager:
    """Test AWS client manager functionality."""
    
    def test_get_session_success(self):
        """Test successful session creation."""
        with patch('boto3.Session') as mock_session_class:
            mock_session = Mock()
            mock_sts = Mock()
            mock_sts.get_caller_identity.return_value = {'Account': '123456789012'}
            mock_session.client.return_value = mock_sts
            mock_session_class.return_value = mock_session
            
            manager = AWSClientManager()
            session = manager.get_session()
            
            assert session == mock_session
            mock_sts.get_caller_identity.assert_called_once()
    
    def test_get_client_caching(self):
        """Test client caching functionality."""
        with patch('boto3.Session') as mock_session_class:
            mock_session = Mock()
            mock_client = Mock()
            mock_sts = Mock()
            mock_sts.get_caller_identity.return_value = {'Account': '123456789012'}
            mock_session.client.side_effect = [mock_sts, mock_client]
            mock_session_class.return_value = mock_session
            
            manager = AWSClientManager()
            
            # First call should create client
            client1 = manager.get_client('ec2', 'us-east-1')
            # Second call should return cached client
            client2 = manager.get_client('ec2', 'us-east-1')
            
            assert client1 == client2
            assert mock_session.client.call_count == 2  # Once for STS, once for EC2


class TestEC2Operations:
    """Test EC2 management operations."""
    
    @patch('aws_infra_manager_mcp_server.server.aws_clients')
    def test_launch_ec2_instance_success(self, mock_aws_clients):
        """Test successful EC2 instance launch."""
        mock_ec2 = Mock()
        mock_ec2.run_instances.return_value = {
            'Instances': [
                {
                    'InstanceId': 'i-1234567890abcdef0',
                    'State': {'Name': 'pending'}
                }
            ]
        }
        mock_aws_clients.get_client.return_value = mock_ec2
        
        request = EC2InstanceRequest(
            image_id='ami-12345678',
            instance_type='t3.micro',
            tags={'Name': 'test-instance'}
        )
        
        result = launch_ec2_instance(request, 'us-east-1')
        
        assert result['success'] is True
        assert len(result['instances']) == 1
        assert result['instance_ids'] == ['i-1234567890abcdef0']
        mock_ec2.run_instances.assert_called_once()
        mock_ec2.create_tags.assert_called_once()
    
    @patch('aws_infra_manager_mcp_server.server.aws_clients')
    def test_list_ec2_instances_success(self, mock_aws_clients):
        """Test successful EC2 instance listing."""
        mock_ec2 = Mock()
        mock_ec2.describe_instances.return_value = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-1234567890abcdef0',
                            'InstanceType': 't3.micro',
                            'State': {'Name': 'running'},
                            'LaunchTime': '2024-01-01T00:00:00Z',
                            'PublicIpAddress': '1.2.3.4',
                            'PrivateIpAddress': '10.0.1.100',
                            'Tags': [{'Key': 'Name', 'Value': 'test-instance'}]
                        }
                    ]
                }
            ]
        }
        mock_aws_clients.get_client.return_value = mock_ec2
        
        result = list_ec2_instances('us-east-1')
        
        assert result['success'] is True
        assert result['count'] == 1
        assert len(result['instances']) == 1
        assert result['instances'][0]['InstanceId'] == 'i-1234567890abcdef0'


class TestVPCOperations:
    """Test VPC management operations."""
    
    @patch('aws_infra_manager_mcp_server.server.aws_clients')
    def test_create_vpc_success(self, mock_aws_clients):
        """Test successful VPC creation."""
        mock_ec2 = Mock()
        mock_ec2.create_vpc.return_value = {
            'Vpc': {
                'VpcId': 'vpc-12345678',
                'CidrBlock': '10.0.0.0/16',
                'State': 'available'
            }
        }
        mock_aws_clients.get_client.return_value = mock_ec2
        
        request = VPCRequest(
            cidr_block='10.0.0.0/16',
            tags={'Name': 'test-vpc'}
        )
        
        result = create_vpc(request, 'us-east-1')
        
        assert result['success'] is True
        assert result['vpc']['VpcId'] == 'vpc-12345678'
        mock_ec2.create_vpc.assert_called_once_with(CidrBlock='10.0.0.0/16')
        mock_ec2.modify_vpc_attribute.assert_called()
        mock_ec2.create_tags.assert_called_once()


class TestS3Operations:
    """Test S3 management operations."""
    
    @patch('aws_infra_manager_mcp_server.server.aws_clients')
    def test_create_s3_bucket_success(self, mock_aws_clients):
        """Test successful S3 bucket creation."""
        mock_s3 = Mock()
        mock_s3.create_bucket.return_value = {
            'Location': 'http://test-bucket.s3.amazonaws.com/'
        }
        mock_aws_clients.get_client.return_value = mock_s3
        
        request = S3BucketRequest(
            bucket_name='test-bucket',
            versioning=True,
            tags={'Environment': 'test'}
        )
        
        result = create_s3_bucket(request, 'us-east-1')
        
        assert result['success'] is True
        assert result['bucket_name'] == 'test-bucket'
        mock_s3.create_bucket.assert_called_once()
        mock_s3.put_bucket_versioning.assert_called_once()
        mock_s3.put_bucket_tagging.assert_called_once()
    
    @patch('aws_infra_manager_mcp_server.server.aws_clients')
    def test_list_s3_buckets_success(self, mock_aws_clients):
        """Test successful S3 bucket listing."""
        mock_s3 = Mock()
        mock_s3.list_buckets.return_value = {
            'Buckets': [
                {
                    'Name': 'test-bucket-1',
                    'CreationDate': '2024-01-01T00:00:00Z'
                },
                {
                    'Name': 'test-bucket-2',
                    'CreationDate': '2024-01-02T00:00:00Z'
                }
            ],
            'Owner': {
                'DisplayName': 'test-user',
                'ID': '123456789012'
            }
        }
        mock_aws_clients.get_client.return_value = mock_s3
        
        result = list_s3_buckets('us-east-1')
        
        assert result['success'] is True
        assert len(result['buckets']) == 2
        assert result['buckets'][0]['Name'] == 'test-bucket-1'


class TestErrorHandling:
    """Test error handling functionality."""
    
    @patch('aws_infra_manager_mcp_server.server.aws_clients')
    def test_client_error_handling(self, mock_aws_clients):
        """Test AWS ClientError handling."""
        mock_sts = Mock()
        error_response = {
            'Error': {
                'Code': 'AccessDenied',
                'Message': 'User is not authorized to perform this action'
            }
        }
        mock_sts.get_caller_identity.side_effect = ClientError(error_response, 'GetCallerIdentity')
        mock_aws_clients.get_client.return_value = mock_sts
        
        result = get_caller_identity('us-east-1')
        
        assert result['error'] is True
        assert result['error_code'] == 'AccessDenied'
        assert 'not authorized' in result['error_message']
    
    @patch('aws_infra_manager_mcp_server.server.aws_clients')
    def test_generic_error_handling(self, mock_aws_clients):
        """Test generic error handling."""
        mock_sts = Mock()
        mock_sts.get_caller_identity.side_effect = Exception('Network timeout')
        mock_aws_clients.get_client.return_value = mock_sts
        
        result = get_caller_identity('us-east-1')
        
        assert result['error'] is True
        assert result['error_message'] == 'Network timeout'


class TestUtilityFunctions:
    """Test utility functions."""
    
    @patch('aws_infra_manager_mcp_server.server.aws_clients')
    def test_get_caller_identity_success(self, mock_aws_clients):
        """Test successful caller identity retrieval."""
        mock_sts = Mock()
        mock_sts.get_caller_identity.return_value = {
            'UserId': 'AIDACKCEVSQ6C2EXAMPLE',
            'Account': '123456789012',
            'Arn': 'arn:aws:iam::123456789012:user/test-user'
        }
        mock_aws_clients.get_client.return_value = mock_sts
        
        result = get_caller_identity('us-east-1')
        
        assert result['success'] is True
        assert result['identity']['Account'] == '123456789012'
        assert 'test-user' in result['identity']['Arn']


if __name__ == '__main__':
    pytest.main([__file__])