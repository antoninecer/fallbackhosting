# Návrh přístupů a izolace aplikací

Stav: PROPOSED / FH-0015 TESTING, 15. 10. 2026. Doporučení podle primárních zdrojů, nikoliv potvrzení bezpečnosti současného provozu. Zadání: osobní aplikační účty bez SSH a bezpečné ovládání přidělených aplikací. Schválení návrhu neopravňuje k instalaci ani změně oprávnění.

## Doporučený model

Každý člověk má vlastní účet platformy; vazba uživatel → projekt → aplikace určuje práva. Jeden účet může obsluhovat více aplikací a jednu aplikaci více lidí. Žádné sdílené heslo, veřejná registrace nebo automatické členství. Přihlášení uvnitř hostované aplikace zůstává samostatné; případné SSO se řeší zvlášť a nesmí automaticky přidělovat správu infrastruktury.

| Operace | Pozorovatel aplikace | Správce aplikace | Administrátor platformy |
| --- | --- | --- | --- |
| Stav vlastní aplikace a výsledek operace | Ano | Ano | Ano |
| Omezené logy | Ne ve výchozím stavu; samostatné citlivé oprávnění | Jen explicitně přidělené | Jen pro provozní potřebu, auditovaně |
| Start, stop, restart | Ne | Ano po delegaci pro danou aplikaci | Ano |
| Nasazení schválené verze / rollback | Ne | Ano v povoleném katalogu a limitech | Ano |
| Nastavení a publikace standby | Ne | Ano pro vlastní aplikaci, po validaci exportu | Ano |
| Přidělení členství, změna serveru/domény/limitů | Ne | Ne | Ano |
| Odstranění aplikace | Ne | Ne | Opětovné ověření identity a potvrzení přesného cíle |
| Odstranění uložených dat | Ne | Ne | Samostatná nevratná operace, záloha a zvláštní potvrzení |
| Libovolný shell, Docker socket, privilegovaný kontejner | Ne | Ne | Mimo běžné webové rozhraní; oddělený provozní přístup |

Administrátor používá běžný omezený účet pro denní práci a zvláštní administrativní identitu/režim pro zvýšení oprávnění. Nouzový provozní přístup je oddělený a auditovaný. Žádný běžný člověk nepotřebuje systémový nebo SSH účet. Technické účty potřebuje pouze řídicí infrastruktura.

## Ověření identity a přístupů

Použít udržovanou knihovnu či poskytovatele identity; nevymýšlet vlastní autentizační protokol. Preferovat WebAuthn/passkeys s požadovaným ověřením uživatele, povinně pro privilegované účty; před delegovanými zápisy také silné ověření běžných správců. TOTP může být předem schválená slabší alternativa, nikoliv stejně odolná náhrada. Pro administrátora dvě nezávislé možnosti přístupu a offline obnovovací prostředek; obnova nesmí obejít bezpečnost přes samotný e-mail. Registraci dalšího autentizátoru chránit opětovným ověřením, auditovat a oznámit.

Session cookies Secure/HttpOnly/SameSite, rotace po přihlášení/zvýšení práv, omezená nečinnost i absolutní životnost, CSRF a přesný Origin u zápisů, omezení pokusů. Pro mazání a změny oprávnění vyžadovat čerstvé ověření a potvrzení konkrétní akce, nikoliv obecné „souhlasím se vším“.

Výchozí rozhodnutí je DENY. Backend kontroluje uživatele, členství, aplikaci, server, operaci a verzi politiky při každém čtení i zápisu, včetně logů, průběhu úloh, exportů a chyb. Skrytí tlačítka nic neautorizuje. Změna ID v požadavku nikdy nezpřístupní jiný projekt.

Odebrání práv nebo zablokování účtu zneplatní session a čekající autorizace. Broker před spuštěním znovu ověří aktuální členství/verzi politiky; krátká platnost tokenu sama o sobě okamžité odvolání nezaručuje. Při nedostupnosti autorizačního zdroje nové operace odmítne. Již odeslanou operaci nelze považovat za odvolanou: dokončení je nutno ověřit a auditovat, při nejistotě UNKNOWN bez automatického opakování.

## Technická hranice

Prohlížeč → autentizovaná administrace → oddělená důvěryhodná autorizace → broker → omezený vykonavatel na aplikačním uzlu. Privátní klíče a podepisovací materiál nejsou v PHP, webrootu ani agentově workspace. Broker přijímá jen strukturované povolené operace; nikdy příkazový řetězec, volný Compose, shell, uživatelskou cestu hostitele nebo libovolné Docker volby. Podpisy přes ověřenou knihovnu, oddělené identity a chráněné politiky; web nesmí sám vydávat oprávnění, která broker považuje za nezávisle schválená.

Registry vlastnictví + skutečné ID a štítky kontejneru musí souhlasit s projektem/aplikací/uzlem; klient si vlastnictví neurčuje. Přesný cíl a digest požadavku musí být v autorizaci. Žádný globální seznam kontejnerů/logů pro běžné účty. Idempotence, limity, timeout, audit bez tajemství a zákaz automatického opakování nejistých zápisů zůstávají povinné.

Současný prototyp vyžaduje zvláštní jednorázové schválení operátora pro KAŽDÝ zápis. Tato pravidla se tímto dokumentem nemění. Budoucí pohodlné delegované restarty/nasazení potřebují samostatně schválenou politiku a skutečný autorizační issuer. Kompromitovaný web nesmí získat neomezený Docker přístup.

## Izolace běhu a dat

