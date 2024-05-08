import subprocess
import time
import os
import logging
from typing import List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def stop_server_on_port(ports_to_kill: List[int]) -> None:
    for port in ports_to_kill:
        logging.info(f"Stopping the server on port {port}...")
        try:
            subprocess.run(f"kill $(lsof -t -i:{port})", shell=True, check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Error stopping the server: {e}")

        while True:
            result = subprocess.run(f"lsof -i:{port}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 1:
                logging.info("Server stopped successfully.")
                break
            else:
                logging.info("Waiting for the server process to stop...")
                time.sleep(1)
    logging.info('All servers stopped successfully!')

def reload(restart_script: str):
    logging.info(f"Running {restart_script}...")
    subprocess.run(f"chmod +x {restart_script}", shell=True)
    subprocess.Popen(f"/bin/sh {restart_script}", shell=True)