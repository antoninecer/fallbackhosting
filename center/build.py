#!/usr/bin/env python3
"""Build a local-only static control-center prototype; never publish it."""
import argparse
from datetime import datetime, timezone
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('public_portal', ROOT / 'portal/build.py')
portal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(portal)
model = portal.model
RUNBOOKS = [
    ('Obnova práce', 'Nejdříve ověřte Git, aktuální checkpoint a skutečný stav. Uložený stav není monitoring.', 'RUNBOOK.md'),
    ('Pravidla bezpečných změn', 'Repozitářové testy jsou oddělené od provozních zásahů. Zachovejte nezávislost veřejné brány.', 'AGENTS.md'),
    ('Projektová data', 'Katalog je jediný zdroj tabulek. Změny stavů potřebují důkazy; neplatný export zachová poslední platnou verzi.', 'docs/PROJECT-DATA.md'),
]


def snapshot(root=ROOT, now=None):
    now = now or datetime.now(timezone.utc)
    catalog = model.load(root)
    model.sync_markdown(root, catalog)
    state = json.loads((root / 'state/current.json').read_text())
    if state.get('catalog_path') != 'state/catalog.json':
        raise ValueError('Invalid catalog pointer')
    tasks = {t['id']:t for t in catalog['tasks']}
    if state['task_id'] not in tasks or state['phase'] != tasks[state['task_id']]['status']:
        raise ValueError('Current task/status differs from catalog')
    model.reference(root, state['last_checkpoint'])
    if not state['last_checkpoint'].startswith('checkpoints/'):
        raise ValueError('Invalid checkpoint pointer')
    # Intentionally select fields. Never serialize state or read private inventory.
    return dict(generated_utc=now.strftime('%Y-%m-%dT%H:%M:%SZ'), current_task=state['task_id'],
                checkpoint=state['last_checkpoint'], milestones=catalog['milestones'], tasks=catalog['tasks'],
                incidents=catalog['incidents'], observations=[dict(o,current_state=model.observation_state(o,now)) for o in catalog['observations']],
                agent=dict(catalog['agent'],current_state=model.agent_state(catalog['agent'],now)))


def resume_prompt(data):
    current = next(t for t in data['tasks'] if t['id']==data['current_task'])
    return f'''FallbackHosting — převzetí práce; uložený snímek {data['generated_utc']} (UTC).
Nejde o živý monitoring ani pokyn ke spuštění vzdálených operací.
Přečti AGENTS.md jako první, potom PROJECT.md, ARCHITECTURE.md, ROADMAP.md,
STATE.md, TASKS.md, SECURITY.md, RUNBOOK.md a checkpoint {data['checkpoint']}.
Ověř git status, poslední historii a skutečný stav před navázáním.
Aktuální úkol: {current['id']} — {current['title']}; stav {current['status']}.
Rozsah: {current['scope']}
Přijetí / další ověření: {current['acceptance']}
Závislosti: {', '.join(current['dependencies']) or 'Žádné zaznamenané.'}
Hotové úkoly: {', '.join(t['id'] for t in data['tasks'] if t['status']=='DONE') or 'Žádné.'}
Blokované úkoly: {', '.join(t['id'] for t in data['tasks'] if t['status']=='BLOCKED') or 'Žádné.'}
Hranice: nečti/neexportuj klíče ani soukromý inventář. Veřejná brána a nesouvisející
produkce musí zůstat nezávislé na domácím uzlu. Provozní zásahy vyžadují přesný
schválený rozsah a rollback; stav IN_PROGRESS není důkaz běžícího agenta.
Před významnou změnou ulož checkpoint, po ověření aktualizuj katalog, stav a veřejný průběh.
'''


def repo_link(path):
    return 'https://github.com/antoninecer/fallbackhosting/blob/main/' + path


