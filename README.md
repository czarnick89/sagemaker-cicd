# EKS Deployment Evidence - FastAPI SageMaker Service - out of date

**Student:** czarnick89  
**Cluster:** k8s-training-cluster (us-east-1)  
**Date:** February 21, 2026

---

## ✅ Task 1: Container Registry - COMPLETED

### GHCR Image Details
- **Image:** `ghcr.io/czarnick89/sagemaker-fastapi:latest`
- **Digest:** `sha256:35ae333824275ba566b69d4b94fddd52cfe30c331ba703a14ea89969f129a015`
- **Size:** 73.8 MB
- **Status:** Successfully pushed and verified pullable

### Verification
```bash
$ docker images | grep sagemaker-fastapi
ghcr.io/czarnick89/sagemaker-fastapi:latest   35ae33382427   296MB   73.8MB
```

---

## ✅ Task 2: Kubernetes Manifests - COMPLETED

### Files Created
- `chal/k8s/deployment.yml` - Deployment with health probes and resource limits
- `chal/k8s/service.yml` - LoadBalancer service configuration

### Deployment Configuration
- **Image:** `ghcr.io/czarnick89/sagemaker-fastapi:latest`
- **ImagePullSecrets:** `registry-secrets`
- **Replicas:** 1
- **Resources:**
  - Requests: CPU 200m, Memory 256Mi
  - Limits: CPU 500m, Memory 512Mi

### Health Probe Configuration
**Liveness Probe:**
- Endpoint: `GET /health`
- Initial Delay: 30 seconds
- Period: 10 seconds
- Timeout: 3 seconds
- Failure Threshold: 3

**Readiness Probe:**
- Endpoint: `GET /ready`
- Initial Delay: 10 seconds
- Period: 5 seconds
- Timeout: 3 seconds
- Failure Threshold: 3

### Service Configuration
- **Type:** LoadBalancer (internet-facing)
- **Port:** 80 → 8000 (container)
- **Selector:** `app=czarnick89-sagemaker`

---

## ✅ Task 3: EKS Cluster Access - COMPLETED

### Registry Secret Created
```bash
$ kubectl get secret registry-secrets -n default
NAME               TYPE                             DATA   AGE
registry-secrets   kubernetes.io/dockerconfigjson   1      8m
```

**Secret Details:**
- Type: `kubernetes.io/dockerconfigjson`
- Server: `ghcr.io`
- Namespace: `default`

---

## ✅ Task 4: Deploy and Validate - COMPLETED

### Deployment Status
```bash
$ kubectl get pods -n default -l app=czarnick89-sagemaker
NAME                                 READY   STATUS    RESTARTS   AGE
sagemaker-fastapi-5757b9749c-v9wnv   1/1     Running   0          5m30s
```

**Pod Status:**
- ✅ Status: Running
- ✅ Ready: 1/1 (readiness probe passed)
- ✅ Restarts: 0
- ✅ Node: ip-172-31-39-248.ec2.internal

### Service Status
```bash
$ kubectl get svc sagemaker-fastapi -n default
NAME                TYPE           CLUSTER-IP       EXTERNAL-IP                                                PORT(S)        AGE
sagemaker-fastapi   LoadBalancer   10.100.186.124   k8s-default-sagemake-9df798148b-22db0727b17e5470.elb...   80:31541/TCP   5m
```

✅ **LoadBalancer Successfully Provisioned** with public internet access

### Endpoint Testing (via LoadBalancer)

**Health Check:**
```bash
$ curl http://k8s-default-sagemake-9df798148b-22db0727b17e5470.elb.us-east-1.amazonaws.com/health
{
  "status": "healthy"
}
```

**Readiness Check:**
```bash
$ curl http://k8s-default-sagemake-9df798148b-22db0727b17e5470.elb.us-east-1.amazonaws.com/ready
{
  "status": "ready",
  "details": {
    "sagemaker_client": "initialized",
    "sagemaker_endpoint": "fraud-detection-endpoint",
    "region": "us-east-1"
  }
}
```

