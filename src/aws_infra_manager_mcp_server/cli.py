#!/usr/bin/env python3
"""
AWS Infrastructure Manager MCP Server CLI

A command-line interface for testing and managing the MCP server.
"""

import argparse
import json
import sys
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .server import (
    get_caller_identity,
    get_aws_regions,
    get_availability_zones,
    list_ec2_instances,
    list_vpcs,
    list_s3_buckets,
    list_lambda_functions,
    list_iam_roles,
    list_cloudformation_stacks,
    launch_ec2_instance,
    create_vpc,
    create_s3_bucket,
    EC2InstanceRequest,
    VPCRequest,
    S3BucketRequest
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MCPServerCLI:
    """Command-line interface for the MCP server."""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            description='AWS Infrastructure Manager MCP Server CLI',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s test-connection
  %(prog)s list ec2 --region us-west-2
  %(prog)s list s3
  %(prog)s create vpc --cidr 10.0.0.0/16 --name test-vpc
  %(prog)s create ec2 --image-id ami-12345678 --instance-type t3.micro
  %(prog)s health-check
            """
        )
        
        parser.add_argument(
            '--region',
            default='us-east-1',
            help='AWS region (default: us-east-1)'
        )
        
        parser.add_argument(
            '--output',
            choices=['json', 'table', 'yaml'],
            default='json',
            help='Output format (default: json)'
        )
        
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose logging'
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Test connection command
        test_parser = subparsers.add_parser('test-connection', help='Test AWS connection')
        
        # Health check command
        health_parser = subparsers.add_parser('health-check', help='Perform health check')
        
        # List commands
        list_parser = subparsers.add_parser('list', help='List AWS resources')
        list_subparsers = list_parser.add_subparsers(dest='resource', help='Resource type')
        
        # List EC2 instances
        ec2_list_parser = list_subparsers.add_parser('ec2', help='List EC2 instances')
        ec2_list_parser.add_argument('--state', help='Filter by instance state')
        ec2_list_parser.add_argument('--tag', help='Filter by tag (format: key=value)')
        
        # List VPCs
        vpc_list_parser = list_subparsers.add_parser('vpcs', help='List VPCs')
        
        # List S3 buckets
        s3_list_parser = list_subparsers.add_parser('s3', help='List S3 buckets')
        
        # List Lambda functions
        lambda_list_parser = list_subparsers.add_parser('lambda', help='List Lambda functions')
        
        # List IAM roles
        iam_list_parser = list_subparsers.add_parser('iam-roles', help='List IAM roles')
        
        # List CloudFormation stacks
        cf_list_parser = list_subparsers.add_parser('cloudformation', help='List CloudFormation stacks')
        
        # List regions
        regions_parser = list_subparsers.add_parser('regions', help='List AWS regions')
        
        # List availability zones
        az_parser = list_subparsers.add_parser('availability-zones', help='List availability zones')
        
        # Create commands
        create_parser = subparsers.add_parser('create', help='Create AWS resources')
        create_subparsers = create_parser.add_subparsers(dest='resource', help='Resource type')
        
        # Create VPC
        vpc_create_parser = create_subparsers.add_parser('vpc', help='Create VPC')
        vpc_create_parser.add_argument('--cidr', required=True, help='CIDR block (e.g., 10.0.0.0/16)')
        vpc_create_parser.add_argument('--name', help='VPC name tag')
        vpc_create_parser.add_argument('--enable-dns-hostnames', action='store_true', help='Enable DNS hostnames')
        vpc_create_parser.add_argument('--enable-dns-support', action='store_true', help='Enable DNS support')
        
        # Create EC2 instance
        ec2_create_parser = create_subparsers.add_parser('ec2', help='Create EC2 instance')
        ec2_create_parser.add_argument('--image-id', required=True, help='AMI ID')
        ec2_create_parser.add_argument('--instance-type', default='t3.micro', help='Instance type')
        ec2_create_parser.add_argument('--key-name', help='Key pair name')
        ec2_create_parser.add_argument('--security-group-ids', nargs='+', help='Security group IDs')
        ec2_create_parser.add_argument('--subnet-id', help='Subnet ID')
        ec2_create_parser.add_argument('--name', help='Instance name tag')
        
        # Create S3 bucket
        s3_create_parser = create_subparsers.add_parser('s3', help='Create S3 bucket')
        s3_create_parser.add_argument('--bucket-name', required=True, help='S3 bucket name')
        s3_create_parser.add_argument('--versioning', action='store_true', help='Enable versioning')
        s3_create_parser.add_argument('--public-read', action='store_true', help='Enable public read access')
        
        return parser
    
    def run(self, args: Optional[list] = None) -> int:
        """Run the CLI with the given arguments."""
        parsed_args = self.parser.parse_args(args)
        
        if parsed_args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        try:
            if parsed_args.command == 'test-connection':
                return self._test_connection(parsed_args)
            elif parsed_args.command == 'health-check':
                return self._health_check(parsed_args)
            elif parsed_args.command == 'list':
                return self._list_resources(parsed_args)
            elif parsed_args.command == 'create':
                return self._create_resources(parsed_args)
            else:
                self.parser.print_help()
                return 1
                
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return 1
        except Exception as e:
            logger.error(f"Error: {e}")
            if parsed_args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def _test_connection(self, args) -> int:
        """Test AWS connection."""
        print("Testing AWS connection...")
        
        try:
            result = get_caller_identity(args.region)
            
            if result.get('success'):
                identity = result['identity']
                print("✅ AWS connection successful!")
                print(f"Account: {identity.get('Account')}")
                print(f"User/Role: {identity.get('Arn')}")
                print(f"Region: {args.region}")
                return 0
            else:
                print("❌ AWS connection failed!")
                print(f"Error: {result.get('error_message', 'Unknown error')}")
                return 1
                
        except Exception as e:
            print(f"❌ AWS connection failed: {e}")
            return 1
    
    def _health_check(self, args) -> int:
        """Perform comprehensive health check."""
        print("Performing health check...")
        
        checks = [
            ("AWS Connection", lambda: get_caller_identity(args.region)),
            ("List Regions", lambda: get_aws_regions(args.region)),
            ("List Availability Zones", lambda: get_availability_zones(args.region)),
            ("List EC2 Instances", lambda: list_ec2_instances(args.region)),
            ("List VPCs", lambda: list_vpcs(args.region)),
            ("List S3 Buckets", lambda: list_s3_buckets(args.region))
        ]
        
        results = []
        for check_name, check_func in checks:
            try:
                result = check_func()
                success = result.get('success', False)
                results.append((check_name, success, result.get('error_message')))
                status = "✅" if success else "❌"
                print(f"{status} {check_name}")
                if not success and args.verbose:
                    print(f"   Error: {result.get('error_message', 'Unknown error')}")
            except Exception as e:
                results.append((check_name, False, str(e)))
                print(f"❌ {check_name}")
                if args.verbose:
                    print(f"   Error: {e}")
        
        # Summary
        successful = sum(1 for _, success, _ in results if success)
        total = len(results)
        
        print(f"\nHealth Check Summary: {successful}/{total} checks passed")
        
        if successful == total:
            print("🎉 All systems operational!")
            return 0
        else:
            print("⚠️  Some checks failed. See details above.")
            return 1
    
    def _list_resources(self, args) -> int:
        """List AWS resources."""
        if not args.resource:
            print("Error: Please specify a resource type to list")
            return 1
        
        try:
            if args.resource == 'ec2':
                filters = {}
                if args.state:
                    filters['instance-state-name'] = [args.state]
                if args.tag:
                    key, value = args.tag.split('=', 1)
                    filters[f'tag:{key}'] = [value]
                
                result = list_ec2_instances(args.region, filters if filters else None)
                
            elif args.resource == 'vpcs':
                result = list_vpcs(args.region)
                
            elif args.resource == 's3':
                result = list_s3_buckets(args.region)
                
            elif args.resource == 'lambda':
                result = list_lambda_functions(args.region)
                
            elif args.resource == 'iam-roles':
                result = list_iam_roles(args.region)
                
            elif args.resource == 'cloudformation':
                result = list_cloudformation_stacks(args.region)
                
            elif args.resource == 'regions':
                result = get_aws_regions(args.region)
                
            elif args.resource == 'availability-zones':
                result = get_availability_zones(args.region)
                
            else:
                print(f"Error: Unknown resource type '{args.resource}'")
                return 1
            
            self._output_result(result, args.output)
            return 0
            
        except Exception as e:
            print(f"Error listing {args.resource}: {e}")
            return 1
    
    def _create_resources(self, args) -> int:
        """Create AWS resources."""
        if not args.resource:
            print("Error: Please specify a resource type to create")
            return 1
        
        try:
            if args.resource == 'vpc':
                tags = {}
                if args.name:
                    tags['Name'] = args.name
                
                request = VPCRequest(
                    cidr_block=args.cidr,
                    enable_dns_hostnames=args.enable_dns_hostnames,
                    enable_dns_support=args.enable_dns_support,
                    tags=tags if tags else None
                )
                
                result = create_vpc(request, args.region)
                
            elif args.resource == 'ec2':
                tags = {}
                if args.name:
                    tags['Name'] = args.name
                
                request = EC2InstanceRequest(
                    image_id=args.image_id,
                    instance_type=args.instance_type,
                    key_name=args.key_name,
                    security_group_ids=args.security_group_ids,
                    subnet_id=args.subnet_id,
                    tags=tags if tags else None
                )
                
                result = launch_ec2_instance(request, args.region)
                
            elif args.resource == 's3':
                request = S3BucketRequest(
                    bucket_name=args.bucket_name,
                    versioning=args.versioning,
                    public_read_access=args.public_read
                )
                
                result = create_s3_bucket(request, args.region)
                
            else:
                print(f"Error: Unknown resource type '{args.resource}'")
                return 1
            
            if result.get('success'):
                print(f"✅ Successfully created {args.resource}")
                self._output_result(result, args.output)
                return 0
            else:
                print(f"❌ Failed to create {args.resource}")
                print(f"Error: {result.get('error_message', 'Unknown error')}")
                return 1
                
        except Exception as e:
            print(f"Error creating {args.resource}: {e}")
            return 1
    
    def _output_result(self, result: Dict[str, Any], output_format: str):
        """Output result in the specified format."""
        if output_format == 'json':
            print(json.dumps(result, indent=2, default=str))
        elif output_format == 'yaml':
            try:
                import yaml
                print(yaml.dump(result, default_flow_style=False))
            except ImportError:
                print("YAML output requires PyYAML. Install with: pip install PyYAML")
                print(json.dumps(result, indent=2, default=str))
        elif output_format == 'table':
            self._output_table(result)
        else:
            print(json.dumps(result, indent=2, default=str))
    
    def _output_table(self, result: Dict[str, Any]):
        """Output result in table format."""
        if not result.get('success'):
            print(f"Error: {result.get('error_message', 'Unknown error')}")
            return
        
        # Handle different resource types
        if 'instances' in result:
            self._print_ec2_table(result['instances'])
        elif 'vpcs' in result:
            self._print_vpc_table(result['vpcs'])
        elif 'buckets' in result:
            self._print_s3_table(result['buckets'])
        elif 'functions' in result:
            self._print_lambda_table(result['functions'])
        elif 'roles' in result:
            self._print_iam_table(result['roles'])
        elif 'regions' in result:
            self._print_regions_table(result['regions'])
        elif 'availability_zones' in result:
            self._print_az_table(result['availability_zones'])
        else:
            # Fallback to JSON
            print(json.dumps(result, indent=2, default=str))
    
    def _print_ec2_table(self, instances):
        """Print EC2 instances in table format."""
        if not instances:
            print("No EC2 instances found.")
            return
        
        print(f"{'Instance ID':<20} {'Type':<12} {'State':<12} {'Public IP':<15} {'Private IP':<15}")
        print("-" * 80)
        
        for instance in instances:
            print(f"{instance.get('InstanceId', 'N/A'):<20} "
                  f"{instance.get('InstanceType', 'N/A'):<12} "
                  f"{instance.get('State', 'N/A'):<12} "
                  f"{instance.get('PublicIpAddress', 'N/A'):<15} "
                  f"{instance.get('PrivateIpAddress', 'N/A'):<15}")
    
    def _print_vpc_table(self, vpcs):
        """Print VPCs in table format."""
        if not vpcs:
            print("No VPCs found.")
            return
        
        print(f"{'VPC ID':<15} {'CIDR Block':<18} {'State':<12} {'Default':<8}")
        print("-" * 60)
        
        for vpc in vpcs:
            print(f"{vpc.get('VpcId', 'N/A'):<15} "
                  f"{vpc.get('CidrBlock', 'N/A'):<18} "
                  f"{vpc.get('State', 'N/A'):<12} "
                  f"{str(vpc.get('IsDefault', False)):<8}")
    
    def _print_s3_table(self, buckets):
        """Print S3 buckets in table format."""
        if not buckets:
            print("No S3 buckets found.")
            return
        
        print(f"{'Bucket Name':<40} {'Creation Date':<25}")
        print("-" * 70)
        
        for bucket in buckets:
            creation_date = bucket.get('CreationDate', 'N/A')
            if hasattr(creation_date, 'strftime'):
                creation_date = creation_date.strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"{bucket.get('Name', 'N/A'):<40} {str(creation_date):<25}")
    
    def _print_lambda_table(self, functions):
        """Print Lambda functions in table format."""
        if not functions:
            print("No Lambda functions found.")
            return
        
        print(f"{'Function Name':<30} {'Runtime':<15} {'Memory':<8} {'Timeout':<8}")
        print("-" * 70)
        
        for func in functions:
            print(f"{func.get('FunctionName', 'N/A'):<30} "
                  f"{func.get('Runtime', 'N/A'):<15} "
                  f"{func.get('MemorySize', 'N/A'):<8} "
                  f"{func.get('Timeout', 'N/A'):<8}")
    
    def _print_iam_table(self, roles):
        """Print IAM roles in table format."""
        if not roles:
            print("No IAM roles found.")
            return
        
        print(f"{'Role Name':<40} {'Creation Date':<25}")
        print("-" * 70)
        
        for role in roles:
            creation_date = role.get('CreateDate', 'N/A')
            if hasattr(creation_date, 'strftime'):
                creation_date = creation_date.strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"{role.get('RoleName', 'N/A'):<40} {str(creation_date):<25}")
    
    def _print_regions_table(self, regions):
        """Print AWS regions in table format."""
        if not regions:
            print("No regions found.")
            return
        
        print(f"{'Region Name':<20} {'Endpoint':<50}")
        print("-" * 75)
        
        for region in regions:
            print(f"{region.get('RegionName', 'N/A'):<20} "
                  f"{region.get('Endpoint', 'N/A'):<50}")
    
    def _print_az_table(self, azs):
        """Print availability zones in table format."""
        if not azs:
            print("No availability zones found.")
            return
        
        print(f"{'Zone Name':<15} {'State':<12} {'Region':<15}")
        print("-" * 45)
        
        for az in azs:
            print(f"{az.get('ZoneName', 'N/A'):<15} "
                  f"{az.get('State', 'N/A'):<12} "
                  f"{az.get('RegionName', 'N/A'):<15}")


def main():
    """Main entry point for the CLI."""
    cli = MCPServerCLI()
    return cli.run()


if __name__ == '__main__':
    sys.exit(main())