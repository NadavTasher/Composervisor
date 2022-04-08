// SSH constants
export const PRIVATE = `key`;
export const PUBLIC = `${PRIVATE}.pub`;

// General constants
export const TAIL = 100;
export const TIMEOUT = 3;
export const REPOSITORY = "repository";

// General commands
export const MKDIR_COMMAND = `mkdir -p "{path}"`;
export const RMDIR_COMMAND = `rm -rf "{path}"`;
export const CD_COMMAND = `cd "{path}"`;
export const KEY_COMMAND = `ssh-keygen -t rsa -b 4096 -f "{path}/${PRIVATE}" -N "" -C "Deployment key for {id}"`;
export const GIT_COMMAND = `${CD_COMMAND}; git -c core.sshCommand="ssh -i {path}/${PRIVATE}"`;
export const COMPOSE_COMMAND = `${CD_COMMAND}; docker-compose --project-name "{id}" --project-directory "${REPOSITORY}/{directory}"`;

// Deployment statuscommands
export const LOG_COMMAND = `${COMPOSE_COMMAND} logs --no-color --timestamps --tail ${TAIL}`;
export const STATUS_COMMAND = `${COMPOSE_COMMAND} ps --quiet`;
// Deployment state commands
export const STOP_COMMAND = `${COMPOSE_COMMAND} down --remove-orphans --timeout ${TIMEOUT}`;
export const START_COMMAND = `${COMPOSE_COMMAND} up --detach`;
export const RESTART_COMMAND = `${STOP_COMMAND}; ${START_COMMAND}`;
// Deployment destruction commands
export const DESTROY_COMMAND = `${STOP_COMMAND} --volumes`;
export const RESET_COMMAND = `${DESTROY_COMMAND}; ${START_COMMAND}`;
// Deployment repository commands
export const PULL_COMMAND = `${GIT_COMMAND} -C ${REPOSITORY} pull`;
export const CLONE_COMMAND = `${GIT_COMMAND} clone {repository} ${REPOSITORY}`;
// Deployment management commands
export const BUILD_COMMAND = `${COMPOSE_COMMAND} build --pull --force-rm`;
export const UPDATE_COMMAND = `${PULL_COMMAND}; ${BUILD_COMMAND}`;
export const WEBHOOK_COMMAND = `${UPDATE_COMMAND}; ${RESTART_COMMAND}`;