# AWS Infrastructure Manager MCP Server

A comprehensive Model Context Protocol (MCP) server for managing AWS infrastructure using the FastMCP SDK.

## Features

This MCP server provides comprehensive management capabilities for:

### 🏗️ **AWS Foundation Services**
- **AWS Control Tower**: Landing zone management, guardrails, and governance
- **AWS Organizations**: Account management, organizational units, and policies
- **AWS Resource Access Manager (RAM)**: Cross-account resource sharing

### 🖥️ **Compute & Networking**
- **Amazon EC2**: Instance management, AMIs, security groups
- **AWS Outposts**: Hybrid cloud infrastructure management
- **Amazon VPC**: Virtual private cloud, subnets, routing, NAT gateways
- **Amazon EKS**: Kubernetes cluster management and operations

### 📊 **Monitoring & Observability**
- **Amazon CloudWatch**: Metrics, logs, alarms, and dashboards
- **Amazon Managed Prometheus**: Prometheus workspaces and queries
- **Amazon Managed Grafana**: Grafana workspaces and dashboards

### 🏗️ **Infrastructure as Code**
- **AWS CloudFormation**: Stack management, templates, and deployments

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                AWS Infrastructure Manager                    │
├─────────────────────────────────────────────────────────────┤
│  Foundation      │  Compute/Network  │  Monitoring/IaC     │
│  • Control Tower │  • EC2            │  • CloudWatch       │
│  • Organizations │  • Outposts       │  • Prometheus        │
│  • RAM           │  • VPC            │  • Grafana           │
│                  │  • EKS            │  • CloudFormation   │
└─────────────────────────────────────────────────────────────┘
```

## Installation

This MCP server is designed to be run with `uv`:

```bash
# Install dependencies
uv sync --extra dev

# Run the server
uv run aws-infra-manager-mcp-server

# Or use the CLI tool
uv run aws-infra-cli --help
uv run aws-infra-manager-mcp-server
```

## Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "aws-infra-manager": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/aws-infra-manager-mcp-server",
        "aws-infra-manager-mcp-server"
      ],
      "env": {
        "AWS_PROFILE": "your-aws-profile",
        "AWS_REGION": "us-east-1"
      },
      "disabled": false,
      "autoApprove": [
        "list_ec2_instances",
        "describe_vpc",
        "get_cloudwatch_metrics",
        "list_eks_clusters"
      ]
    }
  }
}
```

## AWS Permissions

The server requires comprehensive AWS permissions for:

### Foundation Services
- `controltower:*`
- `organizations:*`
- `ram:*`

### Compute & Networking
- `ec2:*`
- `outposts:*`
- `eks:*`

### Monitoring & IaC
- `cloudwatch:*`
- `logs:*`
- `aps:*` (Amazon Managed Prometheus)
- `grafana:*` (Amazon Managed Grafana)
- `cloudformation:*`

### Supporting Services
- `iam:PassRole`
- `sts:GetCallerIdentity`

## Available Tools

### Control Tower & Organizations
- `create_landing_zone` - Create Control Tower landing zone
- `list_organizational_units` - List OUs in organization
- `create_organizational_unit` - Create new OU
- `enable_control` - Enable Control Tower control
- `list_accounts` - List organization accounts

### Resource Access Manager
- `create_resource_share` - Create resource share
- `associate_resource_share` - Associate resources with share
- `get_resource_share_invitations` - List pending invitations

### EC2 Management
- `list_ec2_instances` - List EC2 instances
- `create_ec2_instance` - Launch new instance
- `terminate_ec2_instance` - Terminate instance
- `describe_security_groups` - List security groups
- `create_security_group` - Create security group

### VPC Management
- `list_vpcs` - List VPCs
- `create_vpc` - Create new VPC
- `list_subnets` - List subnets
- `create_subnet` - Create subnet
- `create_nat_gateway` - Create NAT gateway

### EKS Management
- `list_eks_clusters` - List EKS clusters
- `create_eks_cluster` - Create EKS cluster
- `describe_eks_cluster` - Get cluster details
- `list_node_groups` - List node groups
- `create_node_group` - Create node group

