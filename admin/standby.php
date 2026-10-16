<?php
declare(strict_types=1);
require_once __DIR__.'/operations-client.php';
require_once __DIR__.'/publication.php';

function standby_rpc(array $extra=[]): array {
    $request=array_merge(['kind'=>'view','actor'=>$_SESSION['user'],'app'=>'demo'],$extra);
    $result=operations_call(admin_dir().'/standby.sock',$request);
    if (isset($result['error']) || ($result['ok']??false)!==true) { throw new InputError('Požadavek nebyl proveden. Obnovte stav; služba mohla odmítnout zastaralou revizi.'); }
    return $result;
}

function standby_prague_utc(string $value): string {
    if (!preg_match('/^\d{4}-\d\d-\d\dT\d\d:\d\d$/D',$value)) { throw new InputError('Vyplňte datum a čas.'); }
    $zone=new DateTimeZone('Europe/Prague');
    $parsed=DateTimeImmutable::createFromFormat('!Y-m-d\TH:i',$value,$zone);
    if ($parsed===false || $parsed->format('Y-m-d\TH:i')!==$value) { throw new InputError('Tento místní čas neexistuje. Zvolte jiný čas.'); }
    // Reject the repeated autumn hour rather than silently selecting an occurrence.
    $utcGuess=DateTimeImmutable::createFromFormat('!Y-m-d\TH:i',$value,new DateTimeZone('UTC'));
    $matches=[];
    foreach ($zone->getTransitions($parsed->getTimestamp()-172800,$parsed->getTimestamp()+172800) as $transition) {
        $candidate=$utcGuess->getTimestamp()-$transition['offset'];
        if ((new DateTimeImmutable('@'.$candidate))->setTimezone($zone)->format('Y-m-d\TH:i')===$value) { $matches[$candidate]=true; }
    }
    if (count($matches)!==1) { throw new InputError('Tento čas se při změně času opakuje. Zvolte čas mimo opakovanou hodinu.'); }
    return $parsed->setTimezone(new DateTimeZone('UTC'))->format('Y-m-d\TH:i:s\Z');
}

function standby_action(array $input): never {
    if (array_diff(array_keys($input),['action','csrf','revision','mode','start','end'])) { throw new InputError('Nepovolené pole údržby.'); }
    $revision=field($input,'revision',10);if (!ctype_digit($revision)) { throw new InputError('Neplatná revize.'); }
    $mode=field($input,'mode',20);$view=standby_rpc();
    $control=$view['control'];
    if ($mode==='maintenance') { $control['manual_maintenance']=true; }
    elseif ($mode==='auto') { $control['manual_maintenance']=false; }
    elseif ($mode==='schedule') {
        $start=standby_prague_utc(field($input,'start',16));$end=standby_prague_utc(field($input,'end',16));
        if ($end<=$start || strtotime($end)<=time()) { throw new InputError('Konec musí být v budoucnosti a po začátku.'); }
        $control['windows']=[['start_utc'=>$start,'end_utc'=>$end]];
    } elseif ($mode==='clear-schedule') { $control['windows']=[]; }
    else { throw new InputError('Neznámá operace údržby.'); }
    standby_rpc(['kind'=>'set_control','revision'=>(int)$revision,'params'=>$control]);
    header('Location: /?standby=1',true,303);exit;
}