def render(data, delivery="static"):
    e = html.escape
    def badge(value):
        labels = dict(portal.LABELS, UNKNOWN='Neznámé', STALE='Zastaralé', STOPPED='Relace ukončena', RECENT='Nedávný záznam', PASS='Ověřeno', FAIL='Selhalo')
        return f'<span class="badge state-{e(value.lower())}">{e(labels.get(value,value))}</span>'
    def refs(paths):
        return ''.join(f'<li><a href="{e(repo_link(p))}" rel="noreferrer">{e(p)}</a></li>' for p in paths) or '<li>Bez zaznamenaného důkazu.</li>'
    tasks = ''
    for task in data['tasks']:
        tasks += f'''<article class="task card" data-status="{e(task['status'])}"><p class="eyebrow">{e(task['id'])} · {e(task['milestone'])}</p><h3>{e(task['title'])}</h3>{badge(task['status'])}<p>{e(task['acceptance'])}</p><details><summary>Rozsah, závislosti a důkazy</summary><dl><dt>Vlastník</dt><dd>{e(task['owner'])}</dd><dt>Rozsah</dt><dd>{e(task['scope'])}</dd><dt>Závislosti</dt><dd>{e(', '.join(task['dependencies']) or 'Žádné zaznamenané')}</dd><dt>Rollback</dt><dd>{e(task['rollback'])}</dd><dt>Revize dokončení</dt><dd>{e(task['completion_revision'] or 'Úkol není dokončen')}</dd></dl><ul>{refs(task['evidence'])}</ul></details></article>'''
    milestones = ''.join(f'''<article class="card"><p class="eyebrow">{e(m['id'])}</p><h3>{e(m['title'])}</h3>{badge(m['status'])}<p>{e(m['acceptance'])}</p><details><summary>Důkazy</summary><ul>{refs(m['evidence'])}</ul></details></article>''' for m in data['milestones'])
    incidents = ''.join(f'''<article class="card"><h3>{e(i['id'])} · {e(i['component'])}</h3><p>{e(i['severity'])} · {e(i['status'])}</p><p>{e(i['symptoms'])}</p><p>Příčina ({e(i['cause_provenance'])}): {e(i['cause'])}</p><p>{e(i['resolution'])}</p><ul>{refs(i['evidence'])}</ul></article>''' for i in data['incidents']) or '<p class="empty">Žádné incidenty nejsou zaznamenané. To samo o sobě nepotvrzuje bezchybný provoz.</p>'
    observations = ''.join(f'''<article class="card"><h3>{e(o['component'])}</h3>{badge(o['current_state'])}<p>Provenience: {e(o['provenance'])}. Poslední výsledek: {e(o['status'])}.</p><p>{e(o['method'])}</p><dl><dt>Pozorováno (Praha)</dt><dd>{e(portal.prague_time(o['observed_at_utc'])) if o['observed_at_utc'] else 'Neznámé'}</dd><dt>Platnost do (Praha)</dt><dd>{e(portal.prague_time(o['expires_at_utc'])) if o['expires_at_utc'] else 'Není stanovena — aktuální zdraví je neznámé'}</dd><dt>Závislosti</dt><dd>{e(', '.join(o['dependencies']) or 'Žádné zaznamenané')}</dd></dl><ul>{refs(o['evidence'])}</ul></article>''' for o in data['observations']) or '<p class="empty">Žádná pozorování. Stav je neznámý.</p>'
    runbooks = ''.join(f'<article class="card"><h3>{e(title)}</h3><p>{e(summary)}</p><a href="{e(repo_link(path))}" rel="noreferrer">Zdroj v repozitáři ↗</a></article>' for title,summary,path in RUNBOOKS)
    agent = data['agent']
    current = next(t for t in data['tasks'] if t['id']==data['current_task'])
    document = f'''<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self'; script-src 'self'; base-uri 'none'; form-action 'none'"><title>FallbackHosting · Řídicí centrum — místní prototyp</title><link rel="stylesheet" href="center.css"><script src="center.js" defer></script></head><body><a class="skip" href="#main">Přejít na obsah</a><header><a class="brand" href="#prehled">F/ FallbackHosting</a><span class="prototype">Místní prototyp · pouze pro čtení</span><nav aria-label="Navigace centra"><a href="#prehled">Přehled</a><a href="#ukoly">Úkoly</a><a href="#milniky">Milníky</a><a href="#incidenty">Incidenty</a><a href="#zdravi">Kontroly</a><a href="#agent">Agent</a><a href="#postupy">Postupy</a><a href="#navazani">Převzetí práce</a></nav></header><main id="main"><section id="prehled"><p class="eyebrow">ŘÍDICÍ CENTRUM / ULOŽENÝ STAV</p><h1>Co je hotové.<br>Co ověřit dál.</h1><p class="intro">Tento prototyp není nasazený ani chráněný přihlašováním. Je určený pouze pro místní kontrolu; před zveřejněním musí být zabezpečený každý soubor.</p><div class="summary"><article class="card"><p>Aktuální úkol</p><h2>{e(current['id'])} · {e(current['title'])}</h2>{badge(current['status'])}<p>{e(current['acceptance'])}</p></article><article class="card"><p>Uložený snímek · Praha</p><h2>{e(portal.prague_time(data['generated_utc']))}</h2><p>Checkpoint: {e(data['checkpoint'])}</p><p>Záznam není živý monitoring.</p></article></div></section><section id="ukoly"><div class="section-head"><h2>Úkoly a důkazy</h2><label>Stav <select id="task-filter"><option value="ALL">Všechny</option><option value="ACTIVE">Rozpracované</option><option value="DONE">Hotové</option><option value="BLOCKED">Čekající</option><option value="READY">Připravené</option></select></label></div><p id="filter-result" role="status">Celkem úkolů: {len(data['tasks'])}.</p><div class="grid">{tasks}</div></section><section id="milniky"><h2>Milníky a přejímací podmínky</h2><div class="grid">{milestones}</div></section><section id="incidenty"><h2>Incidenty</h2><div class="grid">{incidents}</div></section><section id="zdravi"><h2>Kontroly a stáří výsledků</h2><p>Historický výsledek bez platnosti není současná dostupnost.</p><div class="grid">{observations}</div></section><section id="agent"><h2>Poslední záznam o agentovi</h2><article class="card">{badge(agent['current_state'])}<p>Identita: {e(agent['identity'])}. Úkol v záznamu: {e(agent['task_id'])}.</p><p>Heartbeat: {e(portal.prague_time(agent['heartbeat_utc'])) if agent['heartbeat_utc'] else 'Není zaznamenaný'}. Stav úkolu neprokazuje běžící proces.</p><p>Checkpoint záznamu: {e(agent['checkpoint'])}</p><p>Revize: {e(agent['revision'] or 'Neznámá')}</p></article></section><section id="postupy"><h2>Postupy</h2><p>Jen stručný přehled. Klíče, privátní inventář a surové logy sem nepatří.</p><div class="grid">{runbooks}</div></section><section id="navazani"><h2>Převzetí práce po přerušení</h2><label for="resume-prompt">Ověřitelný podklad pro další relaci</label><textarea id="resume-prompt" readonly rows="14">{e(resume_prompt(data))}</textarea><div class="actions"><button id="copy-resume" type="button">Kopírovat podklad</button><a class="button" href="resume.txt" download>Stáhnout TXT</a></div><p id="copy-result" role="status"></p></section></main><footer>Místní sestavení · bez vzdálených akcí · časy Europe/Prague</footer></body></html>'''

    if delivery == "admin-query":
        document = document.replace('<nav aria-label="Navigace centra">', '<nav aria-label="Navigace centra"><a href="/">Správa serverů</a>')
        for name in ("center.css", "center.js", "resume.txt"):
            document = document.replace('"' + name + '"', '"/?center=' + name + '"')
        document = document.replace('Řídicí centrum — místní prototyp', 'Řídicí centrum')
        document = document.replace('Místní prototyp · pouze pro čtení', 'Řídicí centrum · pouze pro čtení')
        document = document.replace('Tento prototyp není nasazený ani chráněný přihlašováním. Je určený pouze pro místní kontrolu; před zveřejněním musí být zabezpečený každý soubor.', 'Zobrazuje uložený stav projektu. Dostupnost a běžící práci je nutné ověřit zvlášť.')
    elif delivery != "static":
        raise ValueError("Unknown artifact delivery mode")
    return document


