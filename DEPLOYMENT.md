# AgentMesh Deployment Guide

This guide covers deploying AgentMesh in production-ready configurations.

## Quick Start (Docker Compose)

For local development and testing:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f server

# Access services
# - AgentMesh API: http://localhost:8080
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/agentmesh)
# - Redis: localhost:6379
# - PostgreSQL: localhost:5432

# Stop services
docker-compose down
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.24+)
- Helm 3.x
- kubectl configured

### Install with Helm

```bash
# Add Bitnami repository (for dependencies)
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install AgentMesh
helm install agentmesh ./charts/agentmesh \
  --namespace agentmesh \
  --create-namespace \
  --set redis.auth.password=your-secure-password \
  --set storage.backend=redis

# Check deployment status
kubectl get pods -n agentmesh
kubectl get svc -n agentmesh
```

### Configuration

Create a `values-production.yaml`:

```yaml
# Production configuration
replicaCount: 5

resources:
  limits:
    cpu: 2000m
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 5
  maxReplicas: 20

storage:
  backend: redis
  cacheEnabled: true

redis:
  enabled: true
  auth:
    password: "CHANGE-ME"
  master:
    persistence:
      enabled: true
      size: 20Gi
  replica:
    replicaCount: 3

observability:
  opentelemetry:
    enabled: true
    endpoint: "http://otel-collector:4317"
  prometheus:
    enabled: true
  logs:
    level: INFO

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: agentmesh.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: agentmesh-tls
      hosts:
        - agentmesh.yourdomain.com
```

Deploy with custom values:

```bash
helm install agentmesh ./charts/agentmesh \
  -f values-production.yaml \
  --namespace agentmesh \
  --create-namespace
```

## GovernedAgent Custom Resource

Deploy governed agents using the CRD:

```yaml
apiVersion: mesh.agentmesh.ai/v1
kind: GovernedAgent
metadata:
  name: data-processor
  namespace: my-app
spec:
  image: my-company/data-processor:v1.2.0
  sponsor: "alice@company.com"
  capabilities:
    - "s3:read"
    - "api:analytics"
  policy: strict
  replicas: 3
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 250m
      memory: 256Mi
  trustScore:
    initialScore: 500
    minimumScore: 300
  observability:
    traces: true
    metrics: true
    logs: true
```

Apply:

```bash
kubectl apply -f governed-agent.yaml
kubectl get governedagents -n my-app
```

## Storage Backends

### Redis (Default)

Recommended for high-performance caching and session storage.

```yaml
storage:
  backend: redis

redis:
  enabled: true
  auth:
    password: "secure-password"
  master:
    persistence:
      enabled: true
      size: 20Gi
```

### PostgreSQL

For persistent data and complex queries.

```yaml
storage:
  backend: postgres

postgresql:
  enabled: true
  auth:
    username: agentmesh
    password: "secure-password"
    database: agentmesh
  primary:
    persistence:
      enabled: true
      size: 50Gi
```

### Hybrid (Redis + PostgreSQL)

Use both for optimal performance:

```yaml
storage:
  backend: redis  # Primary cache
  
redis:
  enabled: true
  # ... redis config

postgresql:
  enabled: true
  # ... postgres config for persistent data
```

## Observability

### Prometheus Metrics

Metrics are exposed on port 9090:

```bash
# Port-forward to access metrics
kubectl port-forward -n agentmesh svc/agentmesh 9090:9090

# View metrics
curl http://localhost:9090/metrics
```

Key metrics:
- `agentmesh_handshake_total` - Trust handshake count
- `agentmesh_policy_violation_count` - Policy violations
- `agentmesh_trust_score_gauge` - Trust scores
- `agentmesh_registry_size` - Registry size
- `agentmesh_api_request_duration_seconds` - API latency

### Grafana Dashboards

Import pre-built dashboards:

