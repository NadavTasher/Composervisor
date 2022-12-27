# Select the base image
FROM webhood/3.8:2022.12.27

# Install some dependencies
RUN apt update
RUN apt install -yq git ssh
RUN apt install -yq docker-compose

# Copy SSH configuration
COPY ssh/ssh_config /etc/ssh/ssh_config

# Copy sources
COPY backend /application/backend
COPY frontend /application/frontend