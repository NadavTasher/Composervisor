# Select the base image
FROM webhood/template:2022.03.12

# Install some dependencies
RUN apt update
RUN apt install -yq docker-compose git ssh

# Copy SSH configuration
COPY sources/ssh_config /etc/ssh/ssh_config

# Copy sources
COPY sources/backend backend
COPY sources/frontend frontend