# Select the base image
FROM webhood/3.8:2024.01.19

# Install some dependencies
RUN apt update && \
	apt install -yq curl git ssh docker.io
RUN curl -SL "https://github.com/docker/compose/releases/download/v2.24.1/docker-compose-linux-$(uname -m)" -o /usr/bin/docker-compose && \
	chmod +x /usr/bin/docker-compose

# Copy SSH configuration
COPY configurations/ssh_config /etc/ssh/ssh_config

# Copy configurations
COPY configurations/nginx.conf /etc/nginx/conf.d/nginx.conf
COPY configurations/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy sources
COPY src /application