function serve_standby(string $csrf,string $error): never {
    $view=null;
    try { $view=standby_rpc(); } catch (Throwable $failure) { $error=$error?:'Služba údržby zatím není připojená. Žádná změna nebyla provedena.'; }
    $labels=['ONLINE'=>'Živý web','STANDBY'=>'Statická záložní verze','MAINTENANCE'=>'Plánovaná nebo ruční údržba','OVERRUN'=>'Údržba překročila termín — čekáme na zdravý web'];
    $date=function(string $utc):string { try { return (new DateTimeImmutable($utc))->setTimezone(new DateTimeZone('Europe/Prague'))->format('d. m. Y H:i:s T'); } catch(Throwable $e) { return 'Neověřeno'; } };
    ?>
<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FallbackHosting · Dostupnost a údržba</title><link rel="stylesheet" href="/admin.css"></head><body><header><a class="brand" href="/">F/ <span>FallbackHosting</span></a><a href="/">Servery</a><a href="/?install=1">Aplikace</a><a href="/?center=index.html">Řídicí centrum</a><form method="post" action="/"><input type="hidden" name="action" value="logout"><input type="hidden" name="csrf" value="<?=e($csrf)?>"><button class="quiet">Odhlásit</button></form></header><main><section class="heading"><p class="eyebrow">DOSTUPNOST / PRVNÍ DEMO</p><h1>Živý web, záložní verze a údržba</h1><p>První řízený průchod pro jeden ukázkový web. V dalších krocích přidáme další aplikace.</p></section>
<?php if($error!==''): ?><p role="alert" class="alert"><?=e($error)?></p><?php endif; ?>
<?php if($view): $health=$view['health'];$fresh=is_array($health)&&isset($health['utc'])&&time()-strtotime($health['utc'])>=0&&time()-strtotime($health['utc'])<=15; ?>
<section class="panel"><p class="eyebrow">MALÁ KAVÁRNA / DEMO</p><h2><?=e($fresh?($labels[$health['mode']]??'Stav vyžaduje kontrolu'):'Chybí aktuální ověření')?></h2><p>Poslední ověření: <?=e(isset($health['utc'])?$date($health['utc']):'Čeká na první kontrolu')?>. <?= $fresh?'Záznam vzniká kontrolou aplikace.':'Uložený záznam nepovažujeme za živý stav.' ?></p><p>Požadavek: <?= $view['control']['manual_maintenance']?'ruční údržba zapnutá':'automatický režim s případným plánovaným intervalem' ?>.</p><p>Po výpadku nebo údržbě čekáme na tři úspěšné kontroly. Záložní stránka zachovává vzhled a místo objednávek nabízí kontakt.</p><a class="button" href="/demo/" target="_blank" rel="noopener">Otevřít ukázkový web ↗</a> <a href="/?standby=1">Obnovit ověření</a></section>
<section class="panel"><h2>Ruční údržba</h2><p>Zapnutí přepne demo na statickou kontaktní verzi. Automatický režim respektuje naplánovaný interval a zdraví aplikace.</p><form method="post" action="/?standby=1"><input type="hidden" name="action" value="standby-control"><input type="hidden" name="csrf" value="<?=e($csrf)?>"><input type="hidden" name="revision" value="<?=e($view['revision'])?>"><button name="mode" value="maintenance">Zapnout údržbu</button> <button name="mode" value="auto">Automatický režim</button></form></section>
<section class="panel"><h2>Naplánovat údržbu</h2><p>Časy zadávejte pro Prahu. První verze podporuje jeden interval pro demo.</p><form method="post" action="/?standby=1"><input type="hidden" name="action" value="standby-control"><input type="hidden" name="csrf" value="<?=e($csrf)?>"><input type="hidden" name="revision" value="<?=e($view['revision'])?>"><div class="fields"><label>Začátek · Praha<input type="datetime-local" name="start" required></label><label>Konec · Praha<input type="datetime-local" name="end" required></label></div><button name="mode" value="schedule">Uložit interval</button></form>
<?php foreach($view['control']['windows'] as $window): ?><p><?=e($date($window['start_utc']))?> — <?=e($date($window['end_utc']))?></p><textarea readonly rows="4" class="wide" aria-label="Oznámení pro zákazníky">Plánovaná údržba: <?=e($date($window['start_utc']))?> až <?=e($date($window['end_utc']))?>. Web bude dostupný v záložním režimu; online objednávky budou dočasně nedostupné. Použijte kontaktní údaje na webu.</textarea><form method="post" action="/?standby=1"><input type="hidden" name="action" value="standby-control"><input type="hidden" name="csrf" value="<?=e($csrf)?>"><input type="hidden" name="revision" value="<?=e($view['revision'])?>"><button name="mode" value="clear-schedule">Zrušit interval</button></form><?php endforeach; ?></section>
<?php publication_panel($csrf); ?>
<section class="panel"><h2>Výchozí ověřená kopie při nasazení</h2><p>Původní verze: <?=e($view['snapshot']['release']??'Není doložena')?>.</p><p><?=e(($view['snapshot']['remote_backup']??'')==='VERIFIED_READBACK_RESTORE'?'Záloha statické kopie: vzdálené uložení, stažení zpět a oddělená obnova ověřené.':'Vzdálená záloha zatím není doložena.')?></p><p>Toto není potvrzení zálohy databází nebo celého serveru. Novou kopii připravíte a prohlédnete výše; publikování vyžaduje ověřenou zálohu.</p></section>
<section class="panel"><h2>Poslední změny</h2><ul><?php foreach(array_reverse($view['audit']) as $item): ?><li><?=e($date($item['utc']))?> · <?=e($item['actor'])?> · revize <?=e($item['revision'])?></li><?php endforeach; ?></ul></section>
<?php endif; ?></main><footer>FallbackHosting · <a href="https://project.lab.ventureout.cz/">Průběh projektu</a></footer></body></html><?php exit;
}
