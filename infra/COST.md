# AWS Cost Estimation

## Environment Comparison

### Staging (stg)

| Resource | Configuration | Monthly Cost |
|----------|--------------|--------------|
| RDS MySQL | db.t4g.micro, Single-AZ, No backups | ~$12-15 |
| ECS Fargate | 256 CPU / 512 MB, 1 task | ~$8-10 |
| ALB | Application Load Balancer | ~$20-25 |
| Secrets Manager | 1 secret | ~$0.40 |
| CloudWatch Logs | 7 days retention | ~$1-2 |
| NAT Gateway | None (Public subnet for ECS) | $0 |
| **Total (stg)** | | **~$40-50/month** |

### Production (prod)

| Resource | Configuration | Monthly Cost |
|----------|--------------|--------------|
| RDS MySQL | db.t4g.micro, Multi-AZ, 7 days backups | ~$25-30 |
| ECS Fargate | 512 CPU / 1024 MB, 2 tasks | ~$30-35 |
| ALB | Application Load Balancer | ~$20-25 |
| WAF | 3 managed rule groups | ~$6-8 |
| Secrets Manager | 1 secret | ~$0.40 |
| CloudWatch Logs | 30 days retention | ~$3-5 |
| NAT Gateway | None (Public subnet for ECS) | $0 |
| **Total (prod)** | | **~$85-100/month** |

## Cost Optimization Strategies

### Staging Environment
- ✅ **Single-AZ**: No Multi-AZ for RDS → 50% cost reduction
- ✅ **No Backups**: Skip backup retention → Save ~$2-3/month
- ✅ **Minimal Resources**: 256/512 CPU/Memory → 50% reduction vs prod
- ✅ **Short Log Retention**: 7 days instead of 30 → 70% reduction
- ✅ **Single Task**: 1 task vs 2 in prod → 50% reduction

### Production Environment
- ✅ **Multi-AZ**: High availability with 2x RDS instances
- ✅ **Backup Retention**: 7 days for disaster recovery
- ✅ **Redundant Tasks**: 2 tasks for zero-downtime deployments
- ✅ **WAF Protection**: Security against attacks
- ✅ **Extended Logs**: 30 days for audit compliance

### Both Environments
- ✅ **No NAT Gateway**: Public subnet deployment → Save ~$30-40/month per env
- ✅ **t4g instances**: ARM-based instances for 20% cost reduction
- ✅ **Minimal storage**: 20GB for development needs
- ✅ **On-demand pricing**: No Reserved Instances commitment

## Cost Reduction: Apply/Destroy Strategy

### Development/Testing Workflow
Instead of running 24/7, use Terraform to spin up/down:
```bash
# Start environment for testing
terraform apply   # ~5-10 minutes

# Test application
# ...

# Destroy when done
terraform destroy # ~5-10 minutes
```

**Cost Impact**:
- **Full month (24/7)**: ~$40-50 (stg) or ~$85-100 (prod)
- **8 hours/day**: ~$10-15 (stg) or ~$25-30 (prod)
- **On-demand only**: ~$2-3 per session (stg)

### Production Deployment
- Keep prod running 24/7 for availability
- Use stg for development with apply/destroy cycle
- Deploy to prod only after stg validation

## Monthly Budget Scenarios

| Scenario | stg Usage | prod Usage | Total Cost |
|----------|-----------|------------|------------|
| **Portfolio Demo** | 2 hours/week | Not running | ~$5/month |
| **Active Development** | 8 hours/day | Not running | ~$15/month |
| **Production Ready** | On-demand | 24/7 | ~$90-105/month |
| **Full Operation** | 24/7 | 24/7 | ~$130-150/month |

## Cost Monitoring

### AWS Cost Explorer
- Set up billing alerts at $20, $50, $100
- Monitor by service (RDS, ECS, ALB)
- Track daily spending trends

### Tags for Cost Allocation
All resources tagged with:
- `Project`: customer-import
- `Env`: stg or prod
- Enable cost allocation tags in AWS Billing

## Future Optimizations (Not Implemented)

- [ ] **Reserved Instances**: 30-50% discount for 1-year commitment
- [ ] **Savings Plans**: Flexible commitment with discounts
- [ ] **RDS Aurora Serverless**: Pay per second for variable workloads
- [ ] **Fargate Spot**: 70% discount for fault-tolerant workloads
- [ ] **S3 Lifecycle**: Move old data to cheaper storage tiers
