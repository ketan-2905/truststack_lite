# Deployment Guide

## Local Development

```bash
cp .env.example .env
docker compose up -d --build
bash scripts/wait-for-services.sh
```

Runs all services (API, worker, web, PostgreSQL, Redis, MinIO, Prometheus, Grafana) locally.

## Production-Like (Docker Compose)

```bash
cp .env.example .env
docker compose -f infra/docker-compose.prod-like.yml up -d --build
bash scripts/smoke-test.sh
```

Uses production Dockerfiles (non-root users, no dev dependencies, optimized images).

## Kubernetes Deployment

### Prerequisites

- Kubernetes 1.24+
- kubectl configured
- Docker images pushed to registry
- PostgreSQL managed service (e.g., RDS, Cloud SQL)
- Redis managed service (e.g., ElastiCache, Memorystore)
- S3-compatible bucket (AWS S3, GCS, etc.)

### Install

```bash
# Create namespace
kubectl apply -f infra/k8s/namespace.yaml

# Create secrets (update values)
kubectl create secret generic db-secret \
  --from-literal=url='postgresql://user:password@rds.example.com:5432/truststack' \
  -n truststack-lite

# Create config map
kubectl create configmap app-config \
  --from-literal=s3-bucket='truststack-documents' \
  --from-literal=api-url='https://api.truststack.example.com' \
  -n truststack-lite

# Run migrations
kubectl apply -f infra/k8s/migration-job.yaml
kubectl wait --for=condition=complete job/db-migration -n truststack-lite

# Deploy services
kubectl apply -f infra/k8s/api-deployment.yaml
kubectl apply -f infra/k8s/worker-deployment.yaml
kubectl apply -f infra/k8s/web-deployment.yaml

# Deploy ingress (update domain)
kubectl apply -f infra/k8s/ingress.yaml

# Verify
kubectl get deployments -n truststack-lite
kubectl get pods -n truststack-lite
```

### Scale Workers

```bash
kubectl scale deployment worker --replicas=5 -n truststack-lite
```

### Logs

```bash
kubectl logs -f deployment/api -n truststack-lite
kubectl logs -f deployment/worker -n truststack-lite
```

### Update Image

```bash
kubectl set image deployment/api api=truststack-api:v1.0 -n truststack-lite
```

## Managed Cloud Services

### AWS ECS Fargate

```bash
# Task definition for API
aws ecs register-task-definition --cli-input-json file://ecs-task.json

# Create ECS service
aws ecs create-service \
  --cluster truststack \
  --service-name api \
  --task-definition truststack-api:1 \
  --desired-count 3
```

### Google Cloud Run

```bash
gcloud run deploy truststack-api \
  --image gcr.io/myproject/truststack-api:latest \
  --platform managed \
  --region us-central1 \
  --set-env-vars DATABASE_URL=...,REDIS_URL=...
```

### Railway/Render

Push Docker images to registry. Services auto-deploy on push with environment variables configured via dashboard.

## Environment Variables

### Production Overrides

```bash
APP_ENV=production
LOG_LEVEL=warning  # Reduce verbosity
POSTGRES_HOST=rds-instance.us-east-1.rds.amazonaws.com
REDIS_URL=redis://elasticache-endpoint:6379/0
S3_ENDPOINT_URL=https://s3.us-east-1.amazonaws.com
S3_REGION=us-east-1
S3_BUCKET=truststack-prod-documents
```

## Health Checks

### Kubernetes

Readiness probe: `GET /health/ready` (app ready to serve)
Liveness probe: `GET /health/live` (app process alive)

Both return 200 OK when databases/storage are connected.

### ECS

Task health: container runs, curl to `localhost:8000/health` succeeds

## Database Migrations

**Pre-deployment:**
```bash
docker run truststack-api:latest alembic upgrade head
```

**Kubernetes:**
```bash
kubectl apply -f infra/k8s/migration-job.yaml
```

**Rollback:**
```bash
alembic downgrade -1
```

## Secrets Management

### Local
- `.env` file (git-ignored)
- Changed demo credentials before sharing environment

### Production
- AWS Secrets Manager: `DATABASE_URL`, `REDIS_URL`, `S3_*`
- Environment variables injected at runtime
- Rotation schedule (quarterly minimum)

## Zero-Downtime Deployment

1. New API deployment with blue-green strategy
2. Run migrations on new blue environment
3. Route traffic to blue
4. Keep green for rollback (5 minute window)
5. After validation, destroy green

```bash
# Blue-green with kubectl
kubectl set image deployment/api api=truststack-api:v2 --record
kubectl rollout status deployment/api
kubectl rollout undo deployment/api  # if needed
```

## Backup & Restore

### PostgreSQL (RDS)

```bash
# Backup
aws rds create-db-snapshot --db-instance-identifier truststack --db-snapshot-identifier truststack-2026-06-30

# Restore
aws rds restore-db-instance-from-db-snapshot --db-instance-identifier truststack-restored --db-snapshot-identifier truststack-2026-06-30
```

### S3

```bash
# Enable versioning
aws s3api put-bucket-versioning --bucket truststack-documents --versioning-configuration Status=Enabled

# Cross-region replication (optional)
aws s3api put-bucket-replication --bucket truststack-documents --replication-configuration file://replication.json
```

## Monitoring

### Prometheus

Scrapes `/metrics` every 30s from API pods.

### Grafana

Pre-built dashboard at `infra/grafana/dashboards/truststack.json`.

### Logs

- Local: `docker compose logs api`
- Kubernetes: `kubectl logs deployment/api -n truststack-lite`
- Cloud: CloudWatch (AWS), Cloud Logging (GCP)

## Troubleshooting

**API won't start:**
- Check database connection: `echo "SELECT 1" | psql $DATABASE_URL`
- Check Redis connection: `redis-cli -u $REDIS_URL ping`
- Check S3 bucket: `aws s3 ls s3://$S3_BUCKET`

**Worker not processing jobs:**
- Check Redis queue: `redis-cli -u $REDIS_URL LLEN rq:queue:default`
- Check worker process: `kubectl logs deployment/worker`

**Web can't reach API:**
- Check API URL in env: `kubectl get configmap app-config -o yaml`
- Check API health: `curl $NEXT_PUBLIC_API_BASE_URL/health`
- Check network policy: `kubectl get networkpolicies`

## Known Limitations

- No automatic database failover (use managed service features)
- No built-in disaster recovery (implement via snapshots/backups)
- No automatic certificate renewal (use cert-manager in K8s)
- No automatic scaling based on queue depth (configure via HPA/target tracking)
