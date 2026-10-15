#!/usr/bin/env python3
"""Build a public, read-only view. Never export raw operational documents."""
import argparse
import html
import importlib.util
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
_model_spec = importlib.util.spec_from_file_location("project_model", ROOT / "portal/model.py")
model = importlib.util.module_from_spec(_model_spec)
_model_spec.loader.exec_module(model)
STATUSES = {"DONE", "PLANNED", "NEEDS_TEST", "BLOCKED", "IN_PROGRESS", "READY", "BACKLOG", "TESTING"}
LABELS = {"DONE": "Hotovo", "PLANNED": "Plánováno", "NEEDS_TEST": "Čeká na ověření", "BLOCKED": "Čeká na podklady", "IN_PROGRESS": "Rozpracováno", "READY": "Připraveno", "BACKLOG": "Ve frontě", "TESTING": "Ověřování"}
MILESTONES = ["Základy projektu", "Audit infrastruktury", "Projektový přehled", "Nasazování aplikací", "Domény a HTTPS", "Statické záložní verze", "Standby a návrat do provozu", "Nouzový kontakt", "Testy odolnosti", "Návaznost práce agentů", "První vydání"]
TASKS = {
 "FH-0001": "Projektová dokumentace a obnova práce",
 "FH-0002": "Inventura infrastruktury",
 "FH-0003": "Ověření referenční aplikace",
 "FH-0004": "Návrh nasazování aplikací",
 "FH-0005": "Návrh chráněného projektového centra",
 "FH-0006": "Validace a export projektových dat",
 "FH-0007": "Rozhraní projektového centra",
 "FH-0008": "Příprava bezpečného nasazení",
 "FH-0009": "Veřejná prezentace průběhu projektu",
 "FH-0010": "Úvodní stránka připravované platformy",
 "FH-0011": "Návrh připojení aplikačního serveru",
 "FH-0012": "Ověření obnovy HTTPS certifikátu",
 "FH-0013": "Návrh oddělené služby pro autorizované operace",
 "FH-0014": "Nezávislé ověření identity aplikačního serveru",
 "FH-0015": "Návrh oddělení oprávnění technického přístupu",
 "FH-0016": "Ověřený test vytvoření, spuštění a úklidu kontejneru",
 "FH-0017": "Administrace více aplikačních serverů",
 "FH-0018": "Kontrola a opakovatelné nasazení administrace",
}

BLOCKERS = {
 "FH-0002": "Zbývá doložit zálohy a závislosti infrastruktury. OS, prostředky a Compose domácího uzlu už jsou ověřené.",
 "FH-0003": "Zbývá kontrola referenční aplikace z nezávislého vnějšího místa a bezpečný test dynamické funkce.",
 "FH-0011": "Pro automatické operace zbývá nezávislé ověření SSH identity a vymezení oprávnění. Připojení, Docker i prostředky uzlu už byly ověřeny.",
 "FH-0014": "Chybí nezávislé porovnání SSH fingerprintu s údajem z důvěryhodné konzole cílového serveru.",
}

