#!/bin/bash
# Build and deployment script for DuckDB Macro REST Server

set -e

# Configuration
IMAGE_NAME="duckdb-macro-rest"
IMAGE_TAG="${1:-latest}"
REGISTRY="${REGISTRY:-}"
ENVIRONMENT="${2:-development}"

echo "Building DuckDB Macro REST Server..."
echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "Environment: ${ENVIRONMENT}"

# Build the Docker image
echo "Building Docker image..."
docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .

# Tag for registry if specified
if [ ! -z "$REGISTRY" ]; then
    echo "Tagging for registry: ${REGISTRY}"
    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
fi

# Run tests in Docker container
echo "Running health check..."
docker run --rm -d --name "${IMAGE_NAME}-test" -p 8001:8000 "${IMAGE_NAME}:${IMAGE_TAG}"

# Wait for container to start
echo "Waiting for container to start..."
sleep 10

# Test health endpoint
if curl -f http://localhost:8001/health; then
    echo "Health check passed!"
else
    echo "Health check failed!"
    docker logs "${IMAGE_NAME}-test"
    exit 1
fi

# Cleanup test container
docker stop "${IMAGE_NAME}-test"

echo "Build completed successfully!"

# Push to registry if specified
if [ ! -z "$REGISTRY" ] && [ "$ENVIRONMENT" = "production" ]; then
    echo "Pushing to registry..."
    docker push "${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
fi

echo "Deployment artifacts ready:"
echo "  Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "  Environment: ${ENVIRONMENT}"
echo ""
echo "To run locally:"
echo "  docker-compose up"
echo ""
echo "To run in production:"
echo "  docker-compose -f docker-compose.prod.yml up -d"
