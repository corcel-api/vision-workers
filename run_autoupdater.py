import subprocess
import time
import os

def fetch_latest_tags():
    # Explicitly fetch all tags from the remote repository
    subprocess.run(["git", "fetch", "--tags"], check=True)

def get_latest_tag():
    # Get the latest tag from the local repository
    return subprocess.getoutput("git describe --tags --abbrev=0")

def get_latest_remote_tag():
    # Get the latest tag from the remote repository
    return subprocess.getoutput("git describe --tags --abbrev=0 `git rev-list --tags --max-count=1`")

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

def run_autoupdate(restart_script: str, special_token: str, ports_to_kill: list):
    while True:
        fetch_latest_tags()
        local_tag = get_latest_tag()
        remote_tag = get_latest_remote_tag()

        if should_update(local_tag, remote_tag):
            print("Local repository is not up-to-date. Updating...")
            update_repository(remote_tag)
            print_changes_since_last_tag(local_tag, remote_tag)
            if contains_special_token(remote_tag, special_token):
                print("Remote tag contains special token. Running the autoupdate steps...")
                stop_server_on_port(ports_to_kill)
                subprocess.run(f"chmod +x {restart_script}", shell=True) 
                subprocess.Popen(f"/bin/sh {restart_script}", shell=True)
                print("Finished running the autoupdate steps! Server is ready.")
            else:
                print("Updated local repository without needing to restart the server.")
        else:
            print("Local repository is up-to-date.")
        time.sleep(10)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--restart_script", type=str)
    args = parser.parse_args()

    orchestrator_port = int(os.environ.get('CURRENT_SERVER_PORT', 6920))
    service_port = int(os.environ.get('SERVICE_SERVER_PORT', 6919))
    comfyui_port = int(os.environ.get('COMFYUI_SERVER_PORT', 8188))

    token = os.environ.get('SERVER_RELOAD_GIT_TOKEN', '')

    print(f"\nListening for Git tag updates on port {orchestrator_port}.")
    print(f"Listening for tags containing the token: '{token}' (if specified).\n")


    run_autoupdate(restart_script=args.restart_script, 
                   special_token=token, 
                   ports_to_kill=[orchestrator_port, service_port, comfyui_port])