Pro nejvyšší praktickou izolaci navrhuji samostatnou QEMU/KVM VM pro každou hranici důvěry; citlivá nebo nedůvěryhodná aplikace vlastní VM. Aplikace jedné důvěryhodné skupiny mohou sdílet VM pouze jako výslovně schválený kompromis. VM přidává oddělený kernel, ale neodstraňuje rizika hypervizoru, správce a sdíleného hardwaru. Aktuální LXC zůstává testovací prostředí. Přechod na VM je NÁVRH změny architektury, nikoliv provedená nebo schválená migrace. Instalace Coolify či změna jeho plánovaného umístění se tímto nepovoluje.

Uvnitř cílové VM vyhodnotit rootless Docker jako další ochranu; nejprve ověřit kompatibilitu síťování, limitů a zvoleného deployment nástroje. Rootless není náhrada autorizace ani samostatného kernelu. Každá aplikace má vlastní síť a datové svazky, vlastní databázový účet a tajemství; nepřipojovat cizí ani hostitelské adresáře. Výchozí síťová politika má omezit komunikaci mezi aplikacemi i přístup do správy a metadata služeb; konkrétní firewall/routing vyžaduje schválení.

Běh jako non-root, bez privileged/host namespaces/Docker socketu/zařízení, capabilities drop, no-new-privileges, zapnuté seccomp a dostupné LSM, read-only root filesystem s úzce přidělenými zapisovatelnými daty. Limity CPU/RAM/PID/disku a rotace logů. Kontrola se vztahuje i na image-declared volumes, sítě a build procesy. Žádný nedůvěryhodný build na sdíleném gateway; budoucí buildy v oddělených dočasných workerech bez produkčních tajemství.

Nasazovat pouze schválené image připnuté digestem, evidovat původ a kontrolu zranitelností a plán aktualizací; digest fixuje obsah, nezaručuje bezpečnost. Tajemství nepřidávat do image, Git, public snapshotu ani logů. Zálohy šifrované, s externí kopií a oddělenými přístupy; obnovu ověřovat v izolovaném prostředí včetně skutečných datových mountů.

Oracle gateway a veřejný přehled musí dál obsluhovat statické záložní verze bez závislosti na této správě, identity provideru, Dockeru a domácím uzlu.

## Co je ověřené a co zbývá

OBSERVED: lokální broker/PHP fixtures a jejich testy existují; nejsou nasazenou bezpečnostní hranicí. Neomezené sudo současného agenta a široký technický Docker přístup vylučují tvrzení o vynucené izolaci. MFA, víceuživatelské role, okamžité odvolání práv a VM izolace nejsou tímto návrhem implementovány ani otestovány. Aktuální existující admin není prezentován jako hotová víceuživatelská platforma.

Před zpřístupněním delegovaných operací musí projít negativní testy: cizí aplikace/ID/log/job/export, chybějící a odebrané členství během čekání, odvolaná session, zvýšení role, neplatný podpis, replay a změna payloadu, souběh vlastnictví, přístup webu/agenta ke klíčům a Docker socketu, nedovolené mounty/sítě, výpadek issueru/brokeru a zachování nezávislého gateway. Dále ověřit obnovu MFA/operátorského přístupu, záloh a auditní stopu. Testy v mocku necertifikují OS ani VM izolaci.

GO: pokračovat v dokumentaci, datovém modelu a lokálních negativních testech. NO-GO: skutečné delegované Docker zápisy, broker service, migrace VM, změny infrastruktury a aktivace nové admin verze bez splnění příslušných bran.

## Rozhodnutí pro operátora přes projekt

1. Izolace: schválit směr „VM na hranici důvěry, vlastní VM pro citlivou/nedůvěryhodnou aplikaci“; současné LXC ponechat pro demo. Před vytvořením potřebuji zvlášť schválit konkrétní cílový stroj, prostředky a rollback. Teď se žádná VM nevytváří.
2. Identita: před nasazením určit správce přístupů a bezpečnou obnovu, dostupnost passkeys a záložního autentizátoru. Konkrétní účty, recovery prostředky a kontakty patří výhradně do soukromého kanálu; nikdy do veřejného projectu.
3. Delegace: potvrdit uvedenou matici práv — správce pouze vlastní aplikace; mazání aplikace/dat vyhrazené administrátorovi; restart a schválené nasazení až po samostatném schválení politiky delegace.

Žádné z těchto rozhodnutí neblokuje místní vývoj. Přehled projektu zveřejňuje jen obecné požadavky, žádné identity, kontakty nebo interní topologii. Přesné aktivační kroky se připraví a předloží k samostatnému schválení; návrh neuděluje právo měnit provoz.

## Primární zdroje ověřené 15. 10. 2026

- [OWASP Authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html): minimální oprávnění, výchozí zákaz, kontrola každého požadavku.
- [OWASP MFA](https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html): phishing-resistant passkeys a bezpečný životní cyklus MFA.
- [OWASP Docker Security](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html): socket, privilege, limity, profily a data. Read-only mount socketu neznamená read-only Docker API.
- [Docker rootless](https://docs.docker.com/engine/security/rootless/): daemon i kontejnery bez hostitelského root uživatele, s omezeními kompatibility.
- [Docker Engine security](https://docs.docker.com/engine/security/): limity izolace kontejnerů a rizika daemonu.
- [Proxmox upstream container guide](https://github.com/proxmox/pve-docs/blob/master/pct.adoc): doporučení QEMU VM pro maximální izolaci aplikačních kontejnerů.

Konkrétní role, rozsah VM a proces schválení jsou náš návrh odvozený z těchto principů; zdroje nepotvrzují bezpečnost naší implementace.
