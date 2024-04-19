module.exports = {
    apps: [
      {
        name: "fineTuneModelUpdate",
        script: "./update_finetune_model.py",
        interpreter: "python",
        cwd: "/app/llm_server",
        watch: false,
        autorestart: true
      },
      {
        name: "entrypoint",
        script: "./entrypoint.sh",
        cwd: "/app/llm_server",
        watch: false,
        autorestart: false
      }
    ]
  };
  