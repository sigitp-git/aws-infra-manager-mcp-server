# AWS Infrastructure Manager MCP Server

A minimal, working Model Context Protocol (MCP) server for managing AWS infrastructure using the FastMCP SDK, developed using Kiro Vibe coding sessions. This project provides essential AWS management tools through a clean, reliable MCP interface.

**Status**: ✅ **Working and Tested** - This MCP server is functional and ready for use with Kiro and other MCP clients.

## Features

This MCP server provides essential AWS management capabilities:

### 🔍 **Core AWS Tools**
- **AWS Identity**: Get caller identity and account information
- **Amazon EC2**: List and filter EC2 instances
- **Amazon VPC**: List VPCs in your account
- **Amazon S3**: List S3 buckets
- **Amazon RDS**: List RDS database instances
- **AWS Lambda**: List Lambda functions
- **AWS Regions**: Get available AWS regions

### 🛡️ **Built-in Features**
- **Error Handling**: Comprehensive AWS API error handling
- **Session Management**: Automatic AWS session and credential management
- **FastMCP Integration**: Full compatibility with FastMCP framework
- **Type Safety**: Proper type hints and validation

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│            AWS Infrastructure Manager MCP Server            │
├─────────────────────────────────────────────────────────────┤
│  Core Services   │  Compute         │  Storage & Functions  │
│  • Identity      │  • EC2           │  • S3                 │
│  • Regions       │  • VPC           │  • RDS                │
│  • Error Handling│                  │  • Lambda             │
└─────────────────────────────────────────────────────────────┘
```

## Installation

This MCP server is designed to be run with `uv`:

```bash
# Clone the repository
git clone <repository-url>
cd aws-infra-manager-mcp-server

# Install dependencies
uv sync

# Test the server (optional)
uv run python -m aws_infra_manager_mcp_server.server --help
```

## Configuration

### MCP Client Configuration

Add to your MCP client configuration (e.g., `.kiro/settings/mcp.json`):

```json
{
  "mcpServers": {
    "aws-infra-manager": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/aws-infra-manager-mcp-server",
        "python",
        "-m",
        "aws_infra_manager_mcp_server.server"
      ],
      "env": {
        "AWS_REGION": "us-east-1"
      },
      "disabled": false,
      "autoApprove": [
        "get_caller_identity",
        "list_ec2_instances",
        "list_vpcs",
        "list_s3_buckets",
        "list_rds_instances",
        "list_lambda_functions",
        "get_aws_regions"
      ]
    }
  }
}
```

### AWS Credentials

Ensure your AWS credentials are configured using one of these methods:

```bash
# AWS CLI configuration
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_REGION=us-east-1

# Or use AWS profiles
export AWS_PROFILE=your-profile-name
```

## AWS Permissions

The server requires the following AWS permissions:

### Required Permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sts:GetCallerIdentity",
        "ec2:DescribeInstances",
        "ec2:DescribeVpcs",
        "ec2:DescribeRegions",
        "s3:ListAllMyBuckets",
        "rds:DescribeDBInstances",
        "lambda:ListFunctions"
      ],
      "Resource": "*"
    }
  ]
}
```

### Minimal IAM Policy
For security, you can create a minimal IAM policy with only the required read permissions above.

## Available Tools

### Core AWS Tools
- `get_caller_identity` - Get information about the current AWS caller identity
- `get_aws_regions` - Get list of all available AWS regions

### EC2 Management
- `list_ec2_instances` - List EC2 instances with optional filtering

### VPC Management
- `list_vpcs` - List all VPCs in the specified region

### S3 Management
- `list_s3_buckets` - List all S3 buckets

### RDS Management
- `list_rds_instances` - List all RDS database instances

### Lambda Management
- `list_lambda_functions` - List all Lambda functions

## Development

```bash
# Install with development dependencies
uv sync --extra dev

# Run the server directly for testing
uv run python -m aws_infra_manager_mcp_server.server

# Run tests (if available)
uv run pytest

# Format code
uv run black .
uv run isort .

# Type checking
uv run mypy .
```

## Testing the Server

You can test the server functionality:

```bash
# Test AWS credentials and connection
uv run python -c "
import sys
sys.path.insert(0, 'src')
from aws_infra_manager_mcp_server.server import aws_clients
try:
    sts = aws_clients.get_client('sts')
    identity = sts.get_caller_identity()
    print(f'✅ AWS connection successful - Account: {identity[\"Account\"]}')
except Exception as e:
    print(f'❌ AWS connection failed: {e}')
"

# Test server import
uv run python -c "
import sys
sys.path.insert(0, 'src')
from aws_infra_manager_mcp_server.server import main, mcp
print(f'✅ Server imported successfully with {len(mcp.tools)} tools')
"
```

## Usage Examples

### Using with Kiro IDE

Once configured, you can use the MCP tools directly in Kiro:

```
# List all EC2 instances
list all my ec2 instances

# Get AWS account information  
get my aws caller identity

# List VPCs
show me all my vpcs

# List S3 buckets
what s3 buckets do I have
```

## Examples

### List EC2 Instances
```python
# List all instances
instances = await mcp_client.call_tool("list_ec2_instances")

# List only running instances
running_instances = await mcp_client.call_tool("list_ec2_instances", {
    "filters": {"instance-state-name": ["running"]}
})
```

### Get AWS Account Information
```python
# Get caller identity
identity = await mcp_client.call_tool("get_caller_identity")
print(f"Account: {identity['identity']['Account']}")
```

### List Resources
```python
# List VPCs
vpcs = await mcp_client.call_tool("list_vpcs")

# List S3 buckets
buckets = await mcp_client.call_tool("list_s3_buckets")

# List RDS instances
databases = await mcp_client.call_tool("list_rds_instances")

# List Lambda functions
functions = await mcp_client.call_tool("list_lambda_functions")

# Get available regions
regions = await mcp_client.call_tool("get_aws_regions")
```

## Security Considerations

- **Read-Only Operations**: Current implementation focuses on read-only operations for safety
- **Least Privilege**: Use minimal IAM permissions as shown in the permissions section
- **Credential Management**: AWS credentials are handled through standard AWS SDK methods
- **Error Handling**: Comprehensive error handling prevents sensitive information leakage
- **No Resource Creation**: Current tools only list/describe resources, no creation or modification

## Troubleshooting

### Common Issues

1. **Import Error**: Ensure the server.py file has a `main()` function
2. **AWS Credentials**: Verify AWS credentials are configured correctly
3. **MCP Connection**: Check that the MCP configuration path is correct
4. **Dependencies**: Run `uv sync` to ensure all dependencies are installed

### Debug Steps

```bash
# Test AWS credentials
aws sts get-caller-identity

# Test server import
uv run python -c "from aws_infra_manager_mcp_server.server import main; print('✅ Import successful')"

# Check MCP tools
uv run python -c "from aws_infra_manager_mcp_server.server import mcp; print(f'Tools: {list(mcp.tools.keys())}')"
```

## License

MIT License
