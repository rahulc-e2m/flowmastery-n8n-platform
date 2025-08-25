#!/usr/bin/env node

const { spawn } = require('child_process')
const fs = require('fs')
const path = require('path')

console.log('🚀 Starting FlowMastery Frontend Development Environment')

// Check if .env file exists
const envFile = path.join(__dirname, '.env')
const envExampleFile = path.join(__dirname, '.env.example')

if (!fs.existsSync(envFile)) {
  console.log('📝 Creating .env file from .env.example...')
  try {
    const envExample = fs.readFileSync(envExampleFile, 'utf8')
    fs.writeFileSync(envFile, envExample)
    console.log('✅ .env file created. You can update it with your configuration.')
  } catch (error) {
    console.error('❌ Failed to create .env file:', error.message)
    process.exit(1)
  }
}

// Check if node_modules exists
const nodeModulesPath = path.join(__dirname, 'node_modules')
if (!fs.existsSync(nodeModulesPath)) {
  console.log('📦 Installing dependencies...')
  const installProcess = spawn('npm', ['install'], {
    stdio: 'inherit',
    shell: true,
    cwd: __dirname
  })

  installProcess.on('close', (code) => {
    if (code !== 0) {
      console.error('❌ Failed to install dependencies')
      process.exit(1)
    }
    startDevServer()
  })
} else {
  startDevServer()
}

function startDevServer() {
  console.log('🌟 Starting Vite development server...')
  
  const devProcess = spawn('npm', ['run', 'dev'], {
    stdio: 'inherit',
    shell: true,
    cwd: __dirname
  })

  devProcess.on('close', (code) => {
    console.log(`Development server exited with code ${code}`)
  })

  // Handle Ctrl+C
  process.on('SIGINT', () => {
    console.log('\n🛑 Shutting down development server...')
    devProcess.kill('SIGINT')
    process.exit(0)
  })
}