const { spawnSync, spawn } = require('child_process')
const fs = require('fs')
const path = require('path')

function whichPython() {
  // Prefer python3, fallback to python
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

  // Create venv if not exists
  if (!fs.existsSync(venvDir)) {
    console.log('Creating virtual environment...')
    runSync(pythonCmd, ['-m', 'venv', 'venv'], { cwd: backendDir })
  }

  // Determine venv python path
  const venvPython = process.platform === 'win32'
    ? path.join(venvDir, 'Scripts', 'python.exe')
    : path.join(venvDir, 'bin', 'python')

  if (!fs.existsSync(venvPython)) {
    throw new Error('Virtualenv python executable not found at ' + venvPython)
  }

  // Only install requirements when explicitly requested. This avoids
  // reinstalling packages on every `pnpm dev` invocation. The script will
  // still create the virtualenv if it does not exist, but will not run
  // `pip install -r requirements.txt` unless `--install` or
  // `--install-only` is passed.
  const reqFile = path.join(backendDir, 'requirements.txt')

  if (forceInstall || installOnly) {
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

  // Run the Flask app using venv python
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
