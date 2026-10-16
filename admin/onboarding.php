<?php
declare(strict_types=1);
require_once __DIR__.'/operations-client.php';

function onboarding_rpc(array $extra): array {
    $result=operations_call(admin_dir().'/onboarding.sock',array_merge(['actor'=>$_SESSION['user']],$extra));
    if (($result['ok']??false)!==true) { throw new InputError('Operace nebyla přijata. Obnovte její stav; při nejasném výsledku ji neopakujte.'); }
    return $result;
}

function onboarding_save(array $job): void {
    $draft=$_SESSION['onboarding_draft']??null;
    if (!is_array($draft)||$draft['input']['id']!==$job['id']||!in_array($job['phase'],['READY','SUCCEEDED'],true)) { throw new InputError('Nejdříve znovu ověřte server.'); }
    foreach (['host','ssh_user','ssh_port'] as $key) {
        if ((string)$draft['input'][$key] !== (string)$job['spec'][$key]) { throw new InputError('Cíl operace se změnil.'); }
    }
    if ($draft['input']['host_fingerprint']!==$job['spec']['fingerprint']) { throw new InputError('Identita serveru se změnila.'); }
    $revision=locked('inventory',function() use($draft,$job): int {
        $data=read_json('inventory');
        if ($data['revision']!==$draft['inventory_revision']) { throw new InputError('Evidence serverů se mezitím změnila. Ověřte výběr znovu.'); }
        $index=null;
        foreach($data['servers'] as $i=>$server) { if($server['id']===$job['id']){$index=$i;} }
        if ($index===null&&count($data['servers'])>=100) { throw new InputError('Limit počtu serverů.'); }
        $node=normalize_server($draft['input'],$index===null?null:$data['servers'][$index]);
        $node['observations']['ssh']=['status'=>'PASS','observed_at_utc'=>$job['utc']];
        $node['observations']['fingerprint']=['status'=>'PASS','observed_at_utc'=>$job['utc']];
        $node['observations']['docker']=['status'=>($job['facts']['docker_ready']??false)&&!empty($job['facts']['compose_version'])?'PASS':'UNKNOWN','observed_at_utc'=>$job['utc']];
        if($index===null){$data['servers'][]=$node;}else{$data['servers'][$index]=$node;}
        $data['revision']++;$data['updated_at_utc']=gmdate('Y-m-d\TH:i:s\Z');
        $data['audit']=array_slice(array_merge($data['audit'],[['utc'=>$data['updated_at_utc'],'actor'=>$_SESSION['user'],'action'=>'server.onboarding','server_id'=>$job['id'],'revision'=>$data['revision']]]),-100);
        write_json('inventory',$data);return $data['revision'];
    });
    $_SESSION['onboarding_draft']['inventory_revision']=$revision;
}

