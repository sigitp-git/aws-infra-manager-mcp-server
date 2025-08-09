"""
Integration tests for AWS Infrastructure Manager MCP Server

These tests verify the complete functionality of the MCP server
with real AWS services (using mocked responses).
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from aws_infra_manager_mcp_server.server import (
    mcp,
    get_caller_identity,
    get_aws_regions,
    launch_ec2_instance,
    create_vpc,
    create_s3_bucket,
    create_lambda_function,
    list_ec2_instances,
    list_s3_buckets,
    EC2InstanceRequest,
    VPCRequest,
    S3BucketRequest,
    LambdaFunctionRequest
)


class TestMCPServerIntegration:
    """Integration tests for the complete MCP server."""
    
    def test_mcp_server_initialization(self):
        """Test that the MCP server initializes correctly."""
        assert mcp is not None
        assert hasattr(mcp, 'tools')
        assert len(mcp.tools) > 0
        
        # Check that key tools are registered
        tool_names = [tool.name for tool in mcp.tools]
        expected_tools = [
            'get_caller_identity',
            'get_aws_regions',
            'launch_ec2_instance',
            'list_ec2_instances',
            'create_vpc',
            'list_vpcs',
            'create_s3_bucket',
            'list_s3_buckets'
        ]
        
        for tool in expected_tools:
            assert tool in tool_names, f"Tool {tool} not found in registered tools"
    
    @patch('aws_infra_manager_mcp_server.server.aws_clients')
    def test_complete_infrastructure_workflow(self, mock_aws_clients):
        """Test a complete infrastructure creation workflow."""
        # Mock AWS clients
        mock_sts = Mock()
        mock_ec2 = Mock()
        mock_s3 = Mock()
        
        mock_aws_clients.get_client.side_effect = lambda service, region=None: {
            'sts': mock_sts,
            'ec2': mock_ec2,
            's3': mock_s3
        }[service]
        
        # Mock STS response
        mock_sts.get_caller_identity.return_value = {
            'UserId': 'AIDACKCEVSQ6C2EXAMPLE',
            'Account': '123456789012',
            'Arn': 'arn:aws:iam::123456789012:user/test-user'
        }
        
        # Mock EC2 responses
        mock_ec2.describe_regions.return_value = {
            'Regions': [
                {'RegionName': 'us-east-1', 'Endpoint': 'ec2.us-east-1.amazonaws.com'},
                {'RegionName': 'us-west-2', 'Endpoint': 'ec2.us-west-2.amazonaws.com'}
            ]
        }
        
        mock_ec2.create_vpc.return_value = {
            'Vpc': {
                'VpcId': 'vpc-12345678',
                'CidrBlock': '10.0.0.0/16',
                'State': 'available'
            }
        }
        
        mock_ec2.run_instances.return_value = {
            'Instances': [
                {
                    'InstanceId': 'i-1234567890abcdef0',
                    'State': {'Name': 'pending'},
                    'InstanceType': 't3.micro'
                }
            ]
        }
        
        mock_ec2.describe_instances.return_value = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-1234567890abcdef0',
                            'InstanceType': 't3.micro',
                            'State': {'Name': 'running'},
                            'LaunchTime': datetime.now(),
                            'PublicIpAddress': '1.2.3.4',
                            'PrivateIpAddress': '10.0.1.100',
                            'Tags': []
                        }
                    ]
                }
            ]
        }
        
        # Mock S3 responses
        mock_s3.create_bucket.return_value = {
            'Location': 'http://test-bucket.s3.amazonaws.com/'
        }
        
        mock_s3.list_buckets.return_value = {
            'Buckets': [
                {
                    'Name': 'test-bucket',
                    'CreationDate': datetime.now()
                }
            ],
            'Owner': {
                'DisplayName': 'test-user',
                'ID': '123456789012'
            }
        }
        
        # Test workflow
        # 1. Verify AWS connection
        identity_result = get_caller_identity()
        assert identity_result['success'] is True
        assert identity_result['identity']['Account'] == '123456789012'
        
        # 2. Get regions
        regions_result = get_aws_regions()
        assert regions_result['success'] is True
        assert len(regions_result['regions']) == 2
        
        # 3. Create VPC
        vpc_request = VPCRequest(
            cidr_block='10.0.0.0/16',
            tags={'Name': 'test-vpc'}
        )
        vpc_result = create_vpc(vpc_request)
        assert vpc_result['success'] is True
        assert vpc_result['vpc']['VpcId'] == 'vpc-12345678'
        
        # 4. Launch EC2 instance
        ec2_request = EC2InstanceRequest(
            image_id='ami-12345678',
            instance_type='t3.micro',
            tags={'Name': 'test-instance'}
        )
        ec2_result = launch_ec2_instance(ec2_request)
        assert ec2_result['success'] is True
        assert len(ec2_result['instance_ids']) == 1
        
        # 5. List EC2 instances
        instances_result = list_ec2_instances()
        assert instances_result['success'] is True
        assert instances_result['count'] == 1
        
        # 6. Create S3 bucket
        s3_request = S3BucketRequest(
            bucket_name='test-bucket',
            versioning=True
        )
        s3_result = create_s3_bucket(s3_request)
        assert s3_result['success'] is True
        assert s3_result['bucket_name'] == 'test-bucket'
        
        # 7. List S3 buckets
        buckets_result = list_s3_buckets()
        assert buckets_result['success'] is True
        assert len(buckets_result['buckets']) == 1
    
    @patch('aws_infra_manager_mcp_server.server.aws_clients')
    def test_error_handling_workflow(self, mock_aws_clients):
        """Test error handling in various scenarios."""
        # Mock AWS client that raises errors
        mock_ec2 = Mock()
        mock_aws_clients.get_client.return_value = mock_ec2
        
        # Test ClientError handling
        from botocore.exceptions import ClientError
        error_response = {
            'Error': {
                'Code': 'AccessDenied',
                'Message': 'User is not authorized to perform this action'
            }
        }
        mock_ec2.describe_instances.side_effect = ClientError(error_response, 'DescribeInstances')
        
        result = list_ec2_instances()
        assert result['error'] is True
        assert result['error_code'] == 'AccessDenied'
        assert 'not authorized' in result['error_message']
        
        # Test generic exception handling
        mock_ec2.describe_instances.side_effect = Exception('Network timeout')
        
        result = list_ec2_instances()
        assert result['error'] is True
        assert result['error_message'] == 'Network timeout'
    
    @patch('aws_infra_manager_mcp_server.server.aws_clients')
    def test_lambda_function_workflow(self, mock_aws_clients):
        """Test Lambda function creation and management."""
        mock_lambda = Mock()
        mock_aws_clients.get_client.return_value = mock_lambda
        
        # Mock Lambda responses
        mock_lambda.create_function.return_value = {
            'FunctionName': 'test-function',
            'FunctionArn': 'arn:aws:lambda:us-east-1:123456789012:function:test-function',
            'Runtime': 'python3.9',
            'Role': 'arn:aws:iam::123456789012:role/lambda-role',
            'Handler': 'lambda_function.lambda_handler',
            'CodeSize': 1024,
            'State': 'Active'
        }
        
        mock_lambda.list_functions.return_value = {
            'Functions': [
                {
                    'FunctionName': 'test-function',
                    'Runtime': 'python3.9',
                    'Role': 'arn:aws:iam::123456789012:role/lambda-role'
                }
            ]
        }
        
        # Test Lambda function creation
        lambda_request = LambdaFunctionRequest(
            function_name='test-function',
            runtime='python3.9',
            role='arn:aws:iam::123456789012:role/lambda-role',
            handler='lambda_function.lambda_handler',
            code={'ZipFile': b'test code'},
            tags={'Environment': 'test'}
        )
        
        result = create_lambda_function(lambda_request)
        assert result['success'] is True
        assert result['function']['FunctionName'] == 'test-function'
        
        # Verify function creation was called with correct parameters
        mock_lambda.create_function.assert_called_once()
        call_args = mock_lambda.create_function.call_args[1]
        assert call_args['FunctionName'] == 'test-function'
        assert call_args['Runtime'] == 'python3.9'
        assert call_args['Tags'] == {'Environment': 'test'}
    
    def test_request_validation(self):
        """Test request validation using Pydantic models."""
        # Test valid EC2 request
        valid_request = EC2InstanceRequest(
            image_id='ami-12345678',
            instance_type='t3.micro'
        )
        assert valid_request.image_id == 'ami-12345678'
        assert valid_request.instance_type == 't3.micro'
        assert valid_request.min_count == 1  # Default value
        
        # Test invalid EC2 request (missing required field)
        with pytest.raises(Exception):
            EC2InstanceRequest(instance_type='t3.micro')  # Missing image_id
        
        # Test VPC request validation
        valid_vpc_request = VPCRequest(cidr_block='10.0.0.0/16')
        assert valid_vpc_request.cidr_block == '10.0.0.0/16'
        assert valid_vpc_request.enable_dns_hostnames is True  # Default value
        
        # Test S3 request validation
        valid_s3_request = S3BucketRequest(bucket_name='test-bucket')
        assert valid_s3_request.bucket_name == 'test-bucket'
        assert valid_s3_request.versioning is False  # Default value
    
    @patch('aws_infra_manager_mcp_server.server.aws_clients')
    def test_resource_tagging(self, mock_aws_clients):
        """Test that resource tagging works correctly."""
        mock_ec2 = Mock()
        mock_aws_clients.get_client.return_value = mock_ec2
        
        # Mock EC2 responses
        mock_ec2.run_instances.return_value = {
            'Instances': [
                {
                    'InstanceId': 'i-1234567890abcdef0',
                    'State': {'Name': 'pending'}
                }
            ]
        }
        
        # Test EC2 instance with tags
        ec2_request = EC2InstanceRequest(
            image_id='ami-12345678',
            instance_type='t3.micro',
            tags={
                'Name': 'test-instance',
                'Environment': 'production',
                'Team': 'infrastructure'
            }
        )
        
        result = launch_ec2_instance(ec2_request)
        assert result['success'] is True
        
        # Verify that create_tags was called
        mock_ec2.create_tags.assert_called_once()
        call_args = mock_ec2.create_tags.call_args[1]
        
        # Check that all tags were included
        expected_tags = [
            {'Key': 'Name', 'Value': 'test-instance'},
            {'Key': 'Environment', 'Value': 'production'},
            {'Key': 'Team', 'Value': 'infrastructure'}
        ]
        
        assert len(call_args['Tags']) == 3
        for tag in expected_tags:
            assert tag in call_args['Tags']
    
    @patch('aws_infra_manager_mcp_server.server.aws_clients')
    def test_multi_region_support(self, mock_aws_clients):
        """Test that multi-region operations work correctly."""
        mock_ec2_us_east = Mock()
        mock_ec2_us_west = Mock()
        
        def get_client_side_effect(service, region=None):
            if region == 'us-east-1':
                return mock_ec2_us_east
            elif region == 'us-west-2':
                return mock_ec2_us_west
            else:
                return mock_ec2_us_east  # Default
        
        mock_aws_clients.get_client.side_effect = get_client_side_effect
        
        # Mock different responses for different regions
        mock_ec2_us_east.describe_instances.return_value = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-east-123',
                            'InstanceType': 't3.micro',
                            'State': {'Name': 'running'},
                            'LaunchTime': datetime.now(),
                            'Tags': []
                        }
                    ]
                }
            ]
        }
        
        mock_ec2_us_west.describe_instances.return_value = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-west-456',
                            'InstanceType': 't3.small',
                            'State': {'Name': 'running'},
                            'LaunchTime': datetime.now(),
                            'Tags': []
                        }
                    ]
                }
            ]
        }
        
        # Test listing instances in different regions
        us_east_result = list_ec2_instances('us-east-1')
        assert us_east_result['success'] is True
        assert us_east_result['instances'][0]['InstanceId'] == 'i-east-123'
        
        us_west_result = list_ec2_instances('us-west-2')
        assert us_west_result['success'] is True
        assert us_west_result['instances'][0]['InstanceId'] == 'i-west-456'
        
        # Verify that the correct regional clients were called
        mock_ec2_us_east.describe_instances.assert_called_once()
        mock_ec2_us_west.describe_instances.assert_called_once()
    
    @patch('aws_infra_manager_mcp_server.server.aws_clients')
    def test_filtering_functionality(self, mock_aws_clients):
        """Test resource filtering functionality."""
        mock_ec2 = Mock()
        mock_aws_clients.get_client.return_value = mock_ec2
        
        # Mock EC2 response
        mock_ec2.describe_instances.return_value = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-running-123',
                            'InstanceType': 't3.micro',
                            'State': {'Name': 'running'},
                            'LaunchTime': datetime.now(),
                            'Tags': [{'Key': 'Environment', 'Value': 'production'}]
                        }
                    ]
                }
            ]
        }
        
        # Test filtering by instance state
        filters = {'instance-state-name': ['running']}
        result = list_ec2_instances('us-east-1', filters)
        
        assert result['success'] is True
        assert result['count'] == 1
        
        # Verify that filters were passed to AWS API
        mock_ec2.describe_instances.assert_called_once()
        call_args = mock_ec2.describe_instances.call_args[1]
        
        assert 'Filters' in call_args
        assert len(call_args['Filters']) == 1
        assert call_args['Filters'][0]['Name'] == 'instance-state-name'
        assert call_args['Filters'][0]['Values'] == ['running']


class TestCLIIntegration:
    """Integration tests for the CLI tool."""
    
    def test_cli_import(self):
        """Test that the CLI module can be imported."""
        from aws_infra_manager_mcp_server.cli import MCPServerCLI
        
        cli = MCPServerCLI()
        assert cli is not None
        assert hasattr(cli, 'parser')
        assert hasattr(cli, 'run')
    
    def test_cli_help(self):
        """Test CLI help functionality."""
        from aws_infra_manager_mcp_server.cli import MCPServerCLI
        
        cli = MCPServerCLI()
        
        # Test that help doesn't raise an exception
        try:
            cli.run(['--help'])
        except SystemExit as e:
            # argparse calls sys.exit(0) for help
            assert e.code == 0
    
    @patch('aws_infra_manager_mcp_server.cli.get_caller_identity')
    def test_cli_test_connection(self, mock_get_caller_identity):
        """Test CLI connection testing."""
        from aws_infra_manager_mcp_server.cli import MCPServerCLI
        
        # Mock successful connection
        mock_get_caller_identity.return_value = {
            'success': True,
            'identity': {
                'Account': '123456789012',
                'Arn': 'arn:aws:iam::123456789012:user/test-user'
            }
        }
        
        cli = MCPServerCLI()
        result = cli.run(['test-connection'])
        
        assert result == 0  # Success
        mock_get_caller_identity.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])