1. Access Grafana: `http://localhost:3000` (local) or via ingress
2. Login: admin/agentmesh (change in production)
3. Dashboards are auto-provisioned:
   - Mesh Health
   - Security Violations
   - Agent Latency

### OpenTelemetry Traces

Enable tracing:

```yaml
observability:
  opentelemetry:
    enabled: true
    endpoint: "http://otel-collector:4317"
    serviceName: "agentmesh"
```

## Security

### SPIRE Integration

Enable SPIFFE/SPIRE for workload identity:

```yaml
identity:
  spireEnabled: true
  spireSocketPath: /run/spire/sockets/agent.sock

spire:
  enabled: true
  trustDomain: agentmesh.yourdomain.com
```

### Network Policies

Network policies are enabled by default:

```yaml
networkPolicy:
  enabled: true
  policyTypes:
    - Ingress
    - Egress
```

### TLS/HTTPS

Enable HTTPS with cert-manager:

```yaml
ingress:
  enabled: true
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  tls:
    - secretName: agentmesh-tls
      hosts:
        - agentmesh.yourdomain.com
```

## High Availability

### Multi-AZ Deployment

```yaml
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
            - key: app.kubernetes.io/name
              operator: In
              values:
                - agentmesh
        topologyKey: topology.kubernetes.io/zone
```

### Redis Sentinel

For Redis HA:

```yaml
redis:
  architecture: replication
  sentinel:
    enabled: true
  replica:
    replicaCount: 3
```

## Monitoring & Alerts

### Prometheus Alerts

Create alert rules:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: agentmesh-alerts
spec:
  groups:
    - name: agentmesh
      rules:
        - alert: HighPolicyViolationRate
          expr: rate(agentmesh_policy_violation_count[5m]) > 10
          for: 5m
          annotations:
            summary: "High policy violation rate detected"
        
        - alert: LowTrustScore
          expr: avg(agentmesh_trust_score_gauge) < 400
          for: 10m
          annotations:
            summary: "Average trust score below threshold"
```

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -n agentmesh
kubectl describe pod <pod-name> -n agentmesh
kubectl logs <pod-name> -n agentmesh
```

### Check Service Health

```bash
kubectl port-forward -n agentmesh svc/agentmesh 8080:8080
curl http://localhost:8080/health
curl http://localhost:8080/ready
```

### Check Storage Connectivity

Redis:
```bash
kubectl exec -it -n agentmesh <agentmesh-pod> -- redis-cli -h agentmesh-redis-master ping
```

PostgreSQL:
```bash
kubectl exec -it -n agentmesh <agentmesh-pod> -- psql -h agentmesh-postgresql -U agentmesh -d agentmesh -c '\l'
```

## Upgrade

```bash
# Update Helm chart
helm upgrade agentmesh ./charts/agentmesh \
  -f values-production.yaml \
  --namespace agentmesh

# Rollback if needed
helm rollback agentmesh --namespace agentmesh
```

## Backup & Disaster Recovery

### Redis Backup

```bash
kubectl exec -n agentmesh agentmesh-redis-master-0 -- redis-cli BGSAVE
```

### PostgreSQL Backup

```bash
kubectl exec -n agentmesh agentmesh-postgresql-0 -- \
  pg_dump -U agentmesh agentmesh > backup.sql
```

## Production Checklist

- [ ] Update Redis password
- [ ] Update PostgreSQL password
- [ ] Enable TLS/HTTPS with valid certificates
- [ ] Configure SPIRE for workload identity
- [ ] Set up monitoring alerts
- [ ] Configure backup strategy
- [ ] Enable network policies
- [ ] Configure resource limits
- [ ] Set up log aggregation
- [ ] Test disaster recovery procedures
- [ ] Configure autoscaling
- [ ] Enable audit logging
- [ ] Set up access controls (RBAC)

## Support

For issues or questions:
- GitHub Issues: https://github.com/imran-siddique/agent-mesh/issues
- Documentation: https://github.com/imran-siddique/agent-mesh#readme
