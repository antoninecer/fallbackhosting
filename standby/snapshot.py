"""Bounded, explicit public-page export using installed ImageMagick.

First adapter supports one reviewed HTML page, one CSS file and one raster image.
It intentionally rejects unsupported assets rather than pretending to mirror any site.
"""
from datetime import datetime, timezone
from html import escape
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
import subprocess
import urllib.parse
import urllib.request
import uuid

FILES = ('index.html', 'style.css', 'hero.jpg')
ALLOWED = set('html head title meta body header main section article footer nav h1 h2 h3 p a img link div span strong em small ul ol li br hr details summary'.split())
VOID = {'meta', 'img', 'link', 'br', 'hr'}
DROP = {'script', 'style', 'iframe', 'object', 'embed', 'svg', 'math', 'template', 'form', 'video', 'audio'}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Export redirects are unsupported; approve the final origin explicitly.')


def origin_url(value):
    u = urllib.parse.urlsplit(value)
    if (u.scheme not in ('http', 'https') or not u.hostname or u.username or u.password
            or u.path not in ('', '/') or u.query or u.fragment
            or not re.fullmatch(r'[A-Za-z0-9.-]+', u.hostname)):
        raise ValueError('An explicitly approved HTTP(S) origin without credentials/path is required.')
    if u.port is not None and not 1 <= u.port <= 65535:
        raise ValueError('Invalid origin port')
    return value.rstrip('/')


class StaticPage(HTMLParser):
    def __init__(self, message, contact, asset_prefix):
        super().__init__(convert_charrefs=True)
        self.parts = []; self.suppressed = []; self.message = message; self.contact = contact
        self.asset_prefix = asset_prefix; self.replacing_anchor = False

    def handle_starttag(self, tag, attrs):
        if self.suppressed:
            if tag in DROP: self.suppressed.append(tag)
            return
        if tag in DROP:
            self.suppressed.append(tag)
            if tag == 'form': self.parts.append('<p>Online formulář je během údržby nedostupný. Použijte kontakt níže.</p>')
            return
        if tag not in ALLOWED: return
        attrs = dict(attrs); clean = {}
        for key in ('class', 'id', 'lang', 'charset', 'name', 'content', 'width', 'height', 'alt', 'loading', 'role', 'aria-label'):
            if isinstance(attrs.get(key), str): clean[key] = attrs[key]
        if tag == 'meta' and attrs.get('name', '').lower() not in ('viewport', 'description') and 'charset' not in attrs: return
        if tag == 'link':
            if attrs.get('rel') != 'stylesheet' or attrs.get('href') not in ('style.css', '/style.css'): return
            clean.update(rel='stylesheet', href=self.asset_prefix + '/style.css')
        if tag == 'img':
            if attrs.get('src') not in ('hero.jpg', '/hero.jpg'): raise ValueError('Unapproved image')
            clean.update(src=self.asset_prefix + '/hero.webp', loading='lazy')
        if tag == 'a':
            href = attrs.get('href', '')
            home = href in ('/', '/index.html', 'index.html', './')
            self.replacing_anchor = not home and not bool(re.fullmatch(r'#[A-Za-z][A-Za-z0-9_-]*', href))
            clean['href'] = '#' if home else (href if not self.replacing_anchor else '#fallback-contact')
        self.parts.append('<' + tag + ''.join(' ' + k + '="' + escape(v, quote=True) + '"' for k, v in clean.items()) + '>')
        if tag == 'a' and self.replacing_anchor: self.parts.append('Kontakt během údržby')
        if tag == 'body':
            self.parts.append('<aside role="status" class="fallback-notice"><strong>Dočasně omezený provoz</strong><p>' + escape(self.message) + '</p></aside>')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID: self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if self.suppressed:
            if tag == self.suppressed[-1]: self.suppressed.pop()
            return
        if tag not in ALLOWED or tag in VOID: return
        if tag == 'a': self.replacing_anchor = False
        if tag == 'body':
            self.parts.append('<section id="fallback-contact"><h2>Kontakt během údržby</h2><p>' + escape(self.contact) + '</p><p>Online objednávky, přihlášení a vyhledávání jsou dočasně nedostupné.</p></section>')
        self.parts.append('</' + tag + '>')

    def handle_data(self, data):
        if not self.suppressed and not self.replacing_anchor: self.parts.append(escape(data))


