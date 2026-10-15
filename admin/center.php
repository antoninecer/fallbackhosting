<?php
declare(strict_types=1);
/** Read-only, session-gated artifact delivery. No shell, keys or remote operations. */
function serve_center(mixed $requested, bool $loggedIn, bool $local): never {
    if (!$loggedIn) { http_response_code(401); exit('Přihlaste se na hlavní stránce administrace.'); }
    $assets = [
        'index.html'=>['text/html; charset=utf-8',1048576],
        'center.css'=>['text/css; charset=utf-8',262144],
        'center.js'=>['application/javascript; charset=utf-8',131072],
        'resume.txt'=>['text/plain; charset=utf-8',131072],
        'manifest.json'=>['application/json; charset=utf-8',8192],
    ];
    if (!is_string($requested) || !isset($assets[$requested])) { http_response_code(404); exit; }
    session_write_close();
    try {
        $configured = getenv('FH_CENTER_ARTIFACT') ?: __DIR__ . '/center-artifact';
        $root = realpath($configured);
        if ($root === false || !is_dir($root) || (!$local && is_writable($root))) { throw new RuntimeException('Artifact unavailable.'); }
        $manifestPath = $root . '/manifest.json';
        if (is_link($manifestPath) || !is_file($manifestPath) || filesize($manifestPath) > 8192) { throw new RuntimeException('Manifest unavailable.'); }
        $manifest = json_decode(file_get_contents($manifestPath),true,16,JSON_THROW_ON_ERROR);
        $expected = ['index.html','center.css','center.js','resume.txt'];
        if (!is_array($manifest) || count($manifest) !== count($expected) || array_diff($expected,array_keys($manifest))) { throw new RuntimeException('Invalid manifest.'); }
        foreach ($expected as $name) {
            if (!is_string($manifest[$name]) || !preg_match('/^[a-f0-9]{64}$/D',$manifest[$name])) { throw new RuntimeException('Invalid digest.'); }
        }
        $path = $root . '/' . $requested;
        if (is_link($path) || !is_file($path) || (!$local && is_writable($path)) || filesize($path) > $assets[$requested][1]) { throw new RuntimeException('Asset unavailable.'); }
        $body = file_get_contents($path);
        if ($body === false || ($requested !== 'manifest.json' && !hash_equals($manifest[$requested],hash('sha256',$body)))) { throw new RuntimeException('Asset digest mismatch.'); }
        header('Content-Type: '.$assets[$requested][0]);
        header('Content-Length: '.strlen($body));
        if ($requested === 'resume.txt') { header('Content-Disposition: attachment; filename="fallbackhosting-resume.txt"'); }
        if ($_SERVER['REQUEST_METHOD'] !== 'HEAD') { echo $body; }
        exit;
    } catch (Throwable $failure) {
        http_response_code(503); exit('Řídicí centrum zatím není bezpečně připravené.');
    }
}
