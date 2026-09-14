import { spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import path from 'node:path'

const root = path.resolve(import.meta.dirname, '..')
const local = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python')
const executable = process.env.V3_PYTHON || (existsSync(local) ? local : 'python3')
const result = spawnSync(executable, process.argv.slice(2), { cwd: root, stdio: 'inherit', env: process.env })
if (result.error) process.stderr.write(`${result.error.message}\n`)
process.exit(result.status ?? 1)
