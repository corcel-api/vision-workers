module.exports = {
    apps: [
      {
        name: "fineTuneModelUpdate",
        script: "./update_finetune_model.py",
        interpreter: "python",
        cwd: "/llm_server",
        watch: false,
        autorestart: true
      },
      {
        name: "autoupdater",
        script: "./run_autoupdater.py",
        args: "--restart_script /llm_autoupdater_action.sh",
        interpreter: "python",
        watch: false,
        autorestart: false
      },
      {
        name: "entrypoint",
        script: "./entrypoint.sh",
        cwd: "/llm_server",
        watch: false,
        autorestart: false
      }
    ]
  };
  