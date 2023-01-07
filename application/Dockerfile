# Select the base image
FROM webhood/3.8:2023.01.07

# Install some dependencies
RUN apt update
RUN apt install -yq git ssh docker.io
RUN pip install docker-compose bunch

# Copy SSH configuration
COPY ssh/ssh_config /etc/ssh/ssh_config

# Copy sources
COPY backend /application/backend
COPY frontend /application/frontend