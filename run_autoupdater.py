import subprocess
import time
import os
import argparse


def get_latest_tag():
    return subprocess.getoutput("git describe --tags --abbrev=0")

def get_latest_remote_tag(branch):
    subprocess.run(["git", "fetch", "--tags", "origin", branch], check=True)
    latest_commit = subprocess.getoutput(f"git rev-list --tags --max-count=1 --branches=origin/{branch}")
    return subprocess.getoutput(f"git describe --tags --abbrev=0 {latest_commit}")


def fetch_latest_tags(branch):
    subprocess.run(["git", "fetch", "--tags", "origin", branch], check=True)

def should_update(local_tag, remote_tag):
    print(f"Comparing local tag: {local_tag} to remote tag: {remote_tag}")
    return local_tag != remote_tag

def update_repository(target_tag):
    print(f"Updating to tag: {target_tag}")
    subprocess.run(["git", "reset", "--hard", target_tag], check=True)
    print("Repository updated to the latest tag.")

def stop_server_on_port(ports_to_kill):
    for port in ports_to_kill:
        print("Stopping the server with port {} ...".format(port))
        try:
            subprocess.run(f"kill $(lsof -t -i:{port})", shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error stopping the server: {e}")

        # Wait for the port to become free
        while True:
            result = subprocess.run(f"lsof -i:{port}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 1:
                print("Server stopped successfully.")
                break
            else:
                print("Waiting for the server process to stop...")
                time.sleep(1)
    print('All servers stopped successfully!')

def contains_special_token(tag, token):
    return token in tag

def print_changes_since_last_tag(local_tag, remote_tag):
    print("\nChanges since last update:")
    # Fetching commit messages between local and remote tags
    changes = subprocess.getoutput(f"git log {local_tag}..{remote_tag} --pretty=format:'%h - %s (%cd) [%an]' --date=format:'%Y-%m-%d %H:%M:%S'")
    if changes:
        print("=============================================")
        print(changes)
        print("=============================================\n")
    else:
        print("No changes were found, or the tags are identical.\n")

def run_autoupdate(restart_script: str, env_autoup_token: str, server_special_token: str, ports_to_kill: list, branch: str, auto_updates_sleep: int):
    while True:
        fetch_latest_tags(branch)
        local_tag = get_latest_tag()
        remote_tag = get_latest_remote_tag(branch)

        if should_update(local_tag, remote_tag) and contains_special_token(remote_tag, env_autoup_token):
            print(f"Local repository is not up-to-date. Updating...")
            update_repository(remote_tag)
            print_changes_since_last_tag(local_tag, remote_tag)
            if contains_special_token(remote_tag, server_special_token):
                print(f"Remote tag contains required token. Running the autoupdate steps...")
                stop_server_on_port(ports_to_kill)
                subprocess.run(f"chmod +x {restart_script}", shell=True)
                subprocess.Popen(f"/bin/sh {restart_script}", shell=True)
                print("Finished running the autoupdate steps! Server is ready.")
            else:
                print("Local repository is up-to-date, no restard needed since server token was not mentioned")
        else:
            print("Local repository is up-to-date or the tag does not contain the required token.")
        time.sleep(auto_updates_sleep)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--restart_script", type=str)
    args = parser.parse_args()

    auto_updates_sleep = int(os.environ.get('AUTOUP_SLEEP', '60'))
    current_env = os.environ.get('CURRENT_ENV', 'dev').lower()
    branch = os.environ.get('GIT_BRANCH', 'main' if current_env == 'prod' else 'dev')
    server_special_token = os.environ.get('SERVER_RELOAD_GIT_TOKEN', 'none')
    env_autoup_token = "_prod" if current_env == "prod" else "_dev"

    orchestrator_port = int(os.environ.get('CURRENT_SERVER_PORT', 6920))
    service_port = int(os.environ.get('SERVICE_SERVER_PORT', 6919))
    comfyui_port = int(os.environ.get('COMFYUI_SERVER_PORT', 8188))

    print(f"\nEnvironment: {current_env.upper()}")
    print(f"Listening for Git tag updates on branch '{branch}' with tags containing the tokens: '{env_autoup_token}, {server_special_token}'\n")

    run_autoupdate(restart_script=args.restart_script, 
                   env_autoup_token=env_autoup_token, 
                   server_special_token=server_special_token,
                   ports_to_kill=[orchestrator_port, service_port, comfyui_port],
                   branch=branch,
                   auto_updates_sleep=auto_updates_sleep)
