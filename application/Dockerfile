# Select the base image
FROM webhood/3.8:2023.02.09

# Install some dependencies
RUN apt update
RUN apt install -yq git ssh docker.io
RUN curl -SL "https://github.com/docker/compose/releases/download/v2.15.1/docker-compose-linux-$(uname -m)" -o /usr/bin/docker-compose && chmod +x /usr/bin/docker-compose

# Copy SSH configuration
COPY patches/ssh_config /etc/ssh/ssh_config

# Copy sources
COPY backend /application/backend
COPY frontend /application/frontend
