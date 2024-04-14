module.exports = {
    apps: [
      {
        name: "autoupdater",
        script: "./run_autoupdater.py",
        args: "--restart_script /image_autoupdater_action.sh",
        interpreter: "python",
        watch: false,
        autorestart: false
      },
      {
        name: "entrypoint",
        script: "./entrypoint.sh",
        cwd: "/image_server",
        watch: false,
        autorestart: false
      }
    ]
  };
  