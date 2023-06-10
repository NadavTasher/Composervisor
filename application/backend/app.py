import logging

from router import router
from server import server

# Import composervisor routes
import composer


def main():
    # Set-up logging to stdout
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(threadName)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    try:
        # Start the server
        server.start()

        # Wait for server to stop
        while not server.stopped:
            server.join(1)
    finally:
        server.stop()


if __name__ == "__main__":
    main()
