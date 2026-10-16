<?php
declare(strict_types=1);

const INSTALL_TEMPLATE = 'coolify-4.4.6';
const INSTALL_STATES = ['QUEUED'=>'Čeká na převzetí', 'VALIDATING'=>'Kontrola požadavku', 'DEPLOYING'=>'Spouštění tří služeb', 'BOOTSTRAPPING'=>'Zakládání účtu správce', 'VERIFYING'=>'Kontrola instalace', 'SUCCEEDED'=>'Instalace dokončena', 'FAILED'=>'Instalace se nezdařila', 'UNKNOWN'=>'Výsledek vyžaduje kontrolu'];

function install_node(array $inventory, string $id): array {
    foreach ($inventory['servers'] as $node) {
        if ($node['id'] === $id && $node['enabled'] && $node['runtime'] === 'docker'
            && ($node['observations']['fingerprint']['status'] ?? '') === 'PASS'
            && ($node['observations']['docker']['status'] ?? '') === 'PASS') { return $node; }
    }
    throw new InputError('Vyberte zařazený Docker server s ověřenou identitou a Dockerem.');
}

function install_worker_ready(string $node): bool {
    $path = admin_dir() . '/install-worker.json';
    if (!is_file($path) || is_link($path) || filesize($path) > 2048) { return false; }
    try { $info = json_decode(file_get_contents($path), true, 8, JSON_THROW_ON_ERROR); }
    catch (Throwable $e) { return false; }
    $when = strtotime($info['utc'] ?? '');
    return $when !== false && time() >= $when && time() - $when <= 45
        && ($info['node'] ?? '') === $node && ($info['template'] ?? '') === INSTALL_TEMPLATE
        && ($info['ready'] ?? false) === true;
}

function install_action(string $action, array $input, array $inventory): never {
    if ($action === 'install-plan') {
        if (array_diff(array_keys($input), ['action','csrf','node'])) { throw new InputError('Nepovolené pole průvodce.'); }
        $node = install_node($inventory, field($input, 'node', 40));
        $_SESSION['install_draft'] = ['node'=>$node['id'], 'revision'=>$inventory['revision'], 'token'=>bin2hex(random_bytes(32))];
        header('Location: /?install=review', true, 303); exit;
    }
    if ($action !== 'install-submit' || array_diff(array_keys($input), ['action','csrf','plan_token','email','password','password_confirmation','confirmation'])) {
        throw new InputError('Nepovolená operace průvodce.');
    }
    $draft = $_SESSION['install_draft'] ?? null;
    if (!is_array($draft) || !hash_equals($draft['token'], field($input,'plan_token',64))) { throw new InputError('Nejdříve vyberte server v prvním kroku.'); }
    $node = install_node($inventory, $draft['node']);
    if ($draft['revision'] !== $inventory['revision']) { throw new InputError('Konfigurace serverů se změnila. Vyberte server znovu.'); }
    $email = field($input,'email',254);
    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) { throw new InputError('Zadejte platný e-mail správce.'); }
    $password = $input['password'] ?? '';
    if (!is_string($password) || strlen($password)<12 || strlen($password)>128 || !preg_match('/^[\x21-\x7e]+$/D',$password)
        || !preg_match('/[a-z]/',$password) || !preg_match('/[A-Z]/',$password) || !preg_match('/[0-9]/',$password) || !preg_match('/[^a-zA-Z0-9]/',$password)) {
        throw new InputError('Heslo potřebuje 12–128 znaků bez mezer, malé a velké písmeno, číslici a symbol.');
    }
    if (!is_string($input['password_confirmation'] ?? null) || !hash_equals($password,$input['password_confirmation'])) { throw new InputError('Hesla se neshodují.'); }
    if (($input['confirmation'] ?? '') !== '1') { throw new InputError('Potvrďte rozsah instalace.'); }
    if (!install_worker_ready($node['id'])) { throw new InputError('Technická služba právě není připravená. Údaje nebyly odeslány; heslo neukládáme do rozepsaného formuláře.'); }
    $id = locked('install-queue', function () use ($node,$draft,$email,$password): string {
        $dir = admin_dir() . '/install-requests';
        if (!is_dir($dir) && !mkdir($dir,0700)) { throw new RuntimeException('Private queue unavailable.'); }
        foreach (glob($dir.'/*.status.json') ?: [] as $path) {
            $state=json_decode(file_get_contents($path),true);
            if (in_array($state['state'] ?? '', ['QUEUED','VALIDATING','DEPLOYING','BOOTSTRAPPING','VERIFYING','UNKNOWN'],true)) {
                throw new InputError('Jiná instalace už čeká nebo běží. Otevřete její výsledek níže.');
            }
        }
        if (count(glob($dir.'/*.request.json') ?: []) >= 20) { throw new InputError('Limit historie instalací byl dosažen.'); }
        $id=bin2hex(random_bytes(16)); $now=gmdate('Y-m-d\TH:i:s\Z');
        write_json('install-requests/'.$id.'.secret',['email'=>$email,'password'=>$password]);
        write_json('install-requests/'.$id.'.status',['id'=>$id,'state'=>'QUEUED','utc'=>$now]);
        write_json('install-requests/'.$id.'.request',['schema_version'=>1,'id'=>$id,'action'=>'install','node'=>$node['id'],'template'=>INSTALL_TEMPLATE,'inventory_revision'=>$draft['revision'],'actor'=>$_SESSION['user'],'created_utc'=>$now]);
        return $id;
    });
    unset($_SESSION['install_draft']);
    header('Location: /?install=job&id='.$id, true, 303); exit;
}

