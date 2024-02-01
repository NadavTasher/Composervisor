import logging
import threading
import traceback

from globals import QUEUE, RESULTS
from composer import Deployment

# Setup the logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Create stop event
EVENT = threading.Event()

# Loop until finished
while not EVENT.is_set():
    # Check whether any deployment needs to execute an action
    while QUEUE:
        # Pop a job from the queue
        job_id, job_parameters = QUEUE.popitem()

        # Execute the job
        deployment = Deployment(job_parameters.identifier)

        # Execute the required action
        try:
            # Execute the action
            output = getattr(deployment, job_parameters.action)(**job_parameters.parameters)

            # Update the results
            RESULTS[job_id] = (True, output)
        except:
            # Update the results
            RESULTS[job_id] = (False, traceback.format_exc())
    
    # Wait for event
    EVENT.wait(1)
