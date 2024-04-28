module.exports = {
    apps: [
      {
        name: "entrypoint",
        script: "./entrypoint.sh",
        cwd: "/app/validator_orchestrator",
        watch: false,
        autorestart: true
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
  