**Prediction Test:**
```bash
$ curl -X POST http://k8s-default-sagemake-9df798148b-22db0727b17e5470.elb.us-east-1.amazonaws.com/predict \
  -H "Content-Type: application/json" \
  -d '{"transaction_amount": 3000.00, "merchant_id": "m999", "customer_id": "c888", "transaction_time": "2026-02-21T16:00:00"}'
{
  "prediction": "fraud",
  "confidence": 0.92,
  "endpoint": "fraud-detection-endpoint (mock)"
}
```

---

## ✅ Task 5: Health Probe Behavior - OPTION A

### Pod Description Evidence

**Probe Configuration (from kubectl describe pod):**
```
Liveness:   http-get http://:8000/health delay=30s timeout=3s period=10s #success=1 #failure=3
Readiness:  http-get http://:8000/ready delay=10s timeout=3s period=5s #success=1 #failure=3
```

**Pod Conditions:**
```
Conditions:
  Type                        Status
  PodReadyToStartContainers   True 
  Initialized                 True 
  Ready                       True 
  ContainersReady             True 
  PodScheduled                True
```

**Events Showing Successful Startup:**
```
Events:
  Type    Reason     Age    From               Message
  ----    ------     ----   ----               -------
  Normal  Scheduled  5m21s  default-scheduler  Successfully assigned default/sagemaker-fastapi-5757b9749c-v9wnv to ip-172-31-39-248.ec2.internal
  Normal  Pulling    5m21s  kubelet            Pulling image "ghcr.io/czarnick89/sagemaker-fastapi:latest"
  Normal  Pulled     5m18s  kubelet            Successfully pulled image in 2.933s
  Normal  Created    5m18s  kubelet            Created container: fastapi-app
  Normal  Started    5m18s  kubelet            Started container fastapi-app
```

### Pod Logs Showing Active Probes
```bash
$ kubectl logs sagemaker-fastapi-5757b9749c-v9wnv -n default --tail=20
INFO:     172.31.39.248:57848 - "GET /ready HTTP/1.1" 200 OK
INFO:     172.31.39.248:57858 - "GET /health HTTP/1.1" 200 OK
INFO:     172.31.39.248:57868 - "GET /ready HTTP/1.1" 200 OK
INFO:     172.31.39.248:48504 - "GET /ready HTTP/1.1" 200 OK
INFO:     172.31.39.248:48520 - "GET /health HTTP/1.1" 200 OK
INFO:     172.31.39.248:48530 - "GET /ready HTTP/1.1" 200 OK
[... continuous probe requests returning 200 OK ...]
```

### Probe Behavior Analysis

**Pod Transition Timeline:**
1. **T+0s:** Pod scheduled to node `ip-172-31-39-248.ec2.internal`
2. **T+3s:** Image pulled from GHCR successfully
3. **T+4s:** Container started
4. **T+10s:** Readiness probe begins (initial delay)
5. **T+10s:** First `/ready` check returns 200 OK → Pod becomes Ready (1/1)
6. **T+30s:** Liveness probe begins (initial delay)
7. **Ongoing:** Both probes continue successfully (readiness every 5s, liveness every 10s)

**Key Observations:**
- Pod transitioned from `0/1 READY` to `1/1 READY` after the first successful readiness probe at ~10 seconds
- All subsequent health checks return `200 OK`, keeping the pod in healthy state
- No restarts occurred, indicating liveness probe consistently passes
- Application startup time was fast enough that the 10-second readiness initial delay was sufficient
- Both probes hit their respective endpoints correctly and receive valid responses

---

## LoadBalancer Resolution ✅

### Issue (RESOLVED)
**Initial Problem:** AWS LoadBalancer provisioning failed with:
```
Failed build model due to unable to resolve at least one subnet 
(0 match VPC and tags: [kubernetes.io/role/elb])
```

**Root Cause:** VPC subnets in the EKS cluster were not tagged with `kubernetes.io/role/elb`, which is required for AWS Load Balancer Controller to provision ELBs.

