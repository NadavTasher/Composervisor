# Directory constants
OUTPUT = f'/opt'
DEPLOYMENT = f'{OUTPUT}/{{identifier}}'

# SSH constants
PRIVATE = f'key'
PUBLIC = f'{PRIVATE}.pub'

# General constants
TAIL = 100
TIMEOUT = 3
REPOSITORY = f'repository'

# General commands
KEY_COMMAND = f'ssh-keygen -t rsa -b 4096 -f {PRIVATE} -N "" -C "Deployment key for {{identifier}}"'
GIT_COMMAND = f'git -c core.sshCommand="ssh -i {DEPLOYMENT}/{PRIVATE}"'
COMPOSE_COMMAND = f'docker-compose --project-name "{{identifier}}" --project-directory "{REPOSITORY}/{{directory}}"'

# Deployment status commands
LOG_COMMAND = f'{COMPOSE_COMMAND} logs --no-color --timestamps --no-log-prefix --tail {TAIL}'
STATUS_COMMAND = f'{COMPOSE_COMMAND} ps --quiet'

# Deployment state commands
STOP_COMMAND = f'{COMPOSE_COMMAND} down --remove-orphans --timeout {TIMEOUT}'
START_COMMAND = f'{COMPOSE_COMMAND} up --detach'
RESTART_COMMAND = f'{STOP_COMMAND} && {START_COMMAND}'

# Deployment destruction commands
DESTROY_COMMAND = f'{STOP_COMMAND} --volumes'
RESET_COMMAND = f'{DESTROY_COMMAND} && {START_COMMAND}'

# Deployment repository commands
PULL_COMMAND = f'{GIT_COMMAND} -C {REPOSITORY} pull'
CLONE_COMMAND = f'{GIT_COMMAND} clone {{repository}} {REPOSITORY}'

# Deployment management commands
BUILD_COMMAND = f'{COMPOSE_COMMAND} build --pull --force-rm'
UPDATE_COMMAND = f'{PULL_COMMAND} && {BUILD_COMMAND}'
WEBHOOK_COMMAND = f'{UPDATE_COMMAND} && {RESTART_COMMAND}'

# Action endpoints constant
ACTIONS = {
    # Management actions
    "pull": (PULL_COMMAND, True, False),
    "clone": (CLONE_COMMAND, False, False),
    "update": (UPDATE_COMMAND, True, False),
    "destroy": (DESTROY_COMMAND, True, False),
    # State actions
    "stop": (STOP_COMMAND, True, False),
    "start": (START_COMMAND, True, False),
    "reset": (RESET_COMMAND, True, False),
    "restart": (RESTART_COMMAND, True, False),
    # Status actions
    "log": (LOG_COMMAND, True, False),
    "status": (STATUS_COMMAND, True, False),
    # Webhook action
    "webhook": (WEBHOOK_COMMAND, True, True)
}