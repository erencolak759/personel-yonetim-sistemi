const { spawnSync, spawn } = require('child_process')
const fs = require('fs')
const path = require('path')

function whichPython() {
  const tryCmd = (cmd) => {
    try {
      const res = spawnSync(cmd, ['--version'], { stdio: 'ignore' })
      return res.status === 0
    } catch (e) {
      return false
    }
  }
  if (tryCmd('python3')) return 'python3'
  if (tryCmd('python')) return 'python'
  throw new Error('Python is not available in PATH')
}

function runSync(cmd, args, opts = {}) {
  const r = spawnSync(cmd, args, { stdio: 'inherit', ...opts })
  if (r.status !== 0) {
    throw new Error(`${cmd} ${args.join(' ')} failed with code ${r.status}`)
  }
}

async function main() {
  const repoRoot = path.resolve(__dirname, '..')
  const backendDir = path.join(repoRoot, 'apps', 'backend')
  const venvDir = path.join(backendDir, 'venv')
  const pythonCmd = whichPython()

  const args = process.argv.slice(2)
  const installOnly = args.includes('--install-only')
  const forceInstall = args.includes('--install')

  let venvCreated = false
  if (!fs.existsSync(venvDir)) {
    console.log('Creating virtual environment...')
    runSync(pythonCmd, ['-m', 'venv', 'venv'], { cwd: backendDir })
    venvCreated = true
  }

  const venvPython = process.platform === 'win32'
    ? path.join(venvDir, 'Scripts', 'python.exe')
    : path.join(venvDir, 'bin', 'python')

  if (!fs.existsSync(venvPython)) {
    throw new Error('Virtualenv python executable not found at ' + venvPython)
  }

  const reqFile = path.join(backendDir, 'requirements.txt')
  const skipPip = process.env.SKIP_PIP_INSTALL === '1'
  if (forceInstall || installOnly || (venvCreated && !skipPip)) {
    console.log('Installing backend requirements...')
    runSync(venvPython, ['-m', 'pip', 'install', '--upgrade', 'pip'], { cwd: backendDir })
    if (fs.existsSync(reqFile)) {
      runSync(venvPython, ['-m', 'pip', 'install', '-r', 'requirements.txt'], { cwd: backendDir })
    } else {
      console.log('requirements.txt not found - skipping pip install')
    }
  } else {
    console.log('Skipping pip install (use --install to force).')
  }

  if (installOnly) {
    console.log('Install complete.')
    return
  }

  console.log('Starting backend using venv python:', venvPython)
  const server = spawn(venvPython, ['app.py'], { cwd: backendDir, stdio: 'inherit' })

  server.on('exit', (code) => {
    process.exit(code)
  })
}

main().catch((err) => {
  console.error(err.message || err)
  process.exit(1)
})
