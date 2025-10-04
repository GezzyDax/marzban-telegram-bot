#!/bin/bash
set -e

echo "🧪 Starting smoke test for Marzban Telegram Bot container..."

# Configuration
CONTAINER_NAME="marzban-bot-test"
IMAGE_TAG="${1:-latest}"
WAIT_TIME=30

echo "📦 Testing image: harbor.gezzy.ru/apps/marzban-telegram-bot:${IMAGE_TAG}"

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up..."
    docker rm -f ${CONTAINER_NAME} 2>/dev/null || true
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Start container
echo "🚀 Starting container..."
docker run -d \
    --name ${CONTAINER_NAME} \
    -e DATABASE_URL="postgresql+asyncpg://test:test@postgres:5432/test" \
    -e TELEGRAM_BOT_TOKEN="test:token" \
    -e TELEGRAM_ADMIN_IDS="12345" \
    -e MARZBAN_API_URL="http://test" \
    -e MARZBAN_ADMIN_USERNAME="test" \
    -e MARZBAN_ADMIN_PASSWORD="test" \
    --network=host \
    harbor.gezzy.ru/apps/marzban-telegram-bot:${IMAGE_TAG}

# Wait for container to start
echo "⏳ Waiting ${WAIT_TIME} seconds for container to initialize..."
sleep ${WAIT_TIME}

# Check if container is still running
if ! docker ps | grep -q ${CONTAINER_NAME}; then
    echo "❌ Container crashed during startup!"
    echo "📋 Container logs:"
    docker logs ${CONTAINER_NAME}
    exit 1
fi

# Get logs
echo "📋 Checking container logs..."
LOGS=$(docker logs ${CONTAINER_NAME} 2>&1)

# Check for critical errors
if echo "${LOGS}" | grep -iq "CRITICAL\|FATAL\|Traceback"; then
    echo "❌ Found critical errors in logs!"
    echo "${LOGS}"
    exit 1
fi

# Check for successful startup indicators
if ! echo "${LOGS}" | grep -q "Starting Marzban Telegram Bot"; then
    echo "⚠️  Bot startup message not found, but no critical errors detected"
    echo "${LOGS}"
fi

# Check version is set
if docker exec ${CONTAINER_NAME} test -f /app/VERSION; then
    VERSION=$(docker exec ${CONTAINER_NAME} cat /app/VERSION)
    echo "✅ Version file found: ${VERSION}"
else
    echo "⚠️  Version file not found at /app/VERSION"
fi

# Check bot user
BOT_USER=$(docker exec ${CONTAINER_NAME} whoami)
if [ "$BOT_USER" != "botuser" ]; then
    echo "⚠️  Container running as ${BOT_USER}, expected botuser"
else
    echo "✅ Container running as non-root user: ${BOT_USER}"
fi

# Final check - container still running
if docker ps | grep -q ${CONTAINER_NAME}; then
    echo "✅ Smoke test PASSED! Container is healthy."
    echo "📝 Last 10 log lines:"
    docker logs ${CONTAINER_NAME} --tail 10
    exit 0
else
    echo "❌ Smoke test FAILED! Container stopped unexpectedly."
    exit 1
fi
