# n8n Dockerfile
# Using official n8n image without customizations
# The official image is optimized and doesn't include package managers

FROM docker.n8n.io/n8nio/n8n:latest

# Metadata
LABEL maintainer="your-email@example.com"
LABEL description="n8n workflow automation platform"
LABEL version="1.0"

# Note: The official n8n image is a minimal/distroless image
# It doesn't include apk or apt-get package managers
# 
# If you need Python/JavaScript code execution, n8n provides:
# 1. Built-in Code nodes for JavaScript
# 2. Task runners for Python (separate containers)
# 3. npm packages can be installed via n8n UI settings
#
# For custom requirements, consider:
# - Using n8n's native npm package installation feature
# - Using the task runner containers for Python
# - Creating a custom base image if absolutely necessary

# The image already includes:
# - Node.js runtime
# - n8n application
# - Essential utilities
# - Proper user permissions

# Healthcheck (optional - n8n has built-in health endpoint)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:5678/healthz || exit 1

# Expose n8n port
EXPOSE 5678

# Working directory and entrypoint are inherited from base image
# USER node (already set in base image)
# ENTRYPOINT is set in base image