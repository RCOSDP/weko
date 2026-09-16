module.exports = {
  apps: [
    {
      name: 'AMS',
      port: '3000',
      exec_mode: 'cluster',
      instances: 2,
      node_args: '--max-old-space-size=256',
      max_memory_restart: '320M',
      script: '/usr/local/weko-frontend/.output/server/index.mjs'
    }
  ]
}
