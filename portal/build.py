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
STATUSES = {"DONE", "PLANNED", "NEEDS_TEST", "BLOCKED", "IN_PROGRESS", "READY", "BACKLOG", "TESTING", "BLOCKED_BY_OPERATOR"}
LABELS = {"BLOCKED_BY_OPERATOR": "Čeká na rozhodnutí operátora","DONE": "Hotovo", "PLANNED": "Plánováno", "NEEDS_TEST": "Čeká na ověření", "BLOCKED": "Čeká na podklady", "IN_PROGRESS": "Rozpracováno", "READY": "Připraveno", "BACKLOG": "Ve frontě", "TESTING": "Ověřování"}
MILESTONES = ["Základy projektu", "Audit infrastruktury", "Projektový přehled", "Nasazování aplikací", "Domény a HTTPS", "Statické záložní verze", "Standby a návrat do provozu", "Nouzový kontakt", "Testy odolnosti", "Návaznost práce agentů", "První vydání"]
TASKS = {
 "FH-0026": "Veřejná aktivace demo fallbacku a údržby",
 "FH-0025": "První úplný průchod statickou zálohou a přepínáním",
 "FH-0024": "Obnova řídicího centra ze vzdálených záloh",
 "FH-0023": "Průvodce instalací aplikací",
 "FH-0001": "Projektová dokumentace a obnova práce",
 "FH-0002": "Inventura infrastruktury",
 "FH-0003": "Ověření referenční aplikace",
 "FH-0004": "Nasazení Coolify na testovacím uzlu",
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
 "FH-0019": "Schválení nové verze administrace a přihlášení",
 "FH-0020": "Izolovaná služba Docker operací — místní verze",
 "FH-0021": "Místní správa aplikací a požadavků na operace",
 "FH-0022": "Řízené testy a úklid Dockeru na testovacím uzlu",
}

BLOCKERS = {
 "FH-0026": "Schválit přesný připravený rozsah: demo cesta na labu, dva nové pojmenované servisní soubory a vyhrazená úložiště, ověřená verze administrace a kontrolované reloady se zálohou a návratem. Ostatní vývoj pokračuje; DNS, VPN ani jiné weby se nemění.",
 "FH-0019": "Je potřeba schválit přepnutí nové prověřené verze aplikace na lab.ventureout.cz: oprava přihlášení a chráněné centrum, se zachováním inventáře. Bez změny Nginx, PHP-FPM nebo certifikátů.",
 "FH-0002": "Zbývá doložit zálohy a závislosti infrastruktury. OS, prostředky a Compose domácího uzlu už jsou ověřené.",
 "FH-0003": "Zbývá kontrola referenční aplikace z nezávislého vnějšího místa a bezpečný test dynamické funkce.",
 "FH-0011": "Pro automatické operace zbývá vymezení oprávnění a bezpečné nasazení služby. Identita SSH, připojení, Docker i prostředky uzlu už byly ověřeny.",
 "FH-0014": "Chybí nezávislé porovnání SSH fingerprintu s údajem z důvěryhodné konzole cílového serveru.",
}