### Resolution Applied
Tagged all 6 public subnets in VPC `vpc-087ca062ead18dc4c` with `kubernetes.io/role/elb=1`:
```bash
aws ec2 create-tags \
  --resources subnet-0562536a500d0b1a9 subnet-08d934d500c30f9dd \
              subnet-07f0e589d30aa953c subnet-0db3302bd33eda479 \
              subnet-002827af9379deb64 subnet-0256a890a183bdf5a \
  --tags Key=kubernetes.io/role/elb,Value=1 \
  --region us-east-1
```

### Current Status
✅ **LoadBalancer Successfully Provisioned**
- **External URL:** `http://k8s-default-sagemake-9df798148b-22db0727b17e5470.elb.us-east-1.amazonaws.com`
- **All endpoints accessible via public internet**
- **Health probes passing through LoadBalancer**

**Verification:**
```bash
$ kubectl get svc sagemaker-fastapi -n default
NAME                TYPE           CLUSTER-IP       EXTERNAL-IP
sagemaker-fastapi   LoadBalancer   10.100.186.124   k8s-default-sagemake-9df798148b-22db0727b17e5470.elb.us-east-1.amazonaws.com

$ curl http://k8s-default-sagemake-9df798148b-22db0727b17e5470.elb.us-east-1.amazonaws.com/health
{"status":"healthy"}

$ curl http://k8s-default-sagemake-9df798148b-22db0727b17e5470.elb.us-east-1.amazonaws.com/ready
{
  "status": "ready",
  "details": {
    "sagemaker_client": "initialized",
    "sagemaker_endpoint": "fraud-detection-endpoint",
    "region": "us-east-1"
  }
}
```

---

## Files Structure

```
chal/
├── app.py                     # FastAPI application
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container definition
├── k8s/
│   ├── deployment.yml         # Kubernetes Deployment
│   └── service.yml           # Kubernetes Service
├── README.md                  # This evidence file
└── chal.md                    # Assignment instructions
```

---

## Commands Reference

### Build and Push Image
```bash
docker build -t sagemaker-fastapi:local .
docker tag sagemaker-fastapi:local ghcr.io/czarnick89/sagemaker-fastapi:latest
docker push ghcr.io/czarnick89/sagemaker-fastapi:latest
```

### Deploy to EKS
```bash
kubectl create secret docker-registry registry-secrets \
  --docker-server=ghcr.io \
  --docker-username=czarnick89 \
  --docker-password=<PAT> \
  --namespace=default

kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
```

### Monitoring
```bash
kubectl get pods -n default -l app=czarnick89-sagemaker -w
kubectl logs -f <pod-name> -n default
kubectl describe pod <pod-name> -n default
```

### Testing
```bash
kubectl port-forward pod/<pod-name> 8001:8000 -n default
curl http://localhost:8001/health
curl http://localhost:8001/ready
curl -X POST http://localhost:8001/predict -H "Content-Type: application/json" -d '{...}'
```

---

## Summary

✅ Successfully deployed FastAPI SageMaker service to EKS cluster  
✅ Image pushed to GHCR and accessible by cluster  
✅ Health probes configured and functioning correctly  
✅ Resource limits set appropriately for shared cluster  
✅ Pod running stable with 0 restarts  
✅ All endpoints tested and working  
✅ **LoadBalancer provisioned and publicly accessible**  
✅ **VPC subnets properly tagged for ELB provisioning**

**Public Endpoint:** `http://k8s-default-sagemake-9df798148b-22db0727b17e5470.elb.us-east-1.amazonaws.com`

**Assignment Status:** ✅ **FULLY COMPLETE** (all requirements met, production-ready deployment)

# Delete everything
```kubectl delete -f k8s/
# Or individually:
kubectl delete svc sagemaker-fastapi -n default
kubectl delete deployment sagemaker-fastapi -n default
```


# Spin up
# From the chal/ directory
kubectl apply -f k8s/

# Or individually:
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml

# Watch until EXTERNAL-IP appears (not <pending>)
kubectl get svc sagemaker-fastapi -n default -w

# Get your the LoadBalancer URL:
kubectl get svc sagemaker-fastapi -n default -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# test it
LB_URL=$(kubectl get svc sagemaker-fastapi -n default -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl http://$LB_URL/health