PUBLIC_EVENTS = {
 "center_browser_pass": "Dokončeno místně: centrum prošlo prohlížečem při šířkách 360, 768 a 1440 px. Ověřeny filtry, klávesnice, kopírování a stažení podkladu; všech 36 místních testů prošlo. Nasazení centra je samostatný krok.",
 "center_browser_retest": "Kontrola místního centra: přísná ochrana stránky zablokovala způsob čekání testovacího nástroje. Test upravujeme; ochranu stránky ponecháváme zapnutou.",
 "center_unit_pass": "Dokončeno místně: osm modulů centra a osm testů ochrany dat, vloženého HTML, obnovy práce a zachování poslední platné verze. Probíhá kontrola v prohlížeči; centrum zatím není nasazené.",
 "blockers_clarified": "Upřesněno: čekající úkoly nyní uvádějí konkrétní chybějící důkaz. Zastaralé čekání na souhlas s místním návrhem centra bylo odstraněno.",
 "center_ui_started": "Probíhá: místní rozhraní řídicího centra — úkoly, milníky, události, stáří kontrol a podklady pro pokračování práce. Veřejný web zůstává jen přehledem.",
 "browser_qa_wait": "Kontrola zobrazení: testovací prohlížeč potřebuje doplnit knihovny v dočasné složce. Stránka je dostupná, vizuální kontrola zatím není dokončená.",
 "progress_scroll_pass": "Dokončeno: historie výsledků má vlastní posuvné pole s omezenou výškou, nejnovější záznamy zůstávají nahoře.",
 "data_model_pass": "Dokončeno: 11 milníků a 18 úkolů má jednotný datový zdroj. Kontroly návazností, důkazů, soukromí a zastaralých údajů prošly; tabulky dokumentace se generují z katalogu.",
 "data_model_started": "Probíhá: sjednocení projektových dat, kontrola návazností a bezpečného exportu pro řídicí centrum.",
 "prague_time_pass": "Dokončeno: časy na projektové stránce se zobrazují podle Prahy včetně letního a zimního času.",
 "admin_recheck_pass": "Dokončeno: opakované skutečné HTTPS přihlášení a odhlášení administrátora i všech 14 místních testů prošlo. Vizuální kontrola v prohlížeči a zkouška rollbacku zbývají.",
 "admin_https_failed": "HTTPS certifikát je aktivní; kontrola aplikace odhalila nepřístupný nový adresář. Oprava přístupového režimu probíhá, okolní weby prošly kontrolou.",
 "admin_canary_wait": "Kontrola před pokračováním: certifikát vydán, vedlejší API vrátilo HTTP 429. Čekáme na opakovanou kontrolu; chráněná referenční stránka je dostupná.",
 "home_inventory_pass": "Dokončeno: ověření OS, prostředků, Dockeru a Compose domácího uzlu.",
 "git_push_pass": "Dokončeno: projektové změny a postup nasazení odeslány do Gitu.",
 "admin_prepare_pass": "Dokončeno: ověřená záloha, oddělený účet a PHP prostředí administrace; produkční kontroly prošly.",
 "admin_http_failed": "Aktivace HTTP pozastavena: kontrola přístupu k nové ACME složce selhala před načtením konfigurace. Probíhá oprava.",
 "admin_http_pass": "Dokončeno: HTTP ověření domény a ACME challenge; produkční kontroly prošly.",
 "admin_certificate_pass": "Dokončeno: samostatný HTTPS certifikát pro lab.ventureout.cz vydán.",
 "admin_https_pass": "Dokončeno: administrace na lab.ventureout.cz má platné HTTPS; přihlášení, vzhledové soubory a ochrana neveřejných cest ověřeny.",
 "admin_login_pass": "Dokončeno: skutečné přihlášení administrátora, zobrazení ctx1 a odhlášení ověřeny.",
}

def rows(path, pattern):
    result = []
    for line in path.read_text().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and re.fullmatch(pattern, cells[0]):
            result.append(cells)
    return result

