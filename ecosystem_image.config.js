module.exports = {
    apps: [
      {
        name: "entrypoint",
        script: "./entrypoint.sh",
        cwd: "/app/image_server",
        watch: false,
        autorestart: false
      }
    ]
  };
  