function serve_install(array $inventory, string $csrf, string $error): never {
    $view = is_string($_GET['install'] ?? null) ? $_GET['install'] : '1';
    $draft = $_SESSION['install_draft'] ?? null;
    $review = $view === 'review' && is_array($draft);
    $job=null;
    if ($view === 'job') {
        $id=$_GET['id'] ?? '';
        if (!is_string($id) || !preg_match('/^[a-f0-9]{32}$/D',$id)) { http_response_code(404); exit; }
        $path=admin_dir().'/install-requests/'.$id.'.status.json';
        if (!is_file($path) || is_link($path) || filesize($path)>4096) { http_response_code(404); exit; }
        $job=json_decode(file_get_contents($path),true);
        if (!is_array($job) || !isset(INSTALL_STATES[$job['state'] ?? ''])) { http_response_code(503); exit('Výsledek instalace není dostupný.'); }
    }
    $pending=$job && !in_array($job['state'],['SUCCEEDED','FAILED','UNKNOWN'],true);
    ?>
<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FallbackHosting · Průvodce instalací</title><link rel="stylesheet" href="/admin.css"><?php if ($pending): ?><meta http-equiv="refresh" content="5"><?php endif; ?></head>
<body><header><a class="brand" href="/">F/ <span>FallbackHosting</span></a><a href="/">Servery</a><a href="/?center=index.html">Řídicí centrum</a><form method="post" action="/"><input type="hidden" name="action" value="logout"><input type="hidden" name="csrf" value="<?=e($csrf)?>"><button class="quiet">Odhlásit</button></form></header>
<main><section class="heading"><p class="eyebrow">APLIKACE / PRŮVODCE</p><h1>Nainstalovat aplikaci</h1><p>Provedeme vás výběrem serveru, potřebnými službami a založením prvního účtu.</p></section>
<ol class="wizard-steps"><li>1. Server</li><li>2. Aplikace a nápověda</li><li>3. Účet a potvrzení</li></ol>
<?php if ($error !== ''): ?><p class="alert" role="alert"><?=e($error)?></p><?php endif; ?>
<?php if ($job): ?>
<section class="panel"><p class="eyebrow">COOLIFY 4.4.6</p><h2><?=e(INSTALL_STATES[$job['state']])?></h2><p>Poslední záznam: <?=e($job['utc'] ?? '')?> · UTC</p>
<?php if ($pending): ?><p>Průběh se obnovuje každých pět sekund. Stránku můžete znovu otevřít z přehledu aplikací.</p>
<?php elseif ($job['state']==='SUCCEEDED'): ?><p>Tři služby běží, účet správce je založený a automatická registrace zůstává vypnutá.</p><p>Coolify má samostatné přihlášení: použijte e-mail a heslo z tohoto průvodce. Přístup k rozhraní je zatím soukromý; veřejná adresa ještě není nastavená.</p>
<?php else: ?><p>Požadavek automaticky neopakujeme. Mohla vzniknout část instalace; nejdříve je potřeba ověřit skutečný stav. Heslo se zde nezobrazuje.</p><?php endif; ?><a class="button" href="/?install=1">Zpět na aplikace</a></section>
<?php elseif ($review): $node=install_node($inventory,$draft['node']); $ready=install_worker_ready($node['id']); ?>
<section class="panel"><p class="eyebrow">VÝBĚR APLIKACE</p><h2>Coolify · ověřená verze 4.4.6</h2><p>Server: <strong><?=e($node['name'])?></strong> · Docker</p><p>Coolify spravuje další aplikace. Šablona obsahuje Coolify, databázi PostgreSQL a Redis. Celkový nastavený limit je 2,25 GiB paměti a 1,75 CPU.</p><details open><summary>Co se při instalaci stane?</summary><ol><li>Zkontrolujeme server a nepřítomnost kolidujících kontejnerů.</li><li>Spustíme tři služby z ověřených obrazů.</li><li>Založíme správce podle údajů níže.</li><li>Ověříme zdraví služeb a vypnutou registraci.</li></ol><p>Datová úložiště z předchozí zkušební instalace jsou zachovaná a znovu se použijí. Jejich smazání tento průvodce neprovádí.</p></details><details><summary>Proč není k dispozici „latest“?</summary><p>Ověřená verze zajišťuje, že opakovaná instalace použije stejné obrazy. Aktualizace bude samostatný řízený krok.</p></details><details><summary>Jak se potom přihlásím?</summary><p>Coolify má vlastní účet. Zde zadaný e-mail je přihlašovací jméno; heslo si uložte do správce hesel. Odesílání obnovovacích e-mailů zatím není nastavené. Rozhraní je soukromé a jeho veřejná adresa se řeší zvlášť.</p></details></section>
<section class="panel"><h2>Účet prvního správce</h2><p>Vyplňte skutečný e-mail. Coolify může ověřit existenci jeho domény a bezpečnost hesla. Heslo se nezobrazuje v historii ani na projektovém přehledu.</p>
<?php if (!$ready): ?><p class="alert">Technická služba právě není připojená. Průvodce si ponechá výběr serveru; heslo zatím neodesílejte.</p><?php endif; ?>
<form method="post" action="/?install=review"><input type="hidden" name="action" value="install-submit"><input type="hidden" name="csrf" value="<?=e($csrf)?>"><input type="hidden" name="plan_token" value="<?=e($draft['token'])?>"><div class="fields"><label class="wide">E-mail správce<input type="email" name="email" autocomplete="username" maxlength="254" required></label><label>Heslo<input type="password" name="password" autocomplete="new-password" minlength="12" maxlength="128" required><small>Alespoň 12 znaků; malé a velké písmeno, číslice a symbol, bez mezer.</small></label><label>Heslo znovu<input type="password" name="password_confirmation" autocomplete="new-password" minlength="12" maxlength="128" required></label></div><label class="check"><input type="checkbox" name="confirmation" value="1" required>Chci nainstalovat Coolify na <?=e($node['name'])?> a založit správce.</label><button <?=$ready?'':'disabled'?>>Nainstalovat Coolify</button> <a href="/?install=1">Změnit server</a></form></section>
<?php else: ?>
<section class="panel"><h2>1. Kam aplikaci nainstalovat?</h2><p>Vyberte aplikační server. Veřejný vstup a záložní stránky běží nezávisle.</p><form method="post" action="/?install=1"><input type="hidden" name="action" value="install-plan"><input type="hidden" name="csrf" value="<?=e($csrf)?>"><label>Server<select name="node" required><option value="">Vyberte server</option><?php foreach ($inventory['servers'] as $node): if (!$node['enabled'] || $node['runtime']!=='docker') continue; ?><option value="<?=e($node['id'])?>"><?=e($node['name'])?> · Docker</option><?php endforeach; ?></select></label><button>Pokračovat na Coolify a nápovědu</button></form></section>
<?php endif; ?>
<section class="panel"><h2>Poslední instalace</h2><ul><?php $paths=glob(admin_dir().'/install-requests/*.status.json')?:[]; rsort($paths); foreach (array_slice($paths,0,20) as $path): if (is_link($path)||filesize($path)>4096) continue; $item=json_decode(file_get_contents($path),true); if (!isset(INSTALL_STATES[$item['state']??''])||!preg_match('/^[a-f0-9]{32}$/D',$item['id']??'')) continue; ?><li><a href="/?install=job&amp;id=<?=e($item['id'])?>">Coolify · <?=e(INSTALL_STATES[$item['state']])?></a> · <?=e($item['utc']??'')?></li><?php endforeach; ?><?php if (!$paths): ?><li>Zatím nebyla odeslána žádná instalace.</li><?php endif; ?></ul></section>
</main><footer>FallbackHosting · průvodce instalací</footer></body></html>
<?php exit;
}