function onboarding_action(array $input,array $inventory): never {
    if(array_diff(array_keys($input),['action','csrf','id','name','host','ssh_port','ssh_user','host_fingerprint','revision','confirmation'])){throw new InputError('Nepovolené pole přidání serveru.');}
    $action=$input['action'];
    if($action==='onboard-check'){
        $proposal=['id'=>field($input,'id',40),'name'=>field($input,'name',80),'host'=>field($input,'host',253),'ssh_port'=>field($input,'ssh_port',5),'ssh_user'=>field($input,'ssh_user',32),'runtime'=>'docker','platform'=>'vm','credential_ref'=>'gateway-technical','host_fingerprint'=>field($input,'host_fingerprint',60),'description'=>'Přidáno a ověřeno průvodcem.','enabled'=>'1'];
        $old=null;foreach($inventory['servers'] as $n){if($n['id']===$proposal['id']){$old=$n;}}
        normalize_server($proposal,$old);
        if($old){$proposal['platform']=$old['platform'];$proposal['credential_ref']=$old['credential_ref'];$proposal['description']=$old['description'];}
        onboarding_rpc(['kind'=>'inspect_node','spec'=>['id'=>$proposal['id'],'host'=>$proposal['host'],'ssh_port'=>(int)$proposal['ssh_port'],'ssh_user'=>$proposal['ssh_user'],'fingerprint'=>$proposal['host_fingerprint']]]);
        $_SESSION['onboarding_draft']=['input'=>$proposal,'inventory_revision'=>$inventory['revision']];
        $id=$proposal['id'];
    }else{
        $id=field($input,'id',40);$job=onboarding_rpc(['kind'=>'view','node'=>$id])['job'];
        if(!is_array($job)){throw new InputError('Operace neexistuje.');}
        $revision=field($input,'revision',10);
        if(!ctype_digit($revision)||(int)$revision!==$job['revision']){throw new InputError('Stav operace se změnil. Obnovte stránku.');}
        if($action==='onboard-init'){
            if(($input['confirmation']??'')!=='1'){throw new InputError('Potvrďte inicializaci serveru.');}
            if($job['phase']!=='READY'||!($job['facts']['preparation_supported']??false)){throw new InputError('Server nelze automaticky připravit.');}
            onboarding_save($job);
            onboarding_rpc(['kind'=>'initialize_node','node'=>$id,'revision'=>(int)$revision,'confirmation'=>true]);
        }elseif($action==='onboard-finish'){
            onboarding_save($job);unset($_SESSION['onboarding_draft']);$_SESSION['notice']='Server je uložený podle skutečně ověřeného stavu.';header('Location: /',true,303);exit;
        }else{throw new InputError('Neznámá operace serveru.');}
    }
    header('Location: /?onboard=job&node='.rawurlencode($id),true,303);exit;
}

function onboarding_bootstrap(string $key): string {
    if(!preg_match('/^ssh-ed25519 [A-Za-z0-9+\/=]+(?: [^\r\n]*)?$/D',$key)){throw new RuntimeException('Public key unavailable.');}
    $quoted=escapeshellarg($key);
    return "# Spusťte jako root na novém serveru. Připravuje technický účet s právy správce.\nset -eu\nif ! command -v tailscale >/dev/null 2>&1; then\n  curl -fsSL https://tailscale.com/install.sh | sh\nfi\nsystemctl enable --now tailscaled\ntailscale up --accept-dns=false\nid fallback-agent >/dev/null 2>&1 || useradd --create-home --shell /bin/bash fallback-agent\nonboard_home=\$(getent passwd fallback-agent | cut -d: -f6)\nonboard_group=\$(id -gn fallback-agent)\ninstall -d -m 700 -o fallback-agent -g \"\$onboard_group\" \"\$onboard_home/.ssh\"\ngrep -qxF $quoted \"\$onboard_home/.ssh/authorized_keys\" 2>/dev/null || printf '%s\\n' $quoted >> \"\$onboard_home/.ssh/authorized_keys\"\nchown fallback-agent:\"\$onboard_group\" \"\$onboard_home/.ssh/authorized_keys\"\nchmod 600 \"\$onboard_home/.ssh/authorized_keys\"\ncommand -v restorecon >/dev/null 2>&1 && restorecon -RF \"\$onboard_home/.ssh\" || true\nonboard_sudo=\$(mktemp)\nprintf '%s\\n' 'fallback-agent ALL=(ALL) NOPASSWD: ALL' > \"\$onboard_sudo\"\nvisudo -cf \"\$onboard_sudo\"\nif [ -e /etc/sudoers.d/90-fallback-onboarding ]; then\n  cmp -s \"\$onboard_sudo\" /etc/sudoers.d/90-fallback-onboarding || { rm -f \"\$onboard_sudo\"; exit 1; }\nelse\n  install -o root -g root -m 440 \"\$onboard_sudo\" /etc/sudoers.d/90-fallback-onboarding\nfi\nrm -f \"\$onboard_sudo\"\ntailscale ip -4\nssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub -E sha256\n";
}

