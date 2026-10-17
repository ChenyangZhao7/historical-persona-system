#!/usr/bin/env node
// Cross-platform launcher for the FastAPI backend.
//
// The old npm script hardcoded `../venv/bin/uvicorn`, which only exists on
// macOS/Linux. This resolves the interpreter for the current platform and
// falls back to whatever `python` is on PATH.
//
// Usage:
//   node scripts/run-backend.mjs           # dev server with reload
//   node scripts/run-backend.mjs --test    # run the pytest suite
import { spawn, spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const repoRoot = dirname(dirname(fileURLToPath(import.meta.url)))
const isWindows = process.platform === 'win32'

const venvPython = isWindows
  ? join(repoRoot, 'venv', 'Scripts', 'python.exe')
  : join(repoRoot, 'venv', 'bin', 'python')

const python = existsSync(venvPython)
  ? venvPython
  : (isWindows ? 'python' : 'python3')

const hasWatchfiles = spawnSync(python, ['-c', 'import watchfiles'], { stdio: 'ignore' }).status === 0

if (!existsSync(venvPython)) {
  console.warn('[backend] no venv found at venv/ — using "' + python + '" from PATH')
}
if (!hasWatchfiles) {
  console.warn('[backend] watchfiles not installed: running without --reload')
  console.warn('[backend] (pip install watchfiles to get hot reload)')
}

const args = process.argv.includes('--test')
  ? ['-m', 'pytest', 'tests', '-v']
  : ['-m', 'uvicorn', 'main:app', '--port', '8000', ...(hasWatchfiles ? ['--reload'] : [])]

const child = spawn(python, args, { cwd: join(repoRoot, 'backend'), stdio: 'inherit' })

child.on('exit', code => process.exit(code ?? 0))
child.on('error', err => {
  console.error('[backend] failed to start:', err.message)
  process.exit(1)
})