PUBLIC_EVENTS = {
 "backup_discovery_restore_preview_pass": "Katalog přes SSH našel a ověřil tři skutečné zálohy statických stránek. Všechny tři byly stažené a znovu obnovené do oddělených adresářů. Funguje náhled vybrané obnovy bez přepisování živých dat; všech 116 testů prošlo. Obnova databází a celého řídicího centra zůstává samostatným úkolem.",
 "minimum_standby_activation_prepared": "Veřejné demo a ovládání jsou připravené, prověřené a zmrazené do verze. Čeká pouze konkrétní schválení zásahu do lab vhostu a dvou nových služeb podle pravidel projektu. Ostatní práce pokračuje rozpoznáváním vzdálených záloh; celé řešení na tuto otázku nečeká.",
 "minimum_standby_release_ready": "Všech 113 testů prošlo. Ovládání údržby i plánování v pražském čase je ověřené v prohlížeči; samostatná služba funguje pod neprivilegovaným účtem. Nová statická verze se publikuje až po vzdálené záloze a ověřené obnově. Připravena úzká aktivace pod /demo/; veřejné nasazení zatím neproběhlo.",
 "minimum_standby_control_local_pass": "Ovládání údržby v administraci už prošlo místním prohlížečem na mobilu, tabletu i desktopu: zapnutí/vypnutí, plánovaný interval v pražském čase, oznámení a zrušení intervalu. Ověřeny přístupové kontroly a oddělená technická služba. Veřejná aktivace této části ještě neproběhla.",
 "minimum_standby_actual_outage": "Skutečný výpadek demo kontejneru ověřen: web přešel na místní kopii, obrázky zůstaly dostupné a návrat čekal na tři úspěšné kontroly. Prohlížeč na mobilu, tabletu i desktopu prošel. Ověřena také údržba, časový interval, obnova ze vzdálené kopie a návrat verze. Přidáváme ovládání do administrace.",
 "minimum_standby_remote_backup": "Demo běží na vzdáleném uzlu. Statická kopie vznikla ze skutečného webu; obrázek zmenšen z přibližně 1 MB na 22 kB. Záložní archiv uložen vzdáleně, stažen zpět a úspěšně obnoven do odděleného adresáře. Následuje skutečná zkouška výpadku a návratu; veřejná cesta ještě není aktivní.",
 "minimum_standby_local_pass": "První skutečné testy prošly: Nginx přepnul při výpadku na místní kopii, obrázek i CSS zůstaly dostupné a údržba zablokovala odeslání formuláře. Ověřena optimalizace obrázku, záložní archiv a obnova. Připravujeme zkoušku se vzdáleným demo kontejnerem; veřejné přepínání zatím není nasazené.",
 "minimum_standby_started": "Začala realizace nejmenší funkční verze: jeden demo web, samostatná statická kopie s optimalizovaným obrázkem, přepínání v Nginxu, údržba a ověřená záloha. Obecná obnova a další velké funkce jsou odložené; dokončení potvrdí až skutečné testy.",
 "maintenance_windows_specified": "Do návrhu doplněna plánovaná údržba od–do: výběr dotčených webů, oznámení a vzhledově sladěná kontaktní verze místo objednávek. Návrat až po ověření zdraví; při zpoždění prodloužení nebo hlášení překročení termínu. Funkce je zatím plánovaná.",
 "availability_first_design": "Prioritou je dostupnost webů a jednotné ovládání přes FallbackHosting. Umístění Coolify je volitelné; další práce se zaměří na vytvoření statické kopie, náhled, údržbu a přepnutí při výpadku aplikace nebo VPN. Přesun služeb zatím není potřeba.",
 "public_controller_recovery_design": "Upřesněna cílová architektura: řídicí centrum na veřejném uzlu, aplikace a volitelné zálohy na vzdálených serverech. Připravíme rozpoznání záloh přes SSH a průvodce obnovou; žádný přesun služeb ani obnova zatím neproběhly. Statické záložní stránky zůstávají nezávislé.",
 "credentials_and_native_login_verified": "Opraven generátor hesel: standardně 16 náhodných znaků a povinně malé i velké písmeno, číslice a symbol. Nové přihlášení i odhlášení ověřené v administraci a Coolify. Skutečná instalace dokončena; všech 102 testů prošlo, původní služby jsou beze změny.",
 "install_wizard_success": "Skutečná instalace Coolify přes průvodce dokončena: tři služby jsou zdravé, správce založen a registrace vypnutá. Nové přihlášení do administrace ověřené; následuje kontrola přihlášení přímo do Coolify a sjednocení délky hesla.",
 "install_credentials_rejected": "Skutečný průchod instalačním formulářem odhalil chybějící symbol v požadovaném hesle. Přihlášení do administrace prošlo; instalace se nespustila a údaje se neuložily do fronty. Pro další pokus je potřeba zvolit heslo splňující pravidla formuláře.",
 "install_wizard_live": "V administraci je nový průvodce Aplikace: server, nápověda, účet a potvrzení instalace. Ověřen ve skutečném HTTPS prohlížeči; jednorázová zkouška čeká na údaje z formuláře. Samotná instalace zatím neproběhla.",
 "install_wizard_ready": "Průvodce a oddělený instalační postup prošly všemi 100 testy a předběžnou kontrolou testovacího serveru. Připravujeme aktivaci pro jeden potvrzený pokus z administrace.",
 "install_wizard_local_pass": "Průvodce instalací prošel místními testy i prohlížečem na mobilu, tabletu a desktopu. Oddělený vykonavatel přijímá jen ověřenou šablonu; skutečná instalace z formuláře ještě neproběhla.",
 "coolify_removed_for_wizard": "Původní tři služby Coolify odstraněny pro zkoušku instalace z administrace. Datová úložiště jsou zachovaná a původní aplikace beze změny; připravujeme průvodce s nápovědou.",
 "coolify_private_ready": "Coolify 4.4.6, databáze a Redis běží a jsou zdravé. Stránky, soubory i mobilní zobrazení ověřené; původní služba a veřejný gateway beze změny. Přístup je jen místní, registrace vypnutá. Pro první účet chybí soukromě sdělený e-mail správce; přihlášení ani nasazení aplikace ještě nejsou ověřené.",
 "coolify_ipv4_reconcile": "Databáze a Redis jsou zdravé. Kontrola Coolify odhalila nepodporované IPv6 v testovacím LXC; připravujeme opravu jen uvnitř nové aplikace. Hostitelská síť, veřejný gateway a existující služba se nemění.",
 "coolify_prepared": "Obrazy Coolify a databázových služeb jsou stažené a připnuté na přesné otisky. Nové datové úložiště a konfigurace jsou připravené; kontrola potvrdila jen místní porty a vypnuté automatické aktualizace. Následuje spuštění a kontrola zdraví.",
 "coolify_install_started": "Zahájeno schválené nasazení Coolify na testovacím Docker uzlu. Prostředky vyhovují; existující porty a kontejner zachováme. Rozhraní bude jen místní, veřejný proxy se nespouští. Probíhá příprava bezpečného prvního účtu.",
 "application_policy_tested": "Místní pravidla práv k aplikacím prošla osmi testy: cizí aplikace se odmítá, logy vyžadují zvláštní právo, zápisy silné přihlášení a odebrání práv zneplatní čekající požadavek při nové kontrole. Propojení s reálným přihlášením a brokerem ještě není aktivní.",
 "modular_providers_tested": "Schválen směr osobních účtů a práv k aplikacím. Připraven modulární návrh: Coolify/Docker pro aplikace, Proxmox nebo běžný Linux s libvirt/KVM pro VM a zálohy. Místní plánovač prošel testy; skutečné adaptéry ani změny infrastruktury zatím nejsou aktivní. Obecné schválení rolí a izolace už nečeká na operátora.",
 "access_security_proposed": "Připraven bezpečnostní návrh účtů a aplikací podle OWASP, Dockeru a Proxmoxu. Před nasazením potřebujeme rozhodnout: VM pro oddělené skupiny důvěry; passkeys a bezpečná obnova přístupu; správce pouze vlastní aplikace, mazání jen administrátor. Návrh není nasazený; místní vývoj pokračuje. Osobní údaje ani obnovovací kódy sem nevkládejte.",
 "dependency_audit_verified": "Kontrola závislostí dokončena v omezeném rozsahu: veřejný přehled a základ administrace používají místní soubory. Zahrnutí připojených dat Dockeru do zálohy zatím není doložené; obnova netestovaná, externí kopie nedoložená.",
 "center_release_verifier_tested": "Připravena místní kontrola nové verze administrace: přesná revize, otisky souborů a oprávnění. Čtyři testy prošly; nová verze zatím není nasazená a čeká na schválení.",
 "dependency_audit_started": "Probíhá kontrola závislostí: místní veřejný přehled a administrace, testovací Docker a rozsah zálohové evidence. Jen čtení, bez změn provozu; neověřené části zůstanou výslovně označené.",
 "renewal_proposal_pass": "Připraveno k posouzení: omezený návrh obnovy HTTPS a reload hooku prošel pěti testy, celkem všech 67 testů prošlo. Hook není nainstalovaný a žádný skutečný reload ani obnovu certifikátu jsme nespouštěli.",
 "renewal_plan_started": "Probíhá místní příprava obnovy HTTPS: omezený reload hook, kontrola konfigurace a referenčního webu. Testujeme náhradními příkazy, certifikáty, časovače ani běžící služby neměníme.",
 "agent_boundary_proposal": "Připraveno k posouzení: konkrétní plán oddělení agenta, webu a technické služby, včetně zachování obnovovacího přístupu a testů zamítnutí. Oprávnění zatím nejsou změněná; místní vývoj pokračuje.",
 "agent_boundary_started": "Probíhá návrh oddělení oprávnění: vývojový agent, webová administrace a technická služba mají mít jasně oddělený přístup. Zatím připravujeme postup a ověření, oprávnění na hostiteli neměníme.",
 "admin_ops_browser_pass": "Dokončeno místně: propojení PHP a brokeru i přehled dvou testovacích uzlů prošly. Prohlížeč ověřil mobil, tablet a desktop; požadavky, nejasné výsledky, chyby a audit jsou jasně odlišené od živého monitoringu.",
 "admin_ops_rpc_pass": "Ověřeno místně: PHP komunikuje s brokerem přes omezený Unix protokol. Testovací životní cyklus, výpisy, potvrzené odstranění, odmítnutí oprávnění a bezpečný přehled výsledků prošly; žádné změny živé administrace.",
 "admin_ops_started": "Probíhá místní propojení PHP administrace s odděleným brokerem: aplikace na uzlech, datované stavy, požadavky, výsledky a audit. Živé administrace ani služeb se tento krok netýká.",
 "docker_exercise_pass": "Dokončeno na testovacím uzlu: vytvoření, spuštění, kontrola, omezený log, restart, zastavení a přesný úklid vlastního kontejneru prošly. Původní aplikace zůstala beze změny; broker není aktivovaný.",
 "backup_attested": "Potvrzeno správcem: záloha aplikačního uzlu i test integrity jsou ověřené, měsíční zálohování nastavené. Obnova zatím nebyla testovaná a externí kopie není doložená.",
 "docker_log_policy_fix": "Příčina testu nalezena: nastavení omezeného kontejnerového logu nebylo platné pro použitý Docker. Upravujeme jen nový testovací kontejner; žádná změna démona, hostitele nebo původní aplikace.",
 "docker_isolation_verified": "Upřesnění testu: vlastnictví i všechna omezení izolace prošla. Selhalo až spuštění kontejneru; testovací prostředky byly odstraněny a původní aplikace zůstala beze změny. Ověřujeme příčinu běhového prostředí.",
 "docker_exercise_guard_stop": "Testovací kontejner byl vytvořen, ale kontrola izolace ho před spuštěním zastavila. Přesný úklid i zachování původní aplikace prošly; příčinu kontroly prověřujeme, životní cyklus zatím není dokončený.",
 "docker_exercise_started": "Probíhá povolený test na testovacím uzlu: jeden malý označený kontejner, kontrola životního cyklu a následný přesný úklid. Původní aplikaci porovnáváme před a po testu.",
 "docker_core_tests_pass": "Ověřeno místně: všech osm Docker operací prošlo testovacími daty; testy hlídají oprávnění, vlastnictví kontejnerů, potvrzení mazání, opakování požadavků a nejasný výsledek po timeoutu. Služba zatím není aktivovaná.",
 "ssh_identity_verified": "Dokončeno: identita testovacího uzlu nezávisle potvrzena správcem a porovnána s uloženou důvěrou klienta. Soukromá evidence je aktualizovaná; žádné síťové údaje ani fingerprint nezveřejňujeme.",
 "m01_refresh_pass": "Ověřeno: aktuální stav testovacího uzlu, vybrané služby a dostupnost chráněných webů. Nezávislý SSH fingerprint a úplné zálohové podklady stále chybí; pokračujeme místním Docker brokerem.",
 "center_auth_pass": "Dokončeno místně: centrum i všechny jeho soubory jsou chráněné relací; přihlášení, odhlášení a stažení prošly ve třech velikostech prohlížeče. Oprava nalezené chyby formuláře je připravená, živou verzi jsme zatím neměnili.",
 "center_auth_retest": "Kontrola místního přihlášení: testy přímých požadavků prošly, prohlížeč odhalil nesoulad při ověření formuláře. Příčinu ověřujeme v dočasném prostředí; živá administrace zůstává beze změny.",
 "center_auth_plan_started": "Probíhá: přesný návrh zabezpečeného nasazení centra přes existující přihlášení. Chráníme i soubory, styly a podklad ke stažení; provoz zatím neměníme.",
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
 "admin_login_cookie_fix_pass": "Oprava přihlášení ověřena přes HTTPS i bez předchozí session cookie; kontrola původu požadavku zůstává zapnutá. ctx1, odhlášení i nezměněný inventář potvrzeny.",
 "admin_node_note_reconciled": "Administrátor potvrdil přístup do správy. Opravena zavádějící poznámka; ověřený stav identity zůstal zachován.",
 "center_activation_started": "Řídicí centrum vracelo chybu při otevření. Ověřili jsme chybějící chráněný podklad; připravujeme bezpečné opravené vydání bez změn síťové konfigurace.",
 "center_release_candidate_tested": "Opravené vydání řídicího centra prošlo 88 testy a kontrolou integrity zdrojů a souborů; zatím je připravené pouze místně.",
 "center_release_ready": "Řídicí centrum je připravené k aktivaci jako nové neměnné vydání. Ověření přihlášení, návratu zpět a chráněných služeb proběhlo; změna zatím není aktivní.",
 "center_activation_pass": "Řídicí centrum je dostupné po přihlášení. Přístup bez relace i po odhlášení je zamítnutý; všechny chráněné soubory a kontrolní weby prošly.",
 "admin_center_docs_reconciled": "Dokumentace odpovídá skutečnému stavu: administrace a chráněné read-only centrum jsou nasazené, operace Docker zůstávají prototypem.",
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
        if task["status"] in {"BLOCKED", "BLOCKED_BY_OPERATOR"}:
            if task["id"] not in BLOCKERS:
                raise ValueError("Blocked task needs reviewed public explanation")
            result["blockers"].append({"id":task["id"], "title":task["title"], "reason":BLOCKERS[task["id"]], "status":task["status"]})
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
    blockers = "".join(f'<article class="panel"><span class="code">{e(item["id"])}</span><h3>{e(item["title"])}</h3>{badge(item["status"])}<p class="muted">{e(item["reason"])}</p></article>' for item in data["blockers"])
    counts = {s: sum(t["status"] == s for t in data["tasks"]) for s in STATUSES}
    done = sum(m["status"] == "DONE" for m in data["milestones"])
    return f'''<!doctype html>
<html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="FallbackHosting — ověřený průběh vývoje, milníky a další kroky."><title>FallbackHosting · Průběh projektu</title><link rel="stylesheet" href="/style.css"><script src="/app.js" defer></script></head>
<body><header class="top"><a class="brand" href="#"><span class="mark">F/</span> FallbackHosting</a><nav aria-label="Hlavní navigace"><a href="#stav">Stav</a><a href="#milniky">Milníky</a><a href="#ukoly">Úkoly</a></nav><span class="public">Veřejný přehled</span></header>
<main><section class="hero" id="stav"><p class="eyebrow">VÝVOJ PLATFORMY / PRŮBĚŽNÝ ZÁZNAM</p><h1>Projekt roste.<br><span>Každý krok má svůj záznam.</span></h1><p class="intro">FallbackHosting propojí nasazování aplikací se samostatnou záložní verzí webu. Tady najdete, co už vzniklo, co čeká na ověření a kam směřujeme dál.</p><div class="hero-bottom"><a class="button" href="#ukoly">Zobrazit průběh <span aria-hidden="true">↘</span></a><span class="phase">Aktuální etapa <strong>{e(data['milestone'])} · {e(MILESTONES[int(data['milestone'][1:])])}</strong></span></div></section>
<section class="stats" aria-label="Souhrn"><div><span>Dokončené milníky</span><strong>{done}<small> / {len(data['milestones'])}</small></strong></div><div><span>Hotové úkoly</span><strong>{counts['DONE']}</strong></div><div><span>Rozpracováno / ověřování</span><strong>{counts['IN_PROGRESS'] + counts['TESTING']}</strong></div><div><span>Čeká na podklady</span><strong>{counts['BLOCKED'] + counts['BLOCKED_BY_OPERATOR']}</strong></div></section>
<section class="overview"><article class="panel"><p class="eyebrow">CO UŽ MÁME</p><h2>Pevný základ pro další práci.</h2><ul class="checks"><li>Projektová dokumentace a pravidla bezpečných změn</li><li>Obnova práce z uložených checkpointů</li><li>Úvodní audit infrastruktury a návrh projektového centra</li><li>Veřejný přehled projektu na vlastní HTTPS adrese</li></ul><p class="muted">Oracle, SSH a vytvoření i úklid testovacího Docker kontejneru jsou ověřené. U domácího uzlu jsou ověřeny také OS, prostředky a Compose. Identita SSH je nezávisle ověřená. Záloha a integrita jsou potvrzené správcem. Zbývá externí aplikační kontrola, ověření obnovy a doplnění zálohových postupů. Automatické přepínání do záložního režimu zatím není zprovozněno.</p></article><article class="panel next"><p class="eyebrow">TEĎ A POTOM</p><h2>Rozvíjíme správu aplikací a záložní režim.</h2><p>Aktuální krok: {e(data['next_task'])}. Průběh jednotlivých úkolů najdete v přehledu níže.</p><p class="muted">Veřejná prezentace je pouze pro čtení. Základní administrace je nasazená; rozšířené centrum a ovládání aplikací ověřujeme místně.</p></article></section>
<section id="podklady"><h2>Na jaké podklady čekáme</h2><p class="muted">Tyto konkrétní úkoly čekají na důkaz. Ostatní práce může pokračovat.</p><div class="blocker-grid">{blockers or "<p>Žádný úkol právě nečeká na podklady.</p>"}</div></section>
<section id="posledni-kroky"><h2 id="progress-heading">Poslední dokončené kroky a výsledky</h2><p class="muted">Nejnovější záznamy jsou nahoře. Starší výsledky najdete posunutím uvnitř přehledu.</p><div class="progress-log" role="region" aria-labelledby="progress-heading" tabindex="0"><ol>{events}</ol></div></section>
<section id="milniky"><div class="section-head"><div><p class="eyebrow">CESTA K PRVNÍMU VYDÁNÍ</p><h2>Milníky projektu</h2></div><p class="muted">Hotovo znamená ověřeno a zaznamenáno.</p></div><ol class="roadmap">{milestones}</ol></section>
<section id="ukoly"><div class="section-head"><div><p class="eyebrow">KONKRÉTNÍ KROKY</p><h2>Pracovní přehled</h2></div><label class="filter">Zobrazit <select id="task-filter"><option value="ALL">Všechny úkoly</option><option value="DONE">Hotové</option><option value="ACTIVE">Rozpracované</option><option value="BLOCKED">Chybí podklady</option><option value="BLOCKED_BY_OPERATOR">Čeká na operátora</option><option value="READY">Připravené</option></select></label></div><div class="table-wrap"><table><thead><tr><th>ID</th><th>Úkol</th><th>Etapa</th><th>Stav</th></tr></thead><tbody>{tasks}</tbody></table></div><p id="filter-result" role="status" class="muted"></p></section>
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
