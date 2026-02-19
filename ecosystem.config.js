const path = require('path');

module.exports = {
  apps: [{
    name: 'smart-home',
    script: path.join(__dirname, 'start_server.sh'),
    interpreter: '/bin/bash',
    cwd: __dirname,
    env: {
      PORT: 7999,
    },
    watch: false,
    autorestart: true,
    max_restarts: 3,
    restart_delay: 3000,
  }]
};
