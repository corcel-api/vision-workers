import subprocess
import time
import os
import argparse
import logging
from typing import List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_latest_tag() -> str:
    return subprocess.getoutput("git describe --tags --abbrev=0")

def get_latest_remote_tag(branch: str) -> str:
    subprocess.run(["git", "fetch", "--tags", "origin", branch], check=True)
    latest_commit = subprocess.getoutput(f"git rev-list --tags --max-count=1 --branches=origin/{branch}")
    return subprocess.getoutput(f"git describe --tags --abbrev=0 {latest_commit}")

def fetch_latest_tags(branch: str) -> None:
    subprocess.run(["git", "fetch", "--tags", "origin", branch], check=True)

def should_update(local_tag: str, remote_tag: str) -> bool:
    logging.info(f"Comparing local tag: {local_tag} to remote tag: {remote_tag}")
    return local_tag != remote_tag

def update_repository(target_tag: str) -> None:
    logging.info(f"Updating to tag: {target_tag}")
    subprocess.run(["git", "reset", "--hard", target_tag], check=True)
    logging.info("Repository updated to the latest tag.")

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

def contains_special_token(tag: str, token: str) -> bool:
    return token in tag

def print_changes_since_last_tag(local_tag: str, remote_tag: str) -> None:
    logging.info("\nChanges since last update:")
    changes = subprocess.getoutput(f"git log {local_tag}..{remote_tag} --pretty=format:'%h - %s (%cd) [%an]' --date=format:'%Y-%m-%d %H:%M:%S'")
    if changes:
        logging.info("=============================================")
        logging.info(changes)
        logging.info("=============================================\n")
    else:
        logging.info("No changes were found, or the tags are identical.\n")

def run_autoupdate(restart_script: str, env_autoup_token: str, server_special_token: str, ports_to_kill: List[int], branch: str, auto_updates_sleep: int) -> None:
    while True:
        fetch_latest_tags(branch)
        local_tag = get_latest_tag()
        remote_tag = get_latest_remote_tag(branch)

        if should_update(local_tag, remote_tag) and contains_special_token(remote_tag, env_autoup_token):
            logging.info("Local repository is not up-to-date. Updating...")
            update_repository(remote_tag)
            print_changes_since_last_tag(local_tag, remote_tag)
            if contains_special_token(remote_tag, server_special_token):
                logging.info("Remote tag contains required token. Running the autoupdate steps...")
                stop_server_on_port(ports_to_kill)
                subprocess.run(f"chmod +x {restart_script}", shell=True)
                subprocess.Popen(f"/bin/sh {restart_script}", shell=True)
                logging.info("Finished running the autoupdate steps! Server is ready.")
            else:
                logging.info("No restart needed as server token not present.")
        else:
            logging.info("Local repository is up-to-date or the tag does not contain the required token.")
        time.sleep(auto_updates_sleep)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--restart_script", type=str)
    args = parser.parse_args()

    auto_updates_sleep = int(os.getenv('AUTOUP_SLEEP', '60'))
    current_env = os.getenv('CURRENT_ENV', 'dev').lower()
    branch = os.getenv('GIT_BRANCH', 'main' if current_env == 'prod' else 'dev')
    server_special_token = os.getenv('SERVER_RELOAD_GIT_TOKEN', 'none')
    env_autoup_token = "_prod" if current_env == "prod" else "_dev"

    orchestrator_port = int(os.getenv('CURRENT_SERVER_PORT', 6920))
    service_port = int(os.getenv('SERVICE_SERVER_PORT', 6919))
    comfyui_port = int(os.getenv('COMFYUI_SERVER_PORT', 8188))

    logging.info(f"\nEnvironment: {current_env.upper()}")
    logging.info(f"Listening for Git tag updates on branch '{branch}' with tags containing the tokens: '{env_autoup_token}, {server_special_token}'\n")

    run_autoupdate(
        restart_script=args.restart_script,
        env_autoup_token=env_autoup_token,
        server_special_token=server_special_token,
        ports_to_kill=[orchestrator_port, service_port, comfyui_port],
        branch=branch,
        auto_updates_sleep=auto_updates_sleep
    )