def public_data(root=ROOT):
    catalog = model.load(root)
    model.sync_markdown(root, catalog)
    state = json.loads((root / "state/current.json").read_text())
    if state.get("catalog_path") != "state/catalog.json":
        raise ValueError("Invalid canonical catalog reference")
    milestone = state["milestone"]
    if not re.fullmatch(r"M(?:0[0-9]|10)", milestone):
        raise ValueError("Invalid current milestone")
    ms = [[m["id"], m["title"], m["status"], m["acceptance"]] for m in catalog["milestones"]]
    tasks = [[t["id"], t["milestone"], t["status"], t["owner"], t["acceptance"]] for t in catalog["tasks"]]
    if [r[0] for r in ms] != [f"M{i:02}" for i in range(11)]:
        raise ValueError("Expected unique ordered M00–M10")
    result = {"milestone": milestone, "milestones": [], "tasks": []}
    for r in ms:
        if r[2] not in STATUSES:
            raise ValueError("Unknown milestone status")
        result["milestones"].append({"id": r[0], "title": MILESTONES[int(r[0][1:])], "status": r[2]})
    ids = set()
    for r in tasks:
        if len(r) != 5 or r[0] in ids or r[1] not in {m["id"] for m in result["milestones"]} or r[2] not in STATUSES:
            raise ValueError("Invalid task/reference/status")
        ids.add(r[0])
        # Unknown tasks require explicit public title review. Never copy owner/acceptance text.
        if r[0] not in TASKS:
            raise ValueError("Task needs reviewed public title: " + r[0])
        result["tasks"].append({"id": r[0], "milestone": r[1], "title": TASKS[r[0]], "status": r[2]})
    if state["task_id"] not in ids:
        raise ValueError("Current task missing")
    result["next_task"] = TASKS[state["task_id"]]
    result["blockers"] = []
    for task in result["tasks"]:
        if task["status"] == "BLOCKED":
            if task["id"] not in BLOCKERS:
                raise ValueError("Blocked task needs reviewed public explanation")
            result["blockers"].append({"id":task["id"], "title":task["title"], "reason":BLOCKERS[task["id"]]})
    checkpoint = state["last_checkpoint"]
    if not re.fullmatch(r"checkpoints/\d{8}T\d{6}Z-[A-Za-z0-9-]+\.md", checkpoint) or not (root / checkpoint).is_file():
        raise ValueError("Invalid checkpoint reference")
    result["checkpoint"] = Path(checkpoint).stem
    result["checkpoint_utc"] = datetime.strptime(Path(checkpoint).name[:16], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).isoformat()
    result["events"] = []
    for event in state.get("public_events", []):
        if set(event) != {"id", "utc"} or event["id"] not in PUBLIC_EVENTS:
            raise ValueError("Unknown public event")
        datetime.strptime(event["utc"], "%Y-%m-%dT%H:%M:%SZ")
        result["events"].append({"title": PUBLIC_EVENTS[event["id"]], "utc": event["utc"]})
    result["generated_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return result

def badge(status, label=None):
    return f'<span class="badge {status.lower()}">{html.escape(label or LABELS[status])}</span>'

def prague_time(value):
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        raise ValueError("Timestamp must include a timezone")
    local = moment.astimezone(ZoneInfo("Europe/Prague"))
    return local.strftime("%d. %m. %Y %H:%M:%S") + " · Praha (" + local.tzname() + ")"

def render(data):
    e = html.escape
    milestones = "".join(f'<li class="milestone"><span class="code">{m["id"]}</span><div><h3>{e(m["title"])}</h3>{badge(m["status"], "Částečně ověřeno" if m["id"] == "M01" and m["status"] == "NEEDS_TEST" else None)}</div></li>' for m in data["milestones"])
    tasks = "".join(f'<tr data-status="{t["status"]}"><td><span class="code">{t["id"]}</span></td><td>{e(t["title"])}</td><td>{t["milestone"]}</td><td>{badge(t["status"])}</td></tr>' for t in data["tasks"])
    events = "".join(f'<li><time datetime="{e(event["utc"])}">{e(prague_time(event["utc"]))}</time><p>{e(event["title"])}</p></li>' for event in reversed(data["events"]))
    blockers = "".join(f'<article class="panel"><span class="code">{e(item["id"])}</span><h3>{e(item["title"])}</h3><p class="muted">{e(item["reason"])}</p></article>' for item in data["blockers"])
    counts = {s: sum(t["status"] == s for t in data["tasks"]) for s in STATUSES}
    done = sum(m["status"] == "DONE" for m in data["milestones"])
    return f'''<!doctype html>
<html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="FallbackHosting — ověřený průběh vývoje, milníky a další kroky."><title>FallbackHosting · Průběh projektu</title><link rel="stylesheet" href="/style.css"><script src="/app.js" defer></script></head>
<body><header class="top"><a class="brand" href="#"><span class="mark">F/</span> FallbackHosting</a><nav aria-label="Hlavní navigace"><a href="#stav">Stav</a><a href="#milniky">Milníky</a><a href="#ukoly">Úkoly</a></nav><span class="public">Veřejný přehled</span></header>
<main><section class="hero" id="stav"><p class="eyebrow">VÝVOJ PLATFORMY / PRŮBĚŽNÝ ZÁZNAM</p><h1>Projekt roste.<br><span>Každý krok má svůj záznam.</span></h1><p class="intro">FallbackHosting propojí nasazování aplikací se samostatnou záložní verzí webu. Tady najdete, co už vzniklo, co čeká na ověření a kam směřujeme dál.</p><div class="hero-bottom"><a class="button" href="#ukoly">Zobrazit průběh <span aria-hidden="true">↘</span></a><span class="phase">Aktuální etapa <strong>{e(data['milestone'])} · {e(MILESTONES[int(data['milestone'][1:])])}</strong></span></div></section>
<section class="stats" aria-label="Souhrn"><div><span>Dokončené milníky</span><strong>{done}<small> / {len(data['milestones'])}</small></strong></div><div><span>Hotové úkoly</span><strong>{counts['DONE']}</strong></div><div><span>Rozpracováno / ověřování</span><strong>{counts['IN_PROGRESS'] + counts['TESTING']}</strong></div><div><span>Čeká na podklady</span><strong>{counts['BLOCKED']}</strong></div></section>
<section class="overview"><article class="panel"><p class="eyebrow">CO UŽ MÁME</p><h2>Pevný základ pro další práci.</h2><ul class="checks"><li>Projektová dokumentace a pravidla bezpečných změn</li><li>Obnova práce z uložených checkpointů</li><li>Úvodní audit infrastruktury a návrh projektového centra</li><li>Veřejný přehled projektu na vlastní HTTPS adrese</li></ul><p class="muted">Oracle, SSH a vytvoření i úklid testovacího Docker kontejneru jsou ověřené. U domácího uzlu jsou ověřeny také OS, prostředky a Compose. Zbývá nezávislá kontrola SSH identity, externí aplikační kontrola a doplnění zálohových postupů. Automatické přepínání do záložního režimu zatím není zprovozněno.</p></article><article class="panel next"><p class="eyebrow">TEĎ A POTOM</p><h2>Připravujeme vstup do platformy a připojení serveru.</h2><p>Aktuální krok: {e(data['next_task'])}. Průběh jednotlivých úkolů najdete v přehledu níže.</p><p class="muted">Veřejná prezentace je pouze pro čtení. Chráněné řídicí centrum je další součástí plánu.</p></article></section>
<section id="podklady"><h2>Na jaké podklady čekáme</h2><p class="muted">Tyto konkrétní úkoly čekají na důkaz. Ostatní práce může pokračovat.</p><div class="blocker-grid">{blockers or "<p>Žádný úkol právě nečeká na podklady.</p>"}</div></section>
<section id="posledni-kroky"><h2 id="progress-heading">Poslední dokončené kroky a výsledky</h2><p class="muted">Nejnovější záznamy jsou nahoře. Starší výsledky najdete posunutím uvnitř přehledu.</p><div class="progress-log" role="region" aria-labelledby="progress-heading" tabindex="0"><ol>{events}</ol></div></section>
<section id="milniky"><div class="section-head"><div><p class="eyebrow">CESTA K PRVNÍMU VYDÁNÍ</p><h2>Milníky projektu</h2></div><p class="muted">Hotovo znamená ověřeno a zaznamenáno.</p></div><ol class="roadmap">{milestones}</ol></section>
<section id="ukoly"><div class="section-head"><div><p class="eyebrow">KONKRÉTNÍ KROKY</p><h2>Pracovní přehled</h2></div><label class="filter">Zobrazit <select id="task-filter"><option value="ALL">Všechny úkoly</option><option value="DONE">Hotové</option><option value="ACTIVE">Rozpracované</option><option value="BLOCKED">Čekající</option><option value="READY">Připravené</option></select></label></div><div class="table-wrap"><table><thead><tr><th>ID</th><th>Úkol</th><th>Etapa</th><th>Stav</th></tr></thead><tbody>{tasks}</tbody></table></div><p id="filter-result" role="status" class="muted"></p></section>
<section class="record"><div><p class="eyebrow">POSLEDNÍ ULOŽENÝ ZÁZNAM</p><h2>Stav s časem a kontextem.</h2><p class="muted">Tato stránka zobrazuje uložený stav projektu. Není to živý monitoring ani potvrzení, že agent právě pracuje.</p></div><dl><dt>Checkpoint</dt><dd class="checkpoint">{e(data['checkpoint'])}</dd><dt>Čas checkpointu (Praha)</dt><dd><time datetime="{e(data['checkpoint_utc'])}">{e(prague_time(data['checkpoint_utc']))}</time></dd><dt>Vygenerování stránky (Praha)</dt><dd><time datetime="{e(data['generated_utc'])}">{e(prague_time(data['generated_utc']))}</time></dd></dl></section>
</main><footer><span>F/ FallbackHosting</span><span>Ověřit. Zaznamenat. Pokračovat.</span><a href="https://github.com/antoninecer/fallbackhosting" rel="noopener noreferrer">Veřejný repozitář ↗</a></footer></body></html>'''

def build(output, root=ROOT):
    data = public_data(root)
    document = render(data)
    output.mkdir(parents=True, exist_ok=True)
    for asset in ("style.css", "app.js"):
        shutil.copyfile(ROOT / "portal" / asset, output / asset)
    # Generate fully before replacing the page; no raw source files are copied.
    pending = output / "index.html.tmp"
    pending.write_text(document)
    pending.replace(output / "index.html")

def build_lab(output):
    """Separate, deliberately static platform entry page; no admin functionality."""
    output.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "portal/style.css", output / "style.css")
    pending = output / "index.html.tmp"
    pending.write_text((ROOT / "portal/lab.html").read_text())
    pending.replace(output / "index.html")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "public")
    parser.add_argument("--lab-output", type=Path, default=ROOT / "lab-public")
    args = parser.parse_args()
    build(args.output)
    build_lab(args.lab_output)
    print("Built public presentation:", args.output)
