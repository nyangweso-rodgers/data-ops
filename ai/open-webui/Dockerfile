FROM ghcr.io/open-webui/open-webui:main

# Set working directory
WORKDIR /app

# Install additional dependencies if needed
USER root
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Switch back to non-root user
USER $UID

# Copy custom configuration files
COPY config/ /app/backend/config/

# Set environment variables for customization
ENV WEBUI_NAME="Database Query Assistant"
ENV WEBUI_URL="http://localhost:3000"
ENV WEBUI_SECRET_KEY=${WEBUI_SECRET_KEY}
ENV DEFAULT_USER_ROLE="user"
ENV ENABLE_SIGNUP="true"
ENV ENABLE_LOGIN_FORM="true"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080