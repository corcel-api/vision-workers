import os
import subprocess
import time


def should_update_local(local_tag, remote_tag):
    if remote_tag[0] == local_tag[0]:
        return remote_tag != local_tag
    return False

def contains_special_token(tag, token):
    return token in tag

def stop_server_on_port(port):
    print("Stopping the server...")
    # Find and kill the process listening on the given port
    try:
        subprocess.run(f"kill $(lsof -t -i:{port})", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error stopping the server: {e}")

    # Wait for the port to become free
    while True:
        result = subprocess.run(f"lsof -i:{port}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 1:  # Assuming return code 1 means the port is free (no process found)
            print("Server stopped successfully.")
            break
        else:
            print("Waiting for process to stop...")
            time.sleep(1)


def run_autoupdate(restart_script: str, port: int, special_token: str):
    while True:
        local_tag = subprocess.getoutput("git describe --abbrev=0 --tags")
        os.system("git fetch")
        remote_tag = subprocess.getoutput(
            "git describe --tags `git rev-list --topo-order --tags HEAD --max-count=1`"
        )
        # always update local repo if there's a change
        if should_update_local(local_tag, remote_tag):
            print("Local repo is not up-to-date. Updating...")
            reset_cmd = "git reset --hard " + remote_tag
            process = subprocess.Popen(reset_cmd.split(), stdout=subprocess.PIPE)
            output, error = process.communicate()
            if error:
                print("Error in updating:", error)
            else:
                print(f"Updated local repo to latest version: {remote_tag}")

                # Only restart the process if the remote tag contains a special token (1 token per server type)
                if contains_special_token(remote_tag, special_token):
                    print("Remote tag contains special token. Running the autoupdate steps...")
                    stop_server_on_port(port)
                    restart_process = subprocess.Popen([f"./{restart_script}"], shell=True)
                    process_pid = restart_process.pid
                    print("Finished running the autoupdate steps! Ready to go 😎")
                else:
                    print("Updated local repo without needing to restart the process.")
        else:
            print("Repo is up-to-date.")
        time.sleep(10)



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--restart_script", type=str)
    args = parser.parse_args()


    port = os.environ.get('CURRENT_SERVER_PORT')
    if port is None:
        print("CURRENT_SERVER_PORT is not defined! setting port (for autoupdater) to 6919")
        port = 6919
    port = int(port)

    token = os.environ.get('SERVER_RELOAD_GIT_TOKEN')
    if token is None:
        print("SERVER_RELOAD_GIT_TOKEN is not defined! server will never reload when changes occur!")
        token = ''

    run_autoupdate(restart_script=args.restart_script, port=port, special_token=token)