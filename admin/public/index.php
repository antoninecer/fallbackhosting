<?php
declare(strict_types=1);
umask(0077);
ini_set('display_errors', '0');
require dirname(__DIR__) . '/lib.php';
header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: same-origin');
header("Content-Security-Policy: default-src 'none'; style-src 'self'; script-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'");
header('X-Frame-Options: DENY');
$error = '';
try {
    $origin = getenv('FH_ADMIN_ORIGIN') ?: '';
    $parsed = parse_url($origin);
    if (!is_array($parsed) || !isset($parsed['scheme'],$parsed['host']) || isset($parsed['user']) || isset($parsed['pass']) || isset($parsed['query']) || isset($parsed['fragment']) || ($parsed['path'] ?? '') !== '') {
        throw new RuntimeException('Origin unavailable.');
    }
    $host = $parsed['host'] . (isset($parsed['port']) ? ':' . $parsed['port'] : '');
    $local = getenv('FH_ADMIN_ALLOW_LOCAL_HTTP') === '1' && $parsed['scheme'] === 'http' && $parsed['host'] === '127.0.0.1' && ($_SERVER['REMOTE_ADDR'] ?? '') === '127.0.0.1';
    if (($parsed['scheme'] !== 'https' && !$local) || strtolower($_SERVER['HTTP_HOST'] ?? '') !== strtolower($host)) {
        http_response_code(400); exit('Neplatný veřejný vstup.');
    }
    if (!$local && ($_SERVER['HTTPS'] ?? '') !== 'on') { http_response_code(400); exit('Vyžadováno HTTPS.'); }
    $auth = read_json('auth');
    if (!is_string($auth['username'] ?? null) || !is_string($auth['password_hash'] ?? null)) { throw new RuntimeException('Admin unavailable.'); }
    $sessionPath = admin_dir() . '/sessions';
    if (!is_dir($sessionPath) || (fileperms($sessionPath) & 0077) !== 0) { throw new RuntimeException('Sessions unavailable.'); }
    session_save_path($sessionPath);
    ini_set('session.use_strict_mode','1');
    ini_set('session.use_only_cookies','1');
    session_name('FHADMINSESSID');
    session_set_cookie_params(['lifetime'=>0,'path'=>'/','secure'=>true,'httponly'=>true,'samesite'=>'Strict']);
    session_start();
    if (isset($_SESSION['last_seen']) && time() - $_SESSION['last_seen'] > 1800) { $_SESSION = []; session_regenerate_id(true); }
    $_SESSION['last_seen'] = time();
    $_SESSION['csrf'] ??= bin2hex(random_bytes(32));
    if (array_key_exists('center', $_GET) && !in_array($_SERVER['REQUEST_METHOD'], ['GET','HEAD'], true)) { http_response_code(405); header('Allow: GET, HEAD'); exit; }
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        if ((int)($_SERVER['CONTENT_LENGTH'] ?? 0) > 8192) { http_response_code(413); exit('Požadavek je příliš velký.'); }
        $action = field($_POST,'action',20);
        $originValid = ($_SERVER['HTTP_ORIGIN'] ?? '') === $origin;
        // Login uses exact Origin validation because browsers may omit the
        // pre-auth session cookie on a form POST. Authenticated actions still
        // require the session-bound synchronizer token below.
        $csrfValid = is_string($_POST['csrf'] ?? null) && hash_equals($_SESSION['csrf'], $_POST['csrf']);
        if (!$originValid || ($action !== 'login' && !$csrfValid)) {
            http_response_code(403); exit('Požadavek nemá platné ověření. Obnovte stránku.');
        }
        if ($action === 'login') {
            if (!login_allowed($_SERVER['REMOTE_ADDR'] ?? 'unknown')) { http_response_code(429); $error='Příliš mnoho pokusů. Zkuste to za deset minut.'; }
            else {
                $password = $_POST['password'] ?? null;
                $username = $_POST['username'] ?? null;
                if (is_string($password) && strlen($password) <= 256 && is_string($username) && password_verify($password,$auth['password_hash']) && hash_equals($auth['username'],$username)) {
                    login_allowed($_SERVER['REMOTE_ADDR'] ?? 'unknown',true);
                    session_regenerate_id(true);
                    $_SESSION['user']=$auth['username'];
                    $_SESSION['csrf']=bin2hex(random_bytes(32));
                    header('Location: /',true,303); exit;
                }
                http_response_code(401); $error='Přihlášení se nezdařilo.';
            }
        } else {
            if (!isset($_SESSION['user']) || !hash_equals($auth['username'],$_SESSION['user'])) { http_response_code(401); exit('Přihlaste se.'); }
            if ($action === 'logout') {
                $_SESSION=[]; session_destroy();
                setcookie(session_name(),'', ['expires'=>1,'path'=>'/','secure'=>true,'httponly'=>true,'samesite'=>'Strict']);
                header('Location: /',true,303); exit;
            }
            if (in_array($action,['install-plan','install-submit'],true)) {
                require dirname(__DIR__) . '/install.php';
                install_action($action, $_POST, read_json('inventory'));
            }
            if ($action==='standby-publication') {
                require dirname(__DIR__).'/publication.php';publication_action($_POST);
            }
            if ($action==='standby-control') {
                require dirname(__DIR__).'/standby.php';standby_action($_POST);
            }
            if ($action !== 'save-server') { throw new InputError('Neznámá operace.'); }
            $revision = field($_POST,'revision',10);
            if (!ctype_digit($revision)) { throw new InputError('Neplatná revize.'); }
            $mode = field($_POST,'mode',10);
            $input = $_POST; unset($input['action'],$input['csrf'],$input['revision'],$input['mode']);
            save_server($input,(int)$revision,$_SESSION['user'],$mode);
            $_SESSION['notice']='Konfigurace serveru uložena. Žádná vzdálená operace nebyla spuštěna.';
            header('Location: /',true,303); exit;
        }
    } elseif ($_SERVER['REQUEST_METHOD'] !== 'GET' && !(array_key_exists('center', $_GET) && $_SERVER['REQUEST_METHOD'] === 'HEAD')) { http_response_code(405); header('Allow: GET, POST'); exit; }
    $loggedIn = isset($_SESSION['user']) && hash_equals($auth['username'],$_SESSION['user']);
    if (array_key_exists('center', $_GET)) {
        require dirname(__DIR__) . '/center.php';
        serve_center($_GET['center'], $loggedIn, $local);
    }
    $inventory = $loggedIn ? read_json('inventory') : null;
} catch (InputError $failure) {
    http_response_code(422); $error=$failure->getMessage();
    $loggedIn = isset($_SESSION['user']); $inventory=$loggedIn ? read_json('inventory') : null;
} catch (RevisionConflict $failure) {
    http_response_code(409); $error=$failure->getMessage();
    $loggedIn=true; $inventory=read_json('inventory');
} catch (Throwable $failure) {
    http_response_code(503); exit('Administrace zatím není bezpečně připravena. Kontaktujte správce.');
}
$csrf = $_SESSION['csrf'];
if (array_key_exists('publication-preview',$_GET)) {
    if (!$loggedIn) { http_response_code(401);exit('Přihlaste se.'); }
    require_once dirname(__DIR__).'/publication.php';
    publication_preview($_GET['publication-preview'],$_GET['asset']??'index.html');
}
if (array_key_exists('standby',$_GET)) {
    if (!$loggedIn) { http_response_code(401);exit('Přihlaste se na hlavní stránce administrace.'); }
    require_once dirname(__DIR__).'/standby.php';serve_standby($csrf,$error);
}
if (array_key_exists('install', $_GET)) {
    if (!$loggedIn) { http_response_code(401); exit('Přihlaste se na hlavní stránce administrace.'); }
    require_once dirname(__DIR__) . '/install.php';
    serve_install($inventory,$csrf,$error);
}
$notice = $_SESSION['notice'] ?? ''; unset($_SESSION['notice']);
$edit = ['id'=>'','name'=>'','host'=>'','ssh_port'=>22,'ssh_user'=>'','runtime'=>'docker','platform'=>'unknown','credential_ref'=>'','host_fingerprint'=>'','description'=>'','enabled'=>true];
$editing = false;
if ($loggedIn && is_string($_GET['edit'] ?? null)) {
    foreach ($inventory['servers'] as $server) { if ($server['id'] === $_GET['edit']) { $edit=$server; $editing=true; } }
}
function observation(array $server, string $kind): string {
    $item=$server['observations'][$kind] ?? ['status'=>'UNKNOWN'];
    $label = match($item['status'] ?? 'UNKNOWN') { 'PASS'=>'Ověřeno', 'NEEDS_TEST'=>'Čeká na ověření', default=>'Neověřeno' };
    return $label . (isset($item['observed_at_utc']) ? ' · '.$item['observed_at_utc'] : '');
}
?>
<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FallbackHosting · Správa serverů</title><link rel="stylesheet" href="/admin.css"></head>
<body><header><a class="brand" href="/">F/ <span>FallbackHosting</span></a><span class="tag">Administrace</span><?php if ($loggedIn): ?><a href="/?install=1">Aplikace</a><a href="/?standby=1">Dostupnost a údržba</a><a href="/?center=index.html">Řídicí centrum</a><form method="post"><input type="hidden" name="csrf" value="<?=e($csrf)?>"><input type="hidden" name="action" value="logout"><button class="quiet">Odhlásit</button></form><?php endif; ?></header>
<main><?php if ($error !== ''): ?><p class="alert" role="alert"><?=e($error)?></p><?php endif; ?><?php if ($notice !== ''): ?><p class="notice" role="status"><?=e($notice)?></p><?php endif; ?>
<?php if (!$loggedIn): ?>
<section class="login panel"><p class="eyebrow">SPRÁVA PLATFORMY</p><h1>Přihlášení správce</h1><p class="muted">Konfigurace aplikačních serverů a jejich ověření.</p><form method="post"><input type="hidden" name="action" value="login"><input type="hidden" name="csrf" value="<?=e($csrf)?>"><label>Uživatelské jméno<input name="username" autocomplete="username" maxlength="40" required></label><label>Heslo<input type="password" name="password" autocomplete="current-password" maxlength="256" required></label><button>Přihlásit se</button></form></section>
<?php else: ?>
<section class="heading"><p class="eyebrow">INFRASTRUKTURA</p><h1>Jeden veřejný vstup.<br><span>Více aplikačních serverů.</span></h1><p class="muted">Přidejte protějšky, na kterých budou běžet aplikace. Konfigurace je dostupná pouze správci.</p></section>
<section class="gateway panel"><div><span class="tag">Veřejný VPS</span><h2><?=e($inventory['gateway']['name'])?></h2><p><?=e($inventory['gateway']['url'])?></p></div><div><strong><?=count($inventory['servers'])?> aplikačních serverů</strong><p class="muted">Záložní stránky a projektový přehled zůstávají nezávislé na domácích uzlech.</p></div></section>
<div class="section-title"><h2>Aplikační servery</h2><a class="button" href="/#server-form">+ Přidat server</a></div>
<section class="nodes" aria-label="Seznam serverů"><?php foreach ($inventory['servers'] as $server): ?>
<article class="panel node"><div class="row"><span class="tag"><?=e(strtoupper($server['runtime']))?> · <?=e(strtoupper($server['platform']))?></span><span class="muted"><?=$server['enabled'] ? 'Zařazený' : 'Pozastavený'?></span></div><h2><?=e($server['name'])?></h2><p class="address"><?=e($server['host'])?>:<?=e($server['ssh_port'])?></p><p class="muted">SSH účet <?=e($server['ssh_user'])?></p><dl><dt>SSH</dt><dd><?=e(observation($server,'ssh'))?></dd><dt>Docker</dt><dd><?=e(observation($server,'docker'))?></dd><dt>Identita serveru</dt><dd><?=e(observation($server,'fingerprint'))?></dd></dl><p class="muted"><?=e($server['description'])?></p><a href="/?edit=<?=rawurlencode($server['id'])?>#server-form">Upravit konfiguraci →</a></article>
<?php endforeach; ?></section>
<section class="panel" id="server-form"><p class="eyebrow">KONFIGURACE PROTĚJŠKU</p><h2><?=$editing ? 'Upravit server' : 'Přidat aplikační server'?></h2><p class="muted">Uložení pouze změní evidenci. Nepřipojuje se přes SSH, neinstaluje software a neovládá Docker. Podman a další typy jsou zatím jen konfigurační záznamy.</p>
<form method="post"><input type="hidden" name="action" value="save-server"><input type="hidden" name="mode" value="<?=$editing ? 'edit' : 'create'?>"><input type="hidden" name="csrf" value="<?=e($csrf)?>"><input type="hidden" name="revision" value="<?=e($inventory['revision'])?>"><div class="fields">
<label>ID serveru<input name="id" value="<?=e($edit['id'])?>" pattern="[a-z][a-z0-9-]{0,39}" maxlength="40" required <?=$editing ? 'readonly' : ''?>><small>Jedinečné ID, například home-2.</small></label><label>Název<input name="name" value="<?=e($edit['name'])?>" maxlength="80" required></label>
<label>IP adresa nebo hostname<input name="host" value="<?=e($edit['host'])?>" maxlength="253" required autocomplete="off"></label><label>SSH port<input type="number" name="ssh_port" value="<?=e($edit['ssh_port'])?>" min="1" max="65535" required></label>
<label>Technický SSH účet<input name="ssh_user" value="<?=e($edit['ssh_user'])?>" maxlength="32" required autocomplete="off"></label><label>Reference technické identity<input name="credential_ref" value="<?=e($edit['credential_ref'])?>" maxlength="64"><small>Pouze název identity pro budoucí technickou službu. Žádný klíč ani cesta.</small></label>
<label>Runtime<select name="runtime"><?php foreach (['docker'=>'Docker','podman'=>'Podman (budoucí podpora)','other'=>'Jiný (budoucí podpora)'] as $value=>$label): ?><option value="<?=e($value)?>" <?=$edit['runtime']===$value ? 'selected' : ''?>><?=e($label)?></option><?php endforeach; ?></select></label>
<label>Typ prostředí<select name="platform"><?php foreach (['lxc'=>'LXC','vm'=>'Virtuální stroj','physical'=>'Fyzický server','unknown'=>'Zatím neurčeno'] as $value=>$label): ?><option value="<?=e($value)?>" <?=$edit['platform']===$value ? 'selected' : ''?>><?=e($label)?></option><?php endforeach; ?></select></label>
<label class="wide">Očekávaný SSH fingerprint<input name="host_fingerprint" value="<?=e($edit['host_fingerprint'])?>" maxlength="60" placeholder="SHA256:…"><small>Samotné zadání fingerprintu nepotvrzuje nezávislé ověření. Změna připojení zneplatní dosavadní výsledky kontrol.</small></label>
<label class="wide">Poznámka<input name="description" value="<?=e($edit['description'])?>" maxlength="300"></label></div>
<label class="check"><input type="checkbox" name="enabled" value="1" <?=$edit['enabled'] ? 'checked' : ''?>>Zařadit server do konfigurace</label><button>Uložit konfiguraci</button><?php if ($editing): ?> <a class="cancel" href="/">Zrušit úpravu</a><?php endif; ?></form></section>
<p class="muted">Revize konfigurace <?=e($inventory['revision'])?> · změněno <?=e($inventory['updated_at_utc'])?> · výsledky kontrol jsou uložené záznamy, nikoli živý monitoring.</p>
<?php endif; ?></main><footer>FallbackHosting · <a href="https://project.lab.ventureout.cz/">Veřejný průběh projektu ↗</a></footer></body></html>
