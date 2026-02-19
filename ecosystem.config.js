const path = require('path');

module.exports = {
  apps: [{
    name: 'smart-home',
    script: 'main.py',
    cwd: __dirname,
    interpreter: path.join(__dirname, '.venv', 'bin', 'python'),
    env: {
      PORT: 7999,
    },
    watch: false,
    autorestart: true,
    max_restarts: 3,
    restart_delay: 3000,
  }]
};
