module.exports = {
  apps: [{
    name: 'langfuse-mcp',
    script: 'python3',
    args: ['-m', 'langfuse_mcp'],
    cwd: '/home/ted/repos/personal/langfuse-mcp',
    interpreter: 'none',
    autorestart: true,
    watch: false,
    env: {
      LANGFUSE_BASE_URL: 'http://localhost:3000',
      LOG_LEVEL: 'INFO',
      LOG_FILE: '/home/ted/logs/langfuse-mcp.log',
      // LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY injected via:
      // pm2 start ecosystem.config.js --env-file ~/.secrets/forge.env
    },
  }],
};
