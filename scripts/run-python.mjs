import { spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import path from 'node:path'

const root = path.resolve(import.meta.dirname, '..')
const local = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python')
const executable = process.env.V3_PYTHON || (existsSync(local) ? local : 'python3')
const args = process.argv.slice(2)
const options = []
let offset = 0
// Keep interpreter switches before the bootstrap, and target arguments after
// it. Project callers use script, -m, -c and stdin modes; Python still parses
// its own flags rather than having the bootstrap silently reinterpret them.
while (offset < args.length && args[offset].startsWith('-') && !['-m', '-c', '-', '--'].includes(args[offset])) {
  const option = args[offset++]
  options.push(option)
  if (['-W', '-X', '--check-hash-based-pycs'].includes(option) && offset < args.length) options.push(args[offset++])
}
const informational = options.some(option => ['-h', '--help', '-V', '-VV', '--version'].includes(option))
const launchArgs = !args.length || informational ? args : [...options, path.join(root, 'scripts/sqlite_runtime.py'), '--', ...args.slice(offset)]
const result = spawnSync(executable, launchArgs, { cwd: root, stdio: 'inherit', env: process.env })
if (result.error) process.stderr.write(`${result.error.message}\n`)
process.exit(result.status ?? 1)
