// SSH constants
export const PRIVATE = `ssh-key`;
export const PUBLIC = `${PRIVATE}.pub`;
export const CREATE_KEY_COMMAND = `ssh-keygen -t rsa -b 4096 -f "{path}/${PRIVATE}" -N "" -C "Deployment key for {id}"`;

// General constants
export const REPOSITORY = "repository";
export const CREATE_PATH_COMMAND = `mkdir -p {path}`;
export const DELETE_PATH_COMMAND = `rm -rf {path}`;

// Git constants
export const GIT_COMMAND = `cd {path}; git -c core.sshCommand="ssh -i {path}/${PRIVATE}"`;

// Compose constants
export const COMPOSE_TIMEOUT = 3;
export const COMPOSE_COMMAND = `cd {path}; docker-compose --project-name {id} --project-directory ${REPOSITORY}/{directory}`;

// Control constants
export const START_DEPLOYMENT_COMMAND = `${COMPOSE_COMMAND} up --detach`;
export const STOP_DEPLOYMENT_COMMAND = `${COMPOSE_COMMAND} down --remove-orphans --timeout ${COMPOSE_TIMEOUT}`;
export const DESTROY_DEPLOYMENT_COMMAND = `${STOP_DEPLOYMENT_COMMAND} --volumes`;
export const RESET_DEPLOYMENT_COMMAND = `${DESTROY_DEPLOYMENT_COMMAND}; ${START_DEPLOYMENT_COMMAND}`;
export const RESTART_DEPLOYMENT_COMMAND = `${STOP_DEPLOYMENT_COMMAND}; ${START_DEPLOYMENT_COMMAND}`;
export const DELETE_DEPLOYMENT_COMMAND = `${DESTROY_DEPLOYMENT_COMMAND}; ${DELETE_PATH_COMMAND}`;
export const UPDATE_DEPLOYMENT_COMMAND = `${GIT_COMMAND} pull`;
export const CREATE_DEPLOYMENT_COMMAND = `${GIT_COMMAND} clone {repository} ${REPOSITORY}`;
