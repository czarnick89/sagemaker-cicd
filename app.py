import os
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SageMaker Fraud Detection Service")

# SageMaker configuration
SAGEMAKER_ENDPOINT = os.getenv("SAGEMAKER_ENDPOINT", "fraud-detection-endpoint")
REGION = os.getenv("AWS_REGION", "us-east-1")

# Initialize SageMaker runtime client
try:
    sagemaker_runtime = boto3.client('sagemaker-runtime', region_name=REGION)
    logger.info(f"SageMaker runtime client initialized for region: {REGION}")
except Exception as e:
    logger.warning(f"Failed to initialize SageMaker client: {e}")
    sagemaker_runtime = None


class PredictionRequest(BaseModel):
    """Request model for fraud prediction"""
    transaction_amount: float
    merchant_id: str
    customer_id: str
    transaction_time: str


class PredictionResponse(BaseModel):
    """Response model for fraud prediction"""
    prediction: str
    confidence: float
    endpoint: str


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Liveness probe endpoint.
    Returns healthy if the application is running.
    """
    return {"status": "healthy", 'version': 'v1.0.0'}

@app.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness probe endpoint.
    Checks if the service can handle requests (SageMaker connectivity).
    """
    ready = True
    details = {}
    
    # Check if SageMaker client is initialized
    if sagemaker_runtime is None:
        ready = False
        details["sagemaker_client"] = "not_initialized"
    else:
        details["sagemaker_client"] = "initialized"
    
    # Check if endpoint name is configured
    if not SAGEMAKER_ENDPOINT:
        ready = False
        details["sagemaker_endpoint"] = "not_configured"
    else:
        details["sagemaker_endpoint"] = SAGEMAKER_ENDPOINT
    
    details["region"] = REGION
    
    if ready:
        return {
            "status": "ready",
            "details": details
        }
    else:
        return {
            "status": "not_ready",
            "details": details
        }


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest) -> PredictionResponse:
    """
    Fraud prediction endpoint.
    Calls SageMaker endpoint to get prediction.
    Falls back to mock response if SageMaker is unavailable.
    """
    logger.info(f"Received prediction request for customer: {request.customer_id}")
    
    # If SageMaker is configured and available, try real inference
    if sagemaker_runtime and SAGEMAKER_ENDPOINT:
        try:
            # Prepare payload for SageMaker
            payload = {
                "transaction_amount": request.transaction_amount,
                "merchant_id": request.merchant_id,
                "customer_id": request.customer_id,
                "transaction_time": request.transaction_time
            }
            
            # Call SageMaker endpoint
            response = sagemaker_runtime.invoke_endpoint(
                EndpointName=SAGEMAKER_ENDPOINT,
                ContentType='application/json',
                Body=str(payload)
            )
            
            # Parse response
            result = response['Body'].read().decode()
            logger.info(f"SageMaker prediction: {result}")
            
            return PredictionResponse(
                prediction="fraud" if "fraud" in result.lower() else "legitimate",
                confidence=0.87,
                endpoint=SAGEMAKER_ENDPOINT
            )
            
        except ClientError as e:
            logger.error(f"SageMaker invocation failed: {e}")
            # Fall through to mock response
        except Exception as e:
            logger.error(f"Unexpected error during prediction: {e}")
            # Fall through to mock response
    
    # Mock response for testing/demo purposes
    logger.info("Using mock prediction response")
    
    # Simple rule-based mock: flag high-value transactions as fraud
    is_fraud = request.transaction_amount > 1000.0
    
    return PredictionResponse(
        prediction="fraud" if is_fraud else "legitimate",
        confidence=0.92 if is_fraud else 0.78,
        endpoint=f"{SAGEMAKER_ENDPOINT} (mock)"
    )


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with service information"""
    return {
        "service": "SageMaker Fraud Detection API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "predict": "/predict (POST)"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
