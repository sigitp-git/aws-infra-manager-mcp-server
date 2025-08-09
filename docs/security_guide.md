# AWS Infrastructure Manager MCP Server - Security Guide

This guide covers security best practices, configuration, and considerations when using the AWS Infrastructure Manager MCP Server.

## Table of Contents

- [Authentication & Authorization](#authentication--authorization)
- [IAM Permissions](#iam-permissions)
- [Network Security](#network-security)
- [Data Protection](#data-protection)
- [Monitoring & Auditing](#monitoring--auditing)
- [Secure Configuration](#secure-configuration)
- [Incident Response](#incident-response)

## Authentication & Authorization

### AWS Credentials Management

The MCP server supports multiple AWS credential methods. Choose the most secure option for your environment:

#### 1. IAM Roles (Recommended for EC2/ECS/Lambda)

```bash
# No credentials needed - uses instance/task role
export AWS_REGION=us-east-1
```

**Benefits:**
- Automatic credential rotation
- No long-term credentials stored
- Granular permissions via IAM policies

#### 2. AWS CLI Profiles

```bash
# Configure AWS CLI profile
aws configure --profile mcp-server
export AWS_PROFILE=mcp-server
```

#### 3. Environment Variables (Development Only)

```bash
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_DEFAULT_REGION=us-east-1
```

**⚠️ Warning:** Never use long-term access keys in production environments.

#### 4. AWS SSO/Identity Center

```bash
aws sso login --profile mcp-server
export AWS_PROFILE=mcp-server
```

### MCP Server Authentication

Configure the MCP server with appropriate authentication:

```json
{
  "mcpServers": {
    "aws-infra-manager": {
      "command": "uv",
      "args": ["run", "aws-infra-manager-mcp-server"],
      "env": {
        "AWS_PROFILE": "mcp-server-role",
        "AWS_REGION": "us-east-1"
      },
      "disabled": false,
      "autoApprove": [
        "get_caller_identity",
        "get_aws_regions",
        "list_ec2_instances"
      ]
    }
  }
}
```

## IAM Permissions

### Principle of Least Privilege

Create specific IAM policies for the MCP server with only required permissions:

#### Basic Read-Only Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "rds:Describe*",
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation",
        "lambda:ListFunctions",
        "lambda:GetFunction",
        "iam:ListRoles",
        "iam:GetRole",
        "cloudformation:List*",
        "cloudformation:Describe*",
        "cloudwatch:List*",
        "cloudwatch:Describe*",
        "autoscaling:Describe*",
        "elasticloadbalancing:Describe*",
        "route53:List*",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Infrastructure Management Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:*",
        "rds:*",
        "s3:*",
        "lambda:*",
        "iam:PassRole",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "cloudformation:*",
        "cloudwatch:*",
        "autoscaling:*",
        "elasticloadbalancing:*",
        "route53:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "sts:GetCallerIdentity",
      "Resource": "*"
    }
  ]
}
```

#### Resource-Specific Policies

For production environments, restrict access to specific resources:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:RunInstances",
        "ec2:TerminateInstances",
        "ec2:DescribeInstances"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "ec2:InstanceType": ["t3.micro", "t3.small", "t3.medium"]
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:DeleteBucket",
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::mcp-managed-*"
    }
  ]
}
```

### Service-Linked Roles

Some AWS services require service-linked roles. Ensure these are created:

```bash
# Create service-linked roles if needed
aws iam create-service-linked-role --aws-service-name autoscaling.amazonaws.com
aws iam create-service-linked-role --aws-service-name elasticloadbalancing.amazonaws.com
```

## Network Security

### VPC Security

When creating VPCs and subnets, follow security best practices:

#### Secure VPC Configuration

```python
# Create VPC with private subnets
create_vpc({
    "cidr_block": "10.0.0.0/16",
    "enable_dns_hostnames": True,
    "enable_dns_support": True,
    "tags": {
        "Name": "secure-vpc",
        "Environment": "production"
    }
})

# Create private subnet
create_subnet({
    "vpc_id": "vpc-12345678",
    "cidr_block": "10.0.1.0/24",
    "availability_zone": "us-east-1a",
    "map_public_ip_on_launch": False,  # Keep private
    "tags": {
        "Name": "private-subnet-1a",
        "Type": "private"
    }
})
```

#### Security Group Best Practices

```python
# Restrictive security group
create_security_group({
    "group_name": "web-tier-sg",
    "description": "Web tier security group",
    "vpc_id": "vpc-12345678",
    "tags": {
        "Name": "web-tier-sg",
        "Tier": "web"
    }
})

# Add specific rules only
add_security_group_rule({
    "group_id": "sg-12345678",
    "ip_protocol": "tcp",
    "from_port": 443,
    "to_port": 443,
    "cidr_blocks": ["10.0.0.0/16"],  # Internal only
    "rule_type": "ingress"
})
```

### Network Access Control Lists (NACLs)

Implement defense in depth with NACLs:

- Use default deny-all rules
- Allow only necessary traffic
- Log denied traffic for monitoring

## Data Protection

### Encryption at Rest

Enable encryption for all data storage services:

#### RDS Encryption

```python
create_rds_instance({
    "db_instance_identifier": "secure-db",
    "engine": "mysql",
    "storage_encrypted": True,  # Enable encryption
    "kms_key_id": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
    "backup_retention_period": 30,
    "deletion_protection": True
})
```

#### S3 Encryption

```python
create_s3_bucket({
    "bucket_name": "secure-data-bucket",
    "versioning": True,
    "public_read_access": False,
    "server_side_encryption": {
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "aws:kms",
                "KMSMasterKeyID": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
            }
        }]
    }
})
```

### Encryption in Transit

- Use HTTPS/TLS for all API communications
- Enable SSL/TLS for database connections
- Use VPC endpoints for AWS service communications

### Key Management

- Use AWS KMS for encryption key management
- Rotate keys regularly
- Implement key access policies
- Monitor key usage

## Monitoring & Auditing

### CloudTrail Configuration

Enable comprehensive API logging:

```json
{
  "Trail": {
    "Name": "mcp-server-audit-trail",
    "S3BucketName": "mcp-audit-logs-bucket",
    "IncludeGlobalServiceEvents": true,
    "IsMultiRegionTrail": true,
    "EnableLogFileValidation": true,
    "EventSelectors": [
      {
        "ReadWriteType": "All",
        "IncludeManagementEvents": true,
        "DataResources": [
          {
            "Type": "AWS::S3::Object",
            "Values": ["arn:aws:s3:::*/*"]
          }
        ]
      }
    ]
  }
}
```

### CloudWatch Monitoring

Set up monitoring and alerting:

```python
# Monitor failed API calls
create_cloudwatch_alarm({
    "alarm_name": "MCP-Server-API-Failures",
    "metric_name": "ErrorCount",
    "namespace": "AWS/ApiGateway",
    "statistic": "Sum",
    "threshold": 10,
    "comparison_operator": "GreaterThanThreshold",
    "alarm_actions": ["arn:aws:sns:us-east-1:123456789012:alerts"]
})
```

### Security Monitoring

Monitor for suspicious activities:

- Unusual API call patterns
- Failed authentication attempts
- Resource creation outside business hours
- High-privilege operations

## Secure Configuration

### Environment Variables

Secure environment variable management:

```bash
# Use AWS Systems Manager Parameter Store
aws ssm put-parameter \
    --name "/mcp-server/database/password" \
    --value "SecurePassword123!" \
    --type "SecureString" \
    --key-id "alias/mcp-server-key"

# Retrieve in application
export DB_PASSWORD=$(aws ssm get-parameter \
    --name "/mcp-server/database/password" \
    --with-decryption \
    --query "Parameter.Value" \
    --output text)
```

### Secrets Management

Use AWS Secrets Manager for sensitive data:

```python
import boto3
import json

def get_secret(secret_name, region_name="us-east-1"):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        return json.loads(get_secret_value_response['SecretString'])
    except Exception as e:
        logger.error(f"Error retrieving secret: {e}")
        raise

# Usage
db_credentials = get_secret("mcp-server/database/credentials")
```

### Configuration Validation

Implement configuration validation:

```python
def validate_security_config():
    """Validate security configuration on startup."""
    checks = [
        check_encryption_enabled(),
        check_public_access_blocked(),
        check_logging_enabled(),
        check_backup_configured()
    ]
    
    if not all(checks):
        raise SecurityError("Security configuration validation failed")
```

## Incident Response

### Security Incident Playbook

1. **Detection**
   - Monitor CloudTrail logs
   - Set up CloudWatch alarms
   - Use AWS Config for compliance monitoring

2. **Containment**
   - Disable compromised credentials
   - Isolate affected resources
   - Block suspicious IP addresses

3. **Investigation**
   - Analyze CloudTrail logs
   - Review resource configurations
   - Check for data exfiltration

4. **Recovery**
   - Restore from secure backups
   - Update security configurations
   - Rotate all credentials

5. **Lessons Learned**
   - Document incident details
   - Update security policies
   - Improve monitoring

### Emergency Procedures

#### Credential Compromise

```bash
# Immediately disable access key
aws iam update-access-key \
    --access-key-id AKIAIOSFODNN7EXAMPLE \
    --status Inactive

# Create new access key
aws iam create-access-key --user-name mcp-server-user

# Update MCP server configuration
```

#### Resource Compromise

```bash
# Isolate EC2 instance
aws ec2 modify-instance-attribute \
    --instance-id i-1234567890abcdef0 \
    --groups sg-isolation

# Create forensic snapshot
aws ec2 create-snapshot \
    --volume-id vol-1234567890abcdef0 \
    --description "Forensic snapshot - incident $(date)"
```

## Security Checklist

### Pre-Deployment

- [ ] IAM policies follow least privilege principle
- [ ] All credentials use temporary tokens or roles
- [ ] Encryption enabled for all data stores
- [ ] Network security groups are restrictive
- [ ] CloudTrail logging is enabled
- [ ] Backup and recovery procedures tested

### Post-Deployment

- [ ] Monitor CloudTrail logs regularly
- [ ] Review IAM access patterns
- [ ] Validate resource configurations
- [ ] Test incident response procedures
- [ ] Update security documentation
- [ ] Conduct security reviews

### Ongoing Maintenance

- [ ] Rotate credentials regularly
- [ ] Update IAM policies as needed
- [ ] Review and update security groups
- [ ] Monitor for security advisories
- [ ] Conduct penetration testing
- [ ] Train team on security procedures

## Compliance Considerations

### SOC 2

- Implement access controls
- Enable comprehensive logging
- Document security procedures
- Regular security assessments

### GDPR

- Data encryption at rest and in transit
- Data retention policies
- Right to erasure procedures
- Data processing agreements

### HIPAA

- Encrypt all PHI data
- Implement access controls
- Audit trail requirements
- Business associate agreements

### PCI DSS

- Network segmentation
- Strong access controls
- Regular security testing
- Secure development practices

## Security Tools Integration

### AWS Security Hub

Enable Security Hub for centralized security findings:

```bash
aws securityhub enable-security-hub \
    --enable-default-standards
```

### AWS GuardDuty

Enable threat detection:

```bash
aws guardduty create-detector \
    --enable \
    --finding-publishing-frequency FIFTEEN_MINUTES
```

### AWS Config

Monitor configuration compliance:

```bash
aws configservice put-configuration-recorder \
    --configuration-recorder name=mcp-server-recorder,roleARN=arn:aws:iam::123456789012:role/config-role \
    --recording-group allSupported=true,includeGlobalResourceTypes=true
```

## Contact Information

For security issues or questions:

- **Security Team**: security@yourcompany.com
- **Emergency**: +1-555-SECURITY
- **AWS Support**: Create support case for security issues

Remember: Security is a shared responsibility. While this guide covers AWS infrastructure security, ensure your applications and data handling practices also follow security best practices.