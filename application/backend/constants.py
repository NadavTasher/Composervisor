# Directory constants
OUTPUT = f'/opt'

# SSH constants
PRIVATE = f'key'
PUBLIC = f'{PRIVATE}.pub'

# General constants
TAIL = 100
TIMEOUT = 3
REPOSITORY = f'repository'

# General commands
KEY_COMMAND = f'ssh-keygen -t rsa -b 4096 -f {PRIVATE} -N "" -C "Deployment key for {{id}}"'
GIT_COMMAND = f'git -c core.sshCommand="ssh -i {PRIVATE}"'
COMPOSE_COMMAND = f'cd {REPOSITORY}; docker-compose --project-name "{{id}}" --project-directory "{{directory}}"'

# Deployment status commands
LOG_COMMAND = f'{COMPOSE_COMMAND} logs --no-color --timestamps --tail {TAIL}'
STATUS_COMMAND = f'{COMPOSE_COMMAND} ps --quiet'

# Deployment state commands
STOP_COMMAND = f'{COMPOSE_COMMAND} down --remove-orphans --timeout {TIMEOUT}'
START_COMMAND = f'{COMPOSE_COMMAND} up --detach'
RESTART_COMMAND = f'{STOP_COMMAND}; {START_COMMAND}'

# Deployment destruction commands
DESTROY_COMMAND = f'{STOP_COMMAND} --volumes'
RESET_COMMAND = f'{DESTROY_COMMAND}; {START_COMMAND}'

# Deployment repository commands
PULL_COMMAND = f'{GIT_COMMAND} -C {REPOSITORY} pull'
CLONE_COMMAND = f'{GIT_COMMAND} clone {{repository}} {REPOSITORY}'

# Deployment management commands
BUILD_COMMAND = f'{COMPOSE_COMMAND} build --pull --force-rm'
UPDATE_COMMAND = f'{PULL_COMMAND}; {BUILD_COMMAND}'
WEBHOOK_COMMAND = f'{UPDATE_COMMAND}; {RESTART_COMMAND}'