# Infrastructure as Code (Terraform)

## Overview

3-tier architecture (ALB + ECS Fargate + RDS) fully automated with Terraform, featuring environment separation (stg/prod), Secrets Manager integration, and cost optimization strategies.

## Architecture
```
┌─────────────┐
│   Internet  │
└──────┬──────┘
       │
┌──────▼──────────┐
│      ALB        │ ← WAF (prod only)
└──────┬──────────┘
       │
┌──────▼──────────┐
│  ECS Fargate    │
│ ┌──────┐┌─────┐│
│ │React ││Fast││
│ │      ││API ││
│ └──────┘└─────┘│
└──────┬──────────┘
       │
┌──────▼──────────┐
│   RDS MySQL     │ (Private Subnet)
│  (Secrets Mgr)  │
└─────────────────┘
```

## Directory Structure
```
infra/
├── modules/           # Reusable Terraform modules
│   ├── vpc/          # Network infrastructure
│   ├── ecs/          # Container orchestration
│   ├── rds/          # Database
│   ├── secrets/      # Secrets Manager
│   └── waf/          # Web Application Firewall
├── envs/
│   ├── stg/          # Staging environment
│   └── prod/         # Production environment
├── COST.md           # Cost estimation & optimization
└── README.md         # This file
```

## Environment Differences

| Feature | Staging (stg) | Production (prod) |
|---------|---------------|-------------------|
| **RDS** | Single-AZ, No backups | Multi-AZ, 7 days backups |
| **ECS** | 256 CPU / 512 MB, 1 task | 512 CPU / 1024 MB, 2 tasks |
| **WAF** | None | ✅ Enabled (Rate limit + AWS Managed Rules) |
| **Logs** | 7 days retention | 30 days retention |
| **VPC** | 10.10.0.0/16 | 10.20.0.0/16 |
| **Cost** | ~$40-50/month (24/7) | ~$85-100/month (24/7) |

## Prerequisites

- Terraform >= 1.5.0
- AWS CLI configured
- AWS credentials with appropriate permissions
- ECR images pushed (frontend:stg, backend:stg, etc.)

## Quick Start

### 1. Deploy Staging
```bash
cd infra/envs/stg
terraform init
terraform plan
terraform apply
```

### 2. Deploy Production
```bash
cd infra/envs/prod
terraform init
terraform plan
terraform apply
```

### 3. Access Application
```bash
# Get ALB DNS
terraform output alb_dns_name

# Access in browser
http://<alb_dns_name>
```

### 4. Destroy (Cost Optimization)
```bash
terraform destroy
```

## CI/CD

GitHub Actions automatically runs `terraform plan` on pull requests to `infra/**` paths.

### Workflow
1. Create PR with infrastructure changes
2. GitHub Actions runs `terraform plan`
3. Review plan output in PR comment
4. Merge PR after approval
5. Manually run `terraform apply` (not automated for safety)

## Secrets Management

Database credentials are stored in AWS Secrets Manager and injected into ECS tasks at runtime.

**Never commit**:
- `terraform.tfvars` (contains passwords)
- `*.tfstate` (contains sensitive data)
- `.terraform/` (contains provider binaries)

## Cost Optimization

See [COST.md](./COST.md) for detailed cost analysis.

**Key Strategy**: Use `terraform destroy` when not actively using environments.

- **Stg**: Destroy after testing (~$2-3 per session)
- **Prod**: Keep running 24/7 for availability

## Troubleshooting

### ECS Tasks Not Starting
```bash
# Check logs
aws logs tail /ecs/<env>/backend --region ap-northeast-1 --follow
aws logs tail /ecs/<env>/frontend --region ap-northeast-1 --follow
```

### Database Connection Issues
```bash
# Verify security group rules
aws ec2 describe-security-groups --group-ids <sg-id>

# Check RDS endpoint
terraform output rds_endpoint
```

### Secrets Manager Issues
```bash
# Verify secret exists
aws secretsmanager list-secrets --region ap-northeast-1

# Check ECS task role permissions
aws iam get-role-policy --role-name <role-name> --policy-name secrets_access
```

## Module Reusability

All modules under `modules/` can be reused in other projects:
```hcl
module "vpc" {
  source = "../../modules/vpc"
  
  name                   = "my-project-dev"
  vpc_cidr               = "10.30.0.0/16"
  azs                    = ["ap-northeast-1a", "ap-northeast-1c"]
  public_subnet_cidrs    = ["10.30.1.0/24", "10.30.2.0/24"]
  private_subnet_cidrs   = ["10.30.101.0/24", "10.30.102.0/24"]
  tags                   = { Project = "my-project" }
}
```

## Security Best Practices

- ✅ Database in private subnet
- ✅ Secrets Manager for credentials
- ✅ WAF enabled in production
- ✅ Security groups with minimal permissions
- ✅ No NAT Gateway (cost optimization, accept trade-off)
- ✅ HTTPS ready (add ACM + Route53 when domain available)

## Future Enhancements

- [ ] HTTPS with ACM + Route53 (when domain acquired)
- [ ] Auto Scaling for ECS tasks
- [ ] RDS read replicas for prod
- [ ] CloudFront for static assets
- [ ] Automated terraform apply on main branch
- [ ] Multi-region deployment

## License

MIT
