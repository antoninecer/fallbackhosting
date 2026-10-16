"""Nginx adapter and persisted health/maintenance gate. No shared service edits."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request

from standby.snapshot import NoRedirect, origin_url


def safe_path(value):
    value = str(Path(value).absolute())
    if not re.fullmatch(r'/[a-zA-Z0-9_./-]+', value): raise ValueError('Unsafe Nginx path')
    return value


def server_locations(origin, current, gate, maintenance, prefix=''):
    origin = origin_url(origin)
    if not origin.startswith('http://'): raise ValueError('First gateway adapter requires trusted private HTTP backend')
    if prefix and not re.fullmatch('/[a-z][a-z0-9-]{0,39}',prefix): raise ValueError('Invalid app prefix')
    current, gate, maintenance = map(safe_path, (current, gate, maintenance))
    standby_uri = '/__standby' + prefix.replace('/','_')
    redirect = f'location = {prefix} {{ return 308 {prefix}/; }}\n' if prefix else ''
    rewrite = '''proxy_set_header Accept-Encoding "";
        sub_filter_once off;
        sub_filter 'href="/' 'href="PREFIX/';
        sub_filter 'src="/' 'src="PREFIX/';
        sub_filter 'action="/' 'action="PREFIX/';'''.replace('PREFIX',prefix) if prefix else ''
    return redirect + f'''
    location ^~ {prefix}/__fallback_assets/ {{
        alias {current}/assets/;
        autoindex off;
        add_header Cache-Control "no-cache" always;
        add_header X-Content-Type-Options nosniff always;
    }}
    location = {standby_uri} {{
        internal;
        root {current};
        try_files /index.html =503;
        add_header X-Fallback-Mode standby always;
        add_header Cache-Control "no-store" always;
        add_header Retry-After 60 always;
        add_header X-Robots-Tag "noindex" always;
        add_header Content-Security-Policy "default-src 'none'; style-src 'self'; img-src 'self'; font-src 'self'; form-action 'none'; frame-ancestors 'none'; base-uri 'none'" always;
        add_header X-Content-Type-Options nosniff always;
    }}
    location {prefix}/ {{
        error_page 500 502 503 504 =503 {standby_uri};
        if (-f {maintenance}) {{ return 503; }}
        if (-f {gate}) {{ return 503; }}
        proxy_pass {origin}/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_connect_timeout 1s;
        proxy_read_timeout 3s;
        proxy_send_timeout 3s;
        proxy_intercept_errors on;
        proxy_next_upstream off;
        {rewrite}
        add_header X-Fallback-Mode online always;
        add_header Cache-Control "no-store" always;
    }}
'''


def server_config(origin, current, gate, maintenance, listen='127.0.0.1:18081', hostname='localhost', prefix=''):
    if not re.fullmatch(r'127\.0\.0\.1:[0-9]{2,5}', listen) or not 1 <= int(listen.rsplit(':',1)[1]) <= 65535: raise ValueError('Only loopback prototype listeners accepted')
    if not re.fullmatch(r'[a-zA-Z0-9.-]+', hostname): raise ValueError('Invalid hostname')
    locations = server_locations(origin,current,gate,maintenance,prefix)
    return f'server {{\nlisten {listen};\nserver_name {hostname};\nclient_max_body_size 64k;\n' + locations + '\n}\n'


def standalone_config(server, prefix):
    prefix = safe_path(prefix)
    return f'''worker_processes 1;
pid {prefix}/nginx.pid;
error_log {prefix}/error.log warn;
events {{ worker_connections 128; }}
http {{
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    access_log off;
    client_body_temp_path {prefix}/client-body;
    proxy_temp_path {prefix}/proxy-temp;
    {server}
}}
'''


def parse_time(value):
    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)


def maintenance_active(windows, now):
    if not isinstance(windows, list) or len(windows) > 100: raise ValueError('Bounded maintenance list required')
    active = False
    for w in windows:
        if set(w) != {'start_utc', 'end_utc'}: raise ValueError('Invalid window')
        start, end = parse_time(w['start_utc']), parse_time(w['end_utc'])
        if end <= start: raise ValueError('Invalid maintenance range')
        active |= start <= now < end
    return active


def atomic_json(path, value):
    path = Path(path); temp = path.with_name(path.name + '.pending')
    temp.write_text(json.dumps(value, indent=2) + '\n'); temp.replace(path)


def tick(origin, runtime, now=None, healthy_required=3):
    """Operator-owned process: health failure closes gate; stable success opens it.

    If this process dies, Nginx retains its last safe gate and still independently
    intercepts origin errors. Schedule transitions require this process running.
    """
    origin = origin_url(origin); runtime = Path(runtime); runtime.mkdir(parents=True, exist_ok=True)
    now = now or datetime.now(timezone.utc)
    config = json.loads((runtime/'control.json').read_text())
    if set(config) != {'manual_maintenance', 'windows'} or type(config['manual_maintenance']) is not bool: raise ValueError('Invalid control config')
    active = config['manual_maintenance'] or maintenance_active(config['windows'], now)
    marker = runtime/'maintenance'
    if active: marker.touch()
    state = json.loads((runtime/'health.json').read_text()) if (runtime/'health.json').exists() else {'successes': 0}
    okay = False
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        with opener.open(origin + '/health', timeout=2) as response:
            okay = response.status == 200 and response.read(100) == b'fallback-demo-healthy\n'
    except Exception: pass
    successes = min(healthy_required, state['successes'] + 1) if okay else 0
    gate = runtime/'unhealthy'
    if successes < healthy_required: gate.touch()
    elif gate.exists(): gate.unlink()
    maintenance_recovery = active or (state.get('maintenance_recovery', False) and successes < healthy_required)
    result = {'utc': now.strftime('%Y-%m-%dT%H:%M:%SZ'), 'healthy': okay, 'successes': successes,
              'maintenance_recovery': maintenance_recovery,
              'mode': 'MAINTENANCE' if active else ('ONLINE' if successes >= healthy_required else ('OVERRUN' if maintenance_recovery else 'STANDBY'))}
    atomic_json(runtime/'health.json', result)
    # Keep maintenance closed until its independent health gate is settled.
    if not active and marker.exists(): marker.unlink()
    return result
