<?php
declare(strict_types=1);
require_once __DIR__.'/operations-client.php';

function publication_rpc(array $extra=[]): array {
    $request=array_merge(['kind'=>'view','actor'=>$_SESSION['user'],'app'=>'demo'],$extra);
    $result=operations_call(admin_dir().'/publication.sock',$request);
    if (($result['ok']??false)!==true) { throw new InputError('Požadavek na publikování nebyl přijat. Obnovte stav a zkontrolujte výsledek před opakováním.'); }
    return $result;
}

function publication_action(array $input): never {
    if (array_diff(array_keys($input),['action','csrf','revision','operation'])) { throw new InputError('Nepovolené pole publikování.'); }
    $revision=field($input,'revision',10);$operation=field($input,'operation',20);
    if (!ctype_digit($revision)||!in_array($operation,['prepare','publish','rollback'],true)) { throw new InputError('Neplatný požadavek na publikování.'); }
    publication_rpc(['kind'=>'publication','revision'=>(int)$revision,'operation'=>$operation]);
    header('Location: /?standby=1',true,303);exit;
}

function publication_panel(string $csrf): void {
    try { $view=publication_rpc(); } catch (Throwable $e) { echo '<section class="panel"><h2>Nová záložní verze</h2><p>Publikování nyní není dostupné. Existující záložní stránka funguje nezávisle.</p></section>';return; }
    $labels=['IDLE'=>'Čeká na přípravu','PREPARING'=>'Připravujeme export a ověřujeme zálohu','READY'=>'Připraveno k prohlédnutí a publikování','PUBLISHING'=>'Probíhá publikování','PUBLISHED'=>'Nová verze je publikovaná','ROLLING_BACK'=>'Probíhá návrat k předchozí verzi','ROLLED_BACK'=>'Předchozí verze byla obnovena','FAILED'=>'Příprava selhala; publikovaná verze zůstala zachovaná','NEEDS_REVIEW'=>'Přerušenou operaci musí prověřit správce'];
    ?><section class="panel"><h2>Nová záložní verze</h2><p><strong><?=e($labels[$view['phase']]??'Stav vyžaduje kontrolu')?></strong></p><p>Aktuálně publikovaná verze: <?=e($view['current']??'Neověřeno')?>.</p><p>Připravíme statickou verzi ukázkové kavárny, uložíme ji do vzdálené zálohy, stáhneme zpět a ověříme obnovu. Až potom ji můžete prohlédnout a samostatně publikovat. Živý web se tím nemění.</p>
<?php if (is_string($view['candidate']??null)): ?><p>Verze <?=e($view['candidate'])?></p><a class="button" target="_blank" rel="noopener" href="/?publication-preview=<?=rawurlencode($view['candidate'])?>">Prohlédnout záložní verzi ↗</a><?php endif; ?>
<?php if (($view['backup']??'')==='VERIFIED_READBACK_RESTORE'): ?><p>Vzdálená záloha, stažení zpět a oddělená obnova této verze ověřeny.</p><?php endif; ?>
<form method="post" action="/?standby=1"><input type="hidden" name="action" value="standby-publication"><input type="hidden" name="csrf" value="<?=e($csrf)?>"><input type="hidden" name="revision" value="<?=e($view['revision'])?>">
<?php if (in_array($view['phase'],['IDLE','READY','PUBLISHED','ROLLED_BACK','FAILED'],true)): ?><button name="operation" value="prepare">Připravit novou verzi</button><?php endif; ?>
<?php if ($view['phase']==='READY'): ?><button name="operation" value="publish">Publikovat připravenou verzi</button><?php endif; ?>
<?php if ($view['phase']==='PUBLISHED'): ?><button name="operation" value="rollback">Vrátit předchozí verzi</button><?php endif; ?>
</form><p><a href="/?standby=1">Obnovit stav publikování</a></p></section><?php
}

function publication_preview(mixed $release, mixed $asset): never {
    if (!is_string($release)||!preg_match('/^[0-9]{8}T[0-9]{6}Z-[a-f0-9]{8}$/D',$release)||!is_string($asset)) { http_response_code(404);exit; }
    $files=['index.html'=>'text/html; charset=utf-8','assets/style.css'=>'text/css; charset=utf-8','assets/hero.webp'=>'image/webp'];
    if (!isset($files[$asset])) { http_response_code(404);exit; }
    $root=getenv('FH_STANDBY_RELEASES')?:'/var/www/fallback-standby-demo/releases';
    $dir=$root.'/'.$release;
    if (is_link($dir)||!is_dir($dir)) { http_response_code(404);exit; }
    $manifestPath=$dir.'/manifest.json';
    if (is_link($manifestPath)||!is_file($manifestPath)||filesize($manifestPath)>8192) { http_response_code(404);exit; }
    $manifest=json_decode(file_get_contents($manifestPath),true);
    if (($manifest['release']??null)!==$release || array_diff(array_keys($manifest['files']??[]),array_keys($files)) || count($manifest['files']??[])!==3) { http_response_code(404);exit; }
    if (is_link($dir.'/assets')||is_link($dir.'/'.$asset)||!is_file($dir.'/'.$asset)||filesize($dir.'/'.$asset)>2097152||!hash_equals($manifest['files'][$asset]??'',hash_file('sha256',$dir.'/'.$asset))) { http_response_code(404);exit; }
    $body=file_get_contents($dir.'/'.$asset);
    if ($asset==='index.html') {
        $prefix=$manifest['asset_prefix']??'';
        if ($prefix!=='/demo/__fallback_assets') { http_response_code(404);exit; }
        foreach (['style.css','hero.webp'] as $name) {
            $body=str_replace($prefix.'/'.$name,'/?publication-preview='.rawurlencode($release).'&amp;asset=assets/'.$name,$body);
        }
    }
    header('Content-Type: '.$files[$asset]);
    header("Content-Security-Policy: sandbox allow-same-origin; default-src 'none'; style-src 'self'; img-src 'self'; form-action 'none'; frame-ancestors 'none'; base-uri 'none'");
    header('X-Robots-Tag: noindex');
    echo $body;exit;
}
