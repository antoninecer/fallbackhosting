<?php
declare(strict_types=1);
/** Read-only local scoped projection; no private transport or credentials rendered. */
function ops_e(string $value): string { return htmlspecialchars($value,ENT_QUOTES|ENT_SUBSTITUTE,'UTF-8'); }
function ops_time(?string $value): string {
    if ($value===null) { return 'Neznámý čas'; }
    try { return (new DateTimeImmutable($value))->setTimezone(new DateTimeZone('Europe/Prague'))->format('d. m. Y H:i:s T'); }
    catch (Throwable $failure) { return 'Neznámý čas'; }
}
function operations_render(array $views): string {
    if (count($views)>50) { throw new RuntimeException('Too many scoped application views.'); }
    $cards='';$jobs='';$errors='';$audit='';$nodes=[];
    $labels=['QUEUED'=>'Ve frontě','RUNNING'=>'Probíhá','SUCCEEDED'=>'Dokončeno','FAILED'=>'Selhalo','UNKNOWN'=>'Výsledek nejasný','created'=>'Vytvořený','running'=>'Spuštěný','exited'=>'Zastavený','missing'=>'Odstraněný','unknown'=>'Neznámý'];
    foreach ($views as $view) {
        $expected=['node','project','app','last_observation','health_provenance','current_health','jobs','errors','audit'];
        if (!is_array($view) || count($view)!==count($expected) || array_diff($expected,array_keys($view)) || !is_array($view['jobs']) || !is_array($view['errors']) || !is_array($view['audit']) || count($view['jobs'])>50 || count($view['errors'])>50 || count($view['audit'])>50) { throw new RuntimeException('Invalid scoped view.'); }
        foreach (['node','project','app'] as $id) { if (!is_string($view[$id]) || !preg_match('/^[a-z][a-z0-9-]{0,39}$/D',$view[$id])) { throw new RuntimeException('Invalid scoped identity.'); } }
        $nodes[$view['node']]=true;
        $last=$view['last_observation'];
        if ($last!==null && (!is_array($last) || !is_string($last['container_id'] ?? null) || !preg_match('/^[a-f0-9]{64}$/D',$last['container_id']))) { throw new RuntimeException('Invalid observed resource.'); }
        $observed=$last ? ($labels[$last['state']] ?? 'Neznámý') : 'Bez zaznamenaného kontejneru';
        $cards.='<article class="panel node"><p class="eyebrow">'.ops_e($view['project']).' · '.ops_e($view['node']).'</p><h2>'.ops_e($view['app']).'</h2><p>Poslední pozorovaný stav: <strong>'.ops_e($observed).'</strong></p><p class="muted">'.ops_e(ops_time($last['observed_utc'] ?? null)).' · uložený výsledek, nikoli živý monitoring</p><p class="address">'.ops_e($last['container_id'] ?? 'Žádný registrovaný prostředek').'</p><p>Aktuální dostupnost: neověřená.</p></article>';
        foreach ($view['jobs'] as $job) {
            $jobs.='<tr><td data-label="Požadavek">'.ops_e($job['job_id']).'</td><td data-label="Aplikace">'.ops_e($view['app']).'</td><td data-label="Operace">'.ops_e($job['action']).'</td><td data-label="Výsledek">'.ops_e($labels[$job['state']] ?? 'Neznámý').'</td><td data-label="Čas Praha">'.ops_e(ops_time($job['finished_utc'] ?? $job['created_utc'])).'</td></tr>';
        }
        foreach ($view['errors'] as $job) { $errors.='<li>'.ops_e($view['app']).' · '.ops_e($job['job_id']).' · '.ops_e($job['code'] ?? 'UNKNOWN').'</li>'; }
        foreach ($view['audit'] as $entry) { $audit.='<li>'.ops_e(ops_time($entry['utc'])).' · '.ops_e($entry['action']).' · '.ops_e($entry['result']).'</li>'; }
    }
    $nodeList=implode(', ',array_keys($nodes));
    return '<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'self\'; base-uri \'none\'; form-action \'none\'"><title>FallbackHosting · Aplikace a operace — místní prototyp</title><link rel="stylesheet" href="admin.css"><link rel="stylesheet" href="operations.css"></head><body><header><a class="brand" href="#apps">F/ FallbackHosting</a><span class="tag">Místní prototyp · pouze pro čtení</span></header><main><section class="heading"><p class="eyebrow">APLIKACE / POŽADAVKY / AUDIT</p><h1>Spravované aplikace.<br>Každá operace má výsledek.</h1><p class="muted">Zobrazuje vybrané výsledky místní testovací služby. Tento prototyp není nasazený. Podpisová oprávnění a SSH klíče nejsou součástí PHP.</p><p>Vazby na servery: '.ops_e($nodeList ?: 'Žádné').'. Záznam vazby nepotvrzuje aktuální spojení.</p></section><section id="apps"><h2>Aplikace podle serverů</h2><div class="nodes">'.($cards ?: '<p>Žádné přiřazené aplikace.</p>').'</div></section><section><h2>Požadavky, průběh a výsledky</h2><div class="operations-table"><table><thead><tr><th>Požadavek</th><th>Aplikace</th><th>Operace</th><th>Výsledek</th><th>Čas Praha</th></tr></thead><tbody>'.$jobs.'</tbody></table></div>'.($jobs==='' ? '<p>Žádné zaznamenané požadavky.</p>' : '').'</section><section><h2>Chyby a nejasné výsledky</h2><ul>'.($errors ?: '<li>Žádné zaznamenané chyby.</li>').'</ul></section><section><h2>Audit operací</h2><div class="operations-audit" tabindex="0" role="region" aria-label="Audit operací"><ul>'.($audit ?: '<li>Žádné zaznamenané operace.</li>').'</ul></div></section><section class="panel"><h2>Bezpečný úklid aplikace</h2><p>Úklid se vztahuje jen na registrovaný a označený kontejner vybrané aplikace: samostatné zastavení, potom odstranění s potvrzením úplného ID a jednorázovým schválením. Plošný prune, svazky a cizí kontejnery nejsou dostupné.</p><p class="muted">Tento přehled operace nespouští. Místní PHP klient je testovaný proti izolované službě; ovládání z webu a produkční nasazení vyžadují dokončené ověření identity uživatele a schvalování.</p></section></main></body></html>';
}
if (PHP_SAPI==='cli' && realpath($_SERVER['SCRIPT_FILENAME'] ?? '')===__FILE__) {
    try {
        $input=json_decode(stream_get_contents(STDIN,131072),true,32,JSON_THROW_ON_ERROR);
        if (!is_array($input)) { throw new RuntimeException('Invalid local projection.'); }
        echo operations_render($input);
    } catch (Throwable $failure) { fwrite(STDERR,"Operations view invalid.\n");exit(1); }
}
