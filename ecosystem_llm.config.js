module.exports = {
    apps: [
      {
        name: "entrypoint",
        script: "./entrypoint.sh",
        cwd: "/app/llm_server",
        watch: false,
        autorestart: false
      }
    ]
  };
  