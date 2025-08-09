#!/usr/bin/env python3
"""
AWS Infrastructure Manager MCP Server - Setup Validation Script

This script validates the complete setup including AWS credentials, permissions,
and MCP server functionality.
"""

import sys
import json
import subprocess
import importlib.util
from typing import Dict, List, Tuple, Any
from pathlib import Path

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}\n")

def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

class SetupValidator:
    """Validates the complete MCP server setup."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.project_root = Path(__file__).parent.parent
    
    def run_validation(self) -> bool:
        """Run all validation checks."""
        print_header("AWS Infrastructure Manager MCP Server - Setup Validation")
        
        checks = [
            ("Python Environment", self.check_python_environment),
            ("Project Structure", self.check_project_structure),
            ("Dependencies", self.check_dependencies),
            ("AWS Configuration", self.check_aws_configuration),
            ("AWS Permissions", self.check_aws_permissions),
            ("MCP Server", self.check_mcp_server),
            ("CLI Tool", self.check_cli_tool),
            ("Documentation", self.check_documentation)
        ]
        
        for check_name, check_func in checks:
            print_info(f"Running {check_name} check...")
            try:
                check_func()
                print_success(f"{check_name} check passed")
            except Exception as e:
                self.errors.append(f"{check_name}: {str(e)}")
                print_error(f"{check_name} check failed: {str(e)}")
        
        self.print_summary()
        return len(self.errors) == 0
    
    def check_python_environment(self):
        """Check Python version and virtual environment."""
        # Check Python version
        if sys.version_info < (3, 10):
            raise Exception(f"Python 3.10+ required, found {sys.version_info.major}.{sys.version_info.minor}")
        
        # Check if uv is available
        try:
            result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                self.warnings.append("uv package manager not found, consider installing for better performance")
        except FileNotFoundError:
            self.warnings.append("uv package manager not found, consider installing for better performance")
    
    def check_project_structure(self):
        """Check project directory structure."""
        required_files = [
            'pyproject.toml',
            'README.md',
            'LICENSE',
            'src/aws_infra_manager_mcp_server/__init__.py',
            'src/aws_infra_manager_mcp_server/server.py',
            'src/aws_infra_manager_mcp_server/cli.py',
            'tests/test_server.py',
            'examples/basic_usage.py',
            'examples/demo_script.py',
            'docs/api_reference.md',
            'docs/security_guide.md'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            raise Exception(f"Missing required files: {', '.join(missing_files)}")
    
    def check_dependencies(self):
        """Check if required dependencies are installed."""
        required_packages = [
            'fastmcp',
            'boto3',
            'botocore',
            'pydantic'
        ]
        
        missing_packages = []
        for package in required_packages:
            spec = importlib.util.find_spec(package)
            if spec is None:
                missing_packages.append(package)
        
        if missing_packages:
            raise Exception(f"Missing required packages: {', '.join(missing_packages)}. Run 'uv sync' to install.")
    
    def check_aws_configuration(self):
        """Check AWS configuration and credentials."""
        try:
            import boto3
            from botocore.exceptions import NoCredentialsError, ClientError
            
            # Try to create a session and get caller identity
            session = boto3.Session()
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            
            print_info(f"AWS Account: {identity.get('Account')}")
            print_info(f"AWS User/Role: {identity.get('Arn')}")
            
        except NoCredentialsError:
            raise Exception("AWS credentials not configured. Run 'aws configure' or set environment variables.")
        except ClientError as e:
            raise Exception(f"AWS credentials invalid: {e}")
        except Exception as e:
            raise Exception(f"AWS configuration error: {e}")
    
    def check_aws_permissions(self):
        """Check basic AWS permissions."""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            session = boto3.Session()
            
            # Test basic permissions
            permission_tests = [
                ('EC2', 'ec2', 'describe_instances'),
                ('S3', 's3', 'list_buckets'),
                ('IAM', 'iam', 'list_roles'),
                ('Lambda', 'lambda', 'list_functions')
            ]
            
            failed_permissions = []
            for service_name, service, operation in permission_tests:
                try:
                    client = session.client(service)
                    getattr(client, operation)()
                    print_info(f"{service_name} permissions: OK")
                except ClientError as e:
                    if e.response['Error']['Code'] in ['AccessDenied', 'UnauthorizedOperation']:
                        failed_permissions.append(f"{service_name}:{operation}")
                    else:
                        # Other errors might be OK (like no resources found)
                        print_info(f"{service_name} permissions: OK")
                except Exception:
                    failed_permissions.append(f"{service_name}:{operation}")
            
            if failed_permissions:
                self.warnings.append(f"Limited permissions for: {', '.join(failed_permissions)}")
                
        except Exception as e:
            raise Exception(f"Permission check failed: {e}")
    
    def check_mcp_server(self):
        """Check MCP server functionality."""
        try:
            # Import the server module
            sys.path.insert(0, str(self.project_root / 'src'))
            from aws_infra_manager_mcp_server.server import get_caller_identity, mcp
            
            # Test a basic function
            result = get_caller_identity()
            if not result.get('success'):
                raise Exception(f"MCP server function failed: {result.get('error_message')}")
            
            # Check if MCP instance is properly configured
            if not hasattr(mcp, 'tools') or len(mcp.tools) == 0:
                raise Exception("MCP server has no tools registered")
            
            print_info(f"MCP server has {len(mcp.tools)} tools registered")
            
        except ImportError as e:
            raise Exception(f"Cannot import MCP server: {e}")
        except Exception as e:
            raise Exception(f"MCP server check failed: {e}")
    
    def check_cli_tool(self):
        """Check CLI tool functionality."""
        try:
            # Try to run the CLI help command
            result = subprocess.run([
                sys.executable, '-m', 'aws_infra_manager_mcp_server.cli', '--help'
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                raise Exception(f"CLI tool failed: {result.stderr}")
            
            if 'AWS Infrastructure Manager MCP Server CLI' not in result.stdout:
                raise Exception("CLI tool output doesn't match expected format")
                
        except FileNotFoundError:
            raise Exception("Python interpreter not found")
        except Exception as e:
            raise Exception(f"CLI tool check failed: {e}")
    
    def check_documentation(self):
        """Check documentation completeness."""
        doc_files = [
            ('API Reference', 'docs/api_reference.md'),
            ('Security Guide', 'docs/security_guide.md'),
            ('Deployment Guide', 'examples/deployment_guide.md'),
            ('Basic Usage', 'examples/basic_usage.py'),
            ('Demo Script', 'examples/demo_script.py')
        ]
        
        missing_docs = []
        for doc_name, doc_path in doc_files:
            full_path = self.project_root / doc_path
            if not full_path.exists():
                missing_docs.append(doc_name)
            elif full_path.stat().st_size < 1000:  # Less than 1KB
                self.warnings.append(f"{doc_name} documentation seems incomplete")
        
        if missing_docs:
            raise Exception(f"Missing documentation: {', '.join(missing_docs)}")
    
    def print_summary(self):
        """Print validation summary."""
        print_header("Validation Summary")
        
        if not self.errors and not self.warnings:
            print_success("🎉 All checks passed! Your setup is ready to use.")
            print_info("You can now:")
            print_info("  • Run the MCP server: uv run aws-infra-manager-mcp-server")
            print_info("  • Use the CLI: uv run aws-infra-cli test-connection")
            print_info("  • Try the demo: uv run python examples/demo_script.py --dry-run")
        else:
            if self.errors:
                print_error(f"Found {len(self.errors)} error(s):")
                for error in self.errors:
                    print(f"  • {error}")
            
            if self.warnings:
                print_warning(f"Found {len(self.warnings)} warning(s):")
                for warning in self.warnings:
                    print(f"  • {warning}")
            
            if self.errors:
                print_error("❌ Setup validation failed. Please fix the errors above.")
            else:
                print_warning("⚠️  Setup validation completed with warnings.")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a detailed validation report."""
        return {
            'timestamp': subprocess.run(['date'], capture_output=True, text=True).stdout.strip(),
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'project_root': str(self.project_root),
            'errors': self.errors,
            'warnings': self.warnings,
            'status': 'PASSED' if not self.errors else 'FAILED'
        }

def main():
    """Main entry point."""
    validator = SetupValidator()
    success = validator.run_validation()
    
    # Generate report if requested
    if '--report' in sys.argv:
        report = validator.generate_report()
        report_file = validator.project_root / 'validation_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print_info(f"Detailed report saved to: {report_file}")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())