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
        name: "entrypoint",
        script: "./entrypoint.sh",
        cwd: "/llm_server",
        watch: false,
        autorestart: false
      }
    ]
  };
  