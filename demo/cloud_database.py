"""Start a disposable loopback-only PostgreSQL for Community Cloud demos."""
import atexit
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile


def start_database():
    if os.getenv('DATABASE_URL'):
        return os.environ['DATABASE_URL']
    candidates = sorted(Path('/usr/lib/postgresql').glob('*/bin/initdb'))
    if not candidates:
        raise RuntimeError('PostgreSQL is missing. Deploy with the repository packages.txt file.')
    binaries = candidates[-1].parent
    root = Path(tempfile.mkdtemp(prefix='finance-demo-'))
    data = root / 'data'
    def run(name, *args):
        result = subprocess.run([str(binaries / name), *map(str, args)], capture_output=True, text=True, timeout=90)
        if result.returncode:
            raise RuntimeError(f'Demo database setup failed at {name}. Check the hosting logs.')
        return result
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0)); port = probe.getsockname()[1]
    run('initdb', '-D', data, '-U', 'demo', '-A', 'trust', '--no-locale', '--encoding=UTF8')
    run('pg_ctl', '-D', data, '-l', root / 'postgres.log', '-o',
        f'-h 127.0.0.1 -p {port} -c unix_socket_directories={root} -c shared_buffers=16MB -c max_connections=12 -c work_mem=2MB', '-w', 'start')
    atexit.register(lambda: subprocess.run([str(binaries / 'pg_ctl'), '-D', str(data), '-m', 'fast', 'stop'], capture_output=True, timeout=30))
    run('createdb', '-h', '127.0.0.1', '-p', port, '-U', 'demo', 'finance_demo')
    return f'postgresql://demo@127.0.0.1:{port}/finance_demo'
