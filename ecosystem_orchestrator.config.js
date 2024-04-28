module.exports = {
    apps: [
      {
        name: "download_models",
        script: "./setup.sh",
        cwd: "/app/image_server",
        watch: false,
        autorestart: false
      },
      {
        name: "entrypoint",
        script: "./entrypoint.sh",
        cwd: "/app/validator_orchestrator",
        watch: false,
        autorestart: false
      },
      {
        name: "autoupdater",
        script: "./run_autoupdater.py",
        args: "--restart_script /app/orchestrator_autoupdater_action.sh",
        interpreter: "python",
        watch: false,
        autorestart: false
      }
    ]
  };
  