def build(output=None, root=ROOT, now=None, delivery="static"):
    root = Path(root).resolve()
    output = Path(output or root / '.local/control-center').resolve()
    if not output.is_relative_to(root / '.local'):
        raise ValueError('Control center output must remain inside repository .local; no public deployment')
    data = snapshot(root, now)
    files = {'index.html':render(data, delivery), 'resume.txt':resume_prompt(data)}
    for asset in ('center.css', 'center.js'):
        files[asset] = (ROOT / 'center' / asset).read_text()
    digest = hashlib.sha256(''.join(name + body for name,body in sorted(files.items())).encode()).hexdigest()
    (root / '.local').mkdir(mode=0o700,exist_ok=True)
    output.mkdir(parents=True,exist_ok=True)
    releases = output / 'releases'
    releases.mkdir(exist_ok=True)
    release = releases / digest
    if not release.exists():
        with tempfile.TemporaryDirectory(dir=releases) as temp:
            pending = Path(temp) / digest
            pending.mkdir()
            for name,body in files.items():
                (pending / name).write_text(body)
            manifest = {name:hashlib.sha256(body.encode()).hexdigest() for name,body in files.items()}
            (pending / 'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
            pending.rename(release)
    for name,body in files.items():
        if (release / name).read_text() != body:
            raise ValueError('Existing immutable release differs; retain current pointer')
    pointer = output / ('current-' + uuid4().hex + '.tmp')
    try:
        pointer.symlink_to(Path('releases') / digest)
        pointer.replace(output / 'current')
    finally:
        if pointer.is_symlink():
            pointer.unlink()
    return release


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--delivery',choices=('static','admin-query'),default='static')
    args = parser.parse_args()
    print('Built local-only center:',build(args.output,delivery=args.delivery))