function serve_onboarding(array $inventory,string $csrf,string $error): never {
    $id=is_string($_GET['node']??null)?$_GET['node']:'new';$state=null;$key='';
    try{$result=onboarding_rpc(['kind'=>'view','node'=>$id]);$key=$result['public_key'];$state=$result['job'];}catch(Throwable $e){$error=$error?:'Služba přípravy serveru není dostupná. Žádná instalace nebyla spuštěna.';}
    $input=['id'=>'','name'=>'','host'=>'','ssh_port'=>22,'ssh_user'=>'fallback-agent','host_fingerprint'=>''];
    foreach($inventory['servers'] as $n){if($n['id']===$id){$input=$n;}}
    $pending=is_array($state)&&in_array($state['phase'],['CHECKING','INITIALIZING'],true);
    $labels=['CHECKING'=>'Ověřujeme připojení a systém','READY'=>'Připojení ověřeno','INITIALIZING'=>'Připravujeme server','SUCCEEDED'=>'Server je připravený','FAILED'=>'Připojení se nepodařilo ověřit','NEEDS_REVIEW'=>'Operace vyžaduje kontrolu'];
    $errors=['HOST_KEY_MISMATCH'=>'Otisk serveru nesouhlasí. Přihlášení nebylo provedeno.','HOST_KEY_UNAVAILABLE'=>'Server neposkytl SSH klíč. Zkontrolujte adresu, port a VPN.','SSH_OR_REMOTE_CHECK_FAILED'=>'SSH přihlášení nebo kontrola systému selhala. Zkontrolujte účet a veřejný klíč.','REMOTE_PREPARATION_REQUIRES_REVIEW'=>'Příprava se nedokončila. Výsledek je nutné zkontrolovat před opakováním.','INTERRUPTED_OPERATION'=>'Služba byla přerušena. Operaci automaticky neopakujeme.'];
    ?>
<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FallbackHosting · Přidat server</title><link rel="stylesheet" href="/admin.css"><?php if($pending):?><meta http-equiv="refresh" content="3"><?php endif;?></head><body><header><a class="brand" href="/">F/ FallbackHosting</a><a href="/">Servery</a><a href="/?install=1">Aplikace</a><a href="/?center=index.html">Řídicí centrum</a><form method="post" action="/"><input type="hidden" name="action" value="logout"><input type="hidden" name="csrf" value="<?=e($csrf)?>"><button class="quiet">Odhlásit</button></form></header><main><section class="heading"><p class="eyebrow">PŘIPOJENÍ A PŘÍPRAVA</p><h1>Přidat server</h1><p>Jednou připravíte přístup. Další ověření a inicializaci provede systém.</p></section>
<?php if($error!==''):?><p class="alert" role="alert"><?=e($error)?></p><?php endif;?>
<?php if($state&&($_GET['onboard']??'')==='job'):?>
<section class="panel"><h2><?=e($labels[$state['phase']]??'Stav vyžaduje kontrolu')?></h2><p>Server <?=e($state['id'])?> · záznam <?=e($state['utc'])?> UTC</p>
<?php if(isset($state['error'])):?><p class="alert"><?=e($errors[$state['error']]??'Operace nebyla dokončena; zkontrolujte přístup a zaznamenaný stav.')?></p><?php endif;?>
<?php if(isset($state['facts'])):$facts=$state['facts'];?><dl><dt>Přihlášený účet</dt><dd><?=e($facts['user'])?></dd><dt>Systém</dt><dd><?=e($facts['os'].' '.$facts['version'])?></dd><dt>Procesory</dt><dd><?=e($facts['cpus'])?></dd><dt>Paměť</dt><dd><?=e((string)round($facts['memory_kib']/1048576,1))?> GiB</dd><dt>Oprávnění k přípravě</dt><dd><?=$facts['sudo']?'Dostupné':'Chybí sudo bez hesla'?></dd><dt>Docker</dt><dd><?=$facts['docker_ready']?e($facts['docker_version']):'Zatím není připravený'?></dd><dt>Compose</dt><dd><?=e($facts['compose_version']?:'Zatím není připravený')?></dd></dl><?php endif;?>
<?php if($state['phase']==='READY'):?><h3>Chcete server inicializovat?</h3><p>Podporovanou instalaci doplníme o Docker Engine a Compose a zapneme jejich spuštění po startu serveru. Už připravený runtime pouze ověříme. Nemažeme aplikace ani data a neměníme ostatní servery.</p><p>Po přípravě bude server připravený pro nasazování aplikací. Instalace řídicího Coolify a aplikačních databází jsou samostatné kroky.</p>
<form method="post" action="/?onboard=job&amp;node=<?=rawurlencode($state['id'])?>"><input type="hidden" name="csrf" value="<?=e($csrf)?>"><input type="hidden" name="id" value="<?=e($state['id'])?>"><input type="hidden" name="revision" value="<?=e($state['revision'])?>"><label class="check"><input type="checkbox" name="confirmation" value="1" required>Chci automaticky připravit tento server.</label><button name="action" value="onboard-init" <?=($facts['preparation_supported']??false)?'':'disabled'?>>Inicializovat server</button></form>
<?php if(!($facts['preparation_supported']??false)):?><p>Automatická příprava podporuje čistý Rocky Linux 9 nebo už funkční Docker s Compose. Jiný systém teď uložíme bez inicializace.</p><?php endif;?>
<?php endif;?>
<?php if(in_array($state['phase'],['READY','SUCCEEDED'],true)):?><form method="post" action="/?onboard=job&amp;node=<?=rawurlencode($state['id'])?>"><input type="hidden" name="action" value="onboard-finish"><input type="hidden" name="csrf" value="<?=e($csrf)?>"><input type="hidden" name="id" value="<?=e($state['id'])?>"><input type="hidden" name="revision" value="<?=e($state['revision'])?>"><button><?=$state['phase']==='SUCCEEDED'?'Dokončit a uložit ověření':'Uložit pouze ověření připojení'?></button></form><?php endif;?>
<?php if($pending):?><p>Stav se obnovuje automaticky. Instalaci nemusíte spouštět znovu; stránku můžete později otevřít ze seznamu serverů.</p><?php endif;?><p><a href="/?onboard=1&amp;node=<?=rawurlencode($state['id'])?>">Zpět k údajům serveru</a></p></section>
<?php else:?>
<?php if($key!==''):?><section class="panel"><h2>1. Jednorázově připravit přístup</h2><p>Na vlastním serveru spusťte následující příkazy jako root. Připojí Tailscale, vloží náš veřejný klíč a připraví účet <strong>fallback-agent s oprávněními správce tohoto serveru</strong>. Přihlašovací odkaz Tailscale otevřete do stejné sítě jako ostatní uzly.</p><details><summary>Zobrazit příkazy pro přípravu serveru</summary><textarea class="onboarding-script" readonly rows="18" aria-label="Příkazy pro první připojení"><?=e(onboarding_bootstrap($key))?></textarea></details><p>Veřejný klíč:</p><textarea class="onboarding-script" readonly rows="3" aria-label="Veřejný SSH klíč"><?=e($key)?></textarea><p>Soukromý klíč ani heslo do formuláře nevkládejte. Poslední dva příkazy vypíší adresu ve VPN a otisk SSH serveru pro ověření níže.</p></section><?php endif;?>
<section class="panel"><h2>2. Ověřit server</h2><form method="post" action="/?onboard=1"><input type="hidden" name="action" value="onboard-check"><input type="hidden" name="csrf" value="<?=e($csrf)?>"><div class="fields"><?php foreach(['id'=>'ID serveru','name'=>'Název','host'=>'Tailscale IPv4 adresa','ssh_port'=>'SSH port','ssh_user'=>'Technický účet','host_fingerprint'=>'Otisk SSH serveru z konzole'] as $name=>$label):?><label><?=e($label)?><input name="<?=e($name)?>" value="<?=e($input[$name])?>" required maxlength="<?=$name==='host_fingerprint'?60:80?>"></label><?php endforeach;?></div><button <?=$key===''?'disabled':''?>>Ověřit připojení</button></form></section>
<?php endif;?></main><footer>FallbackHosting · přístup → ověření → potvrzená inicializace</footer></body></html><?php exit;
}
