module.exports = {
    apps: [
      {
        name: "entrypoint",
        script: "./entrypoint.sh",
        cwd: "/image_server",
        watch: false,
        autorestart: false
      }
    ]
  };
  