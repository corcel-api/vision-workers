module.exports = {
    apps: [
      {
        name: "autoupdater",
        script: "./run_autoupdater.py",
        args: "--restart_script /orchestrator_autoupdater_action.sh",
        interpreter: "python",
        watch: false
      },
      {
        name: "entrypoint",
        script: "./entrypoint.sh",
        cwd: "/validator_orchestrator",
        watch: false
      }
    ]
  };
  