### CloudWatch
- `get_cloudwatch_metrics` - Retrieve metrics
- `create_cloudwatch_alarm` - Create alarm
- `list_log_groups` - List log groups
- `create_dashboard` - Create CloudWatch dashboard

### Prometheus & Grafana
- `list_prometheus_workspaces` - List Prometheus workspaces
- `create_prometheus_workspace` - Create workspace
- `query_prometheus` - Execute PromQL query
- `list_grafana_workspaces` - List Grafana workspaces
- `create_grafana_workspace` - Create Grafana workspace

### CloudFormation
- `list_cloudformation_stacks` - List stacks
- `create_cloudformation_stack` - Create stack
- `update_cloudformation_stack` - Update stack
- `delete_cloudformation_stack` - Delete stack
- `describe_stack_events` - Get stack events

### Outposts
- `list_outposts` - List Outposts
- `describe_outpost` - Get Outpost details
- `list_outpost_instances` - List instances on Outpost

## Development

```bash
# Install with development dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Format code
uv run black .
uv run isort .

# Type checking
uv run mypy .
```

## Command Line Interface

The server includes a comprehensive CLI for testing and management:

```bash
# Test AWS connection
uv run aws-infra-cli test-connection

# Perform comprehensive health check
uv run aws-infra-cli health-check

# List resources in different formats
uv run aws-infra-cli list ec2 --region us-west-2
uv run aws-infra-cli list s3 --output table
uv run aws-infra-cli list vpcs --output yaml

# Create resources
uv run aws-infra-cli create vpc --cidr 10.0.0.0/16 --name test-vpc
uv run aws-infra-cli create ec2 --image-id ami-12345678 --instance-type t3.micro --name test-instance
uv run aws-infra-cli create s3 --bucket-name my-unique-bucket --versioning

# Filter resources
uv run aws-infra-cli list ec2 --state running --tag Environment=production

# Get help for any command
uv run aws-infra-cli --help
uv run aws-infra-cli list --help
uv run aws-infra-cli create --help
```

## Interactive Demo

Run the comprehensive demo script to see all features in action:

```bash
# Run interactive demo (dry run - no resources created)
uv run python examples/demo_script.py --dry-run

# Run actual demo (creates real AWS resources)
uv run python examples/demo_script.py --region us-east-1

# The demo creates:
# • VPC with public subnet and security group
# • EC2 instance with web server
# • RDS MySQL database (if possible)
# • S3 bucket with versioning
# • Lambda function (if IAM role available)
# • Demonstrates cleanup procedures
```

## Examples

### Create a VPC with subnets
```python
# Create VPC
vpc_result = await mcp_client.call_tool("create_vpc", {
    "cidr_block": "10.0.0.0/16",
    "name": "my-vpc"
})

# Create public subnet
subnet_result = await mcp_client.call_tool("create_subnet", {
    "vpc_id": vpc_result["vpc_id"],
    "cidr_block": "10.0.1.0/24",
    "availability_zone": "us-east-1a",
    "public": True
})
```

### Launch EC2 instance
```python
instance_result = await mcp_client.call_tool("create_ec2_instance", {
    "image_id": "ami-0abcdef1234567890",
    "instance_type": "t3.micro",
    "subnet_id": subnet_result["subnet_id"],
    "key_name": "my-key-pair"
})
```

### Create EKS cluster
```python
cluster_result = await mcp_client.call_tool("create_eks_cluster", {
    "cluster_name": "my-cluster",
    "version": "1.28",
    "subnet_ids": [subnet_result["subnet_id"]],
    "role_arn": "arn:aws:iam::123456789012:role/EKSServiceRole"
})
```

### Set up monitoring
```python
# Create Prometheus workspace
prometheus_result = await mcp_client.call_tool("create_prometheus_workspace", {
    "alias": "my-prometheus"
})

# Create Grafana workspace
grafana_result = await mcp_client.call_tool("create_grafana_workspace", {
    "name": "my-grafana",
    "account_access_type": "CURRENT_ACCOUNT"
})
```

## Security Considerations

- All AWS API calls use IAM roles with least privilege principles
- Sensitive data is handled securely and not logged
- Resource creation includes proper tagging for governance
- Cross-account operations require explicit permissions

## License

MIT License