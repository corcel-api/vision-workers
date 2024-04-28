import subprocess
import time
import os
import argparse
import logging
from typing import List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _initialize_git_if_needed(repo_url: str, branch: str) -> None:
    if not os.path.isdir('.git'):
        logging.info("No .git directory found. Initializing and setting up remote repository...")
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["git", "remote", "add", "origin", repo_url], check=True)
        subprocess.run(["git", "fetch"], check=True)
        subprocess.run(["git", "reset", "--hard"], check=True)
        subprocess.run(["git", "clean", "-fd"], check=True)
        subprocess.run(["git", "checkout", branch], check=True)
    else:
        logging.info(".git directory already exists.")

def _get_latest_tag() -> str:
    return subprocess.getoutput("git describe --tags --abbrev=0")

def _get_latest_remote_tag(branch: str) -> str:
    subprocess.run(["git", "fetch", "--tags", "origin", branch], check=True)
    latest_commit = subprocess.getoutput(f"git rev-list --tags --max-count=1 --branches=origin/{branch}")
    return subprocess.getoutput(f"git describe --tags --abbrev=0 {latest_commit}")

def _fetch_latest_tags(branch: str) -> None:
    subprocess.run(["git", "fetch", "--tags", "origin", branch], check=True)

def _should_update(local_tag: str, remote_tag: str) -> bool:
    logging.info(f"Comparing local tag: {local_tag} to remote tag: {remote_tag}")
    return local_tag != remote_tag

def _update_repository(target_tag: str) -> None:
    logging.info(f"Updating to tag: {target_tag}")
    subprocess.run(["git", "reset", "--hard", target_tag], check=True)
    logging.info("Repository updated to the latest tag.")

def _stop_server_on_port(ports_to_kill: List[int]) -> None:
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

def _contains_special_token(tag: str, token: str) -> bool:
    return token in tag

def _print_changes_since_last_tag(local_tag: str, remote_tag: str) -> None:
    logging.info("Changes since last update:")
    changes = subprocess.getoutput(f"git log {local_tag}..{remote_tag} --pretty=format:'%h - %s (%cd) [%an]' --date=format:'%Y-%m-%d %H:%M:%S'")
    if changes:
        logging.info(changes)
    else:
        logging.info("No changes were found, or the tags are identical.\n")

def run_autoupdate(restart_script: str, env_autoup_token: str, server_special_token: str, branch: str, ports_to_kill: List[int], auto_updates_sleep: int) -> None:
    while True:
        _fetch_latest_tags(branch)
        local_tag = _get_latest_tag()
        remote_tag = _get_latest_remote_tag(branch)

        if _should_update(local_tag, remote_tag) and _contains_special_token(remote_tag, env_autoup_token):
            logging.info("Local repository is not up-to-date. Updating...")
            _update_repository(remote_tag)
            _print_changes_since_last_tag(local_tag, remote_tag)
            if _contains_special_token(remote_tag, server_special_token):
                logging.info("Remote tag contains required token. Running the autoupdate steps...")
                _stop_server_on_port(ports_to_kill)
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

    auto_updates_sleep = int(os.getenv('AUTOUP_SLEEP', '200'))
    server_special_token = os.getenv('SERVER_RELOAD_GIT_TOKEN', 'reload_orch')
    env_autoup_token = os.getenv('ENV_TOKEN_AUTOUP', 'dev')
    git_branch = os.getenv('BRANCH', 'feature/auto-updates')
    git_repo = os.getenv('GIT_REPO', 'corcel-api/vision-workers') 
    git_pat = os.getenv('GIT_PAT', '')
    if git_pat != '':
        repo_url = f"https://{git_pat}@github.com/{git_repo}.git"
    else:
        repo_url = f"https://github.com/{git_repo}.git"


    orchestrator_port = int(os.getenv('CURRENT_SERVER_PORT', 6920))
    service_port = int(os.getenv('SERVICE_SERVER_PORT', 6919))
    comfyui_port = int(os.getenv('COMFYUI_SERVER_PORT', 8188))

    time.sleep(auto_updates_sleep)
    _initialize_git_if_needed(repo_url=repo_url, branch=git_branch)

    logging.info(f"Listening for Git tag updates with tags containing the token: {env_autoup_token}, and only reloading if the token {server_special_token} is specified")

    run_autoupdate(
        restart_script=args.restart_script,
        env_autoup_token=env_autoup_token,
        server_special_token=server_special_token,
        branch=git_branch,
        ports_to_kill=[orchestrator_port, service_port, comfyui_port],
        auto_updates_sleep=auto_updates_sleep
    )
