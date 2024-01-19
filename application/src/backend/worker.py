import logging
import threading

# Setup the logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Create stop event
EVENT = threading.Event()

# Loop until finished
while not EVENT.is_set():
    # Log wait
    logging.info("Still waiting for stop event")

    # Wait for event
    EVENT.wait(60 * 60)
