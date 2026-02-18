module.exports = {
  apps: [{
    name: 'smart-home',
    script: 'main.py',
    cwd: '/Users/grapeot/co/knowledge_working/adhoc_jobs/smart_home',
    interpreter: '/Users/grapeot/co/knowledge_working/adhoc_jobs/smart_home/.venv/bin/python',
    env: {
      PORT: 7999,
    },
    watch: false,
    autorestart: true,
    max_restarts: 3,
    restart_delay: 3000,
  }]
};