def build(origin, releases, message, contact, asset_prefix='/__fallback_assets'):
    origin = origin_url(origin)
    if not re.fullmatch(r'/[a-zA-Z0-9_/-]+',asset_prefix) or '//' in asset_prefix: raise ValueError('Invalid asset prefix')
    if not 1 <= len(message) <= 500 or not 1 <= len(contact) <= 300: raise ValueError('Bounded public message/contact required')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    bodies = {}
    for name in FILES:
        request = urllib.request.Request(origin + '/' + name, headers={'User-Agent': 'FallbackHosting-ApprovedExport/1', 'Accept-Encoding': 'identity'})
        with opener.open(request, timeout=8) as response:
            if response.headers.get('Set-Cookie'): raise ValueError('Cookie-bearing page is not a public export')
            expected_type = {'index.html':'text/html','style.css':'text/css','hero.jpg':'image/jpeg'}[name]
            if response.headers.get_content_type() != expected_type: raise ValueError('Unsupported export content type')
            body = response.read(8 * 1024 * 1024 + 1)
            if len(body) > 8 * 1024 * 1024: raise ValueError('Export object too large')
            bodies[name] = body
    html = bodies['index.html'].decode('utf-8')
    if '<body' not in html.lower() or '</body>' not in html.lower(): raise ValueError('Complete HTML body required')
    css = bodies['style.css'].decode('utf-8')
    if re.search(r'url\s*\(|@import|expression\s*\(|[<>\\]', css, re.I): raise ValueError('CSS external/active dependencies unsupported by this adapter')
    parser = StaticPage(message, contact, asset_prefix); parser.feed(html); parser.close()
    if parser.suppressed: raise ValueError('Unclosed active HTML element')
    releases = Path(releases); releases.mkdir(parents=True, exist_ok=True)
    ident = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    release = releases / ident; release.mkdir()
    try:
        (release/'index.html').write_text('<!doctype html>' + ''.join(parser.parts), encoding='utf-8')
        assets = release/'assets'; assets.mkdir()
        (assets/'style.css').write_text(css + '\n.fallback-notice,#fallback-contact{padding:1.25rem;border:2px solid #b46520;border-radius:1rem;margin:1rem auto;max-width:68rem;background:#fff4df;color:#342312}\n', encoding='utf-8')
        source = release/'source.jpg'; source.write_bytes(bodies['hero.jpg'])
        subprocess.run(['convert', '-limit', 'memory', '64MiB', '-limit', 'disk', '128MiB',
                        'jpeg:' + str(source.absolute()), '-auto-orient', '-strip', '-resize', '800x500>', '-quality', '78',
                        'webp:' + str((assets/'hero.webp').absolute())], check=True, capture_output=True, timeout=25)
        source.unlink()
        if (assets/'hero.webp').stat().st_size > 2 * 1024 * 1024: raise ValueError('Optimized image exceeds budget')
        manifest = {'schema_version': 1, 'release': ident, 'created_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'files': {p.relative_to(release).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(release.rglob('*')) if p.is_file()},
                    'image_source_bytes': len(bodies['hero.jpg']), 'image_result_bytes': (assets/'hero.webp').stat().st_size,
                    'scope': 'APPROVED_SINGLE_PUBLIC_PAGE_NO_DYNAMIC_ACTIONS', 'asset_prefix': asset_prefix}
        (release/'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        verify(release)
        return release, manifest
    except Exception:
        # Incomplete directories are deliberately not published; retain for diagnosis.
        raise


def verify(release):
    release = Path(release)
    manifest = json.loads((release/'manifest.json').read_text())
    expected = {'index.html', 'assets/style.css', 'assets/hero.webp'}
    if manifest.get('schema_version') != 1 or set(manifest.get('files', {})) != expected: raise ValueError('Unsupported snapshot manifest')
    found = set()
    for p in release.rglob('*'):
        if p.is_symlink(): raise ValueError('No snapshot symlinks')
        if p.is_file(): found.add(p.relative_to(release).as_posix())
    if found != expected | {'manifest.json'}: raise ValueError('Unexpected snapshot file')
    for name, digest in manifest['files'].items():
        if hashlib.sha256((release/name).read_bytes()).hexdigest() != digest: raise ValueError('Snapshot integrity mismatch')
    return manifest


def publish(release, current):
    release = Path(release).absolute(); verify(release)
    current = Path(current)
    if current.exists() and not current.is_symlink(): raise ValueError('Refuse replacing an ordinary current path')
    temp = current.with_name('.publish-' + uuid.uuid4().hex)
    temp.symlink_to(release, target_is_directory=True)
    temp.replace(current)
