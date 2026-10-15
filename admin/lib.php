<?php
declare(strict_types=1);

final class InputError extends RuntimeException {}
final class RevisionConflict extends RuntimeException {}

function admin_dir(): string {
    $path = getenv('FH_ADMIN_DATA') ?: '';
    $real = $path === '' ? false : realpath($path);
    if ($real === false || !is_dir($real) || (fileperms($real) & 0077) !== 0) {
        throw new RuntimeException('Private data directory is not configured safely.');
    }
    $public = realpath(__DIR__ . '/public');
    if ($public !== false && ($real === $public || str_starts_with($real, $public . '/'))) {
        throw new RuntimeException('Private data cannot be in the webroot.');
    }
    return $real;
}

function read_json(string $name): array {
    if (!is_file(admin_dir() . '/' . $name . '.json')) { throw new RuntimeException('Data unavailable.'); }
    $raw = file_get_contents(admin_dir() . '/' . $name . '.json');
    if ($raw === false) { throw new RuntimeException('Data unavailable.'); }
    $data = json_decode($raw, true, 32, JSON_THROW_ON_ERROR);
    if (!is_array($data)) { throw new RuntimeException('Invalid stored data.'); }
    return $data;
}

function write_json(string $name, array $data): void {
    $dir = admin_dir();
    $temp = tempnam($dir, '.pending-');
    if ($temp === false) { throw new RuntimeException('Cannot write data.'); }
    try {
        $encoded = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR) . "\n";
        if (file_put_contents($temp, $encoded) !== strlen($encoded) || !rename($temp, $dir . '/' . $name . '.json')) {
            throw new RuntimeException('Cannot commit data.');
        }
    } finally {
        if (is_file($temp)) { unlink($temp); }
    }
}

function locked(string $name, callable $fn): mixed {
    $lock = fopen(admin_dir() . '/' . $name . '.lock', 'c');
    if ($lock === false || !flock($lock, LOCK_EX)) { throw new RuntimeException('Cannot lock data.'); }
    try { return $fn(); } finally { flock($lock, LOCK_UN); fclose($lock); }
}

function field(array $input, string $name, int $max, bool $required = true): string {
    if (!isset($input[$name]) || !is_string($input[$name])) {
        if (!$required) { return ''; }
        throw new InputError('Chybí pole: ' . $name);
    }
    $value = trim($input[$name]);
    if (($required && $value === '') || strlen($value) > $max || !preg_match('//u', $value) || preg_match('/[\x00-\x1f\x7f]/', $value)) {
        throw new InputError('Neplatné pole: ' . $name);
    }
    return $value;
}

function normalize_server(array $input, ?array $old = null): array {
    $allowed = ['id','name','host','ssh_port','ssh_user','runtime','platform','credential_ref','host_fingerprint','description','enabled'];
    if (array_diff(array_keys($input), $allowed)) { throw new InputError('Nepovolené pole konfigurace.'); }
    $id = field($input, 'id', 40);
    if (!preg_match('/^[a-z][a-z0-9-]{0,39}$/D', $id) || in_array($id, ['gateway','admin','project'], true)) {
        throw new InputError('ID musí být jednoduchý jedinečný název.');
    }
    $host = strtolower(field($input, 'host', 253));
    if (!filter_var($host, FILTER_VALIDATE_IP) && !filter_var($host, FILTER_VALIDATE_DOMAIN, FILTER_FLAG_HOSTNAME)) {
        throw new InputError('Zadejte platnou IP adresu nebo hostname bez protokolu.');
    }
    $port = field($input, 'ssh_port', 5);
    if (!ctype_digit($port) || (int)$port < 1 || (int)$port > 65535) { throw new InputError('Neplatný SSH port.'); }
    $user = field($input, 'ssh_user', 32);
    if (!preg_match('/^[a-z_][a-z0-9_-]{0,31}$/D', $user)) { throw new InputError('Neplatný SSH účet.'); }
    $runtime = field($input, 'runtime', 20);
    $platform = field($input, 'platform', 20);
    if (!in_array($runtime, ['docker','podman','other'], true) || !in_array($platform, ['lxc','vm','physical','unknown'], true)) {
        throw new InputError('Neznámý typ serveru nebo runtime.');
    }
    $ref = field($input, 'credential_ref', 64, false);
    if ($ref !== '' && !preg_match('/^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/D', $ref)) {
        throw new InputError('Reference identity smí obsahovat pouze název, nikoli cestu nebo klíč.');
    }
    $fingerprint = field($input, 'host_fingerprint', 60, false);
    if ($fingerprint !== '' && !preg_match('/^SHA256:[A-Za-z0-9+\/]{43}$/D', $fingerprint)) {
        throw new InputError('Fingerprint musí mít formát SHA256.');
    }
    $server = ['id'=>$id,'name'=>field($input,'name',80),'host'=>$host,'ssh_port'=>(int)$port,
        'ssh_user'=>$user,'runtime'=>$runtime,'platform'=>$platform,'credential_ref'=>$ref,
        'host_fingerprint'=>$fingerprint,'description'=>field($input,'description',300,false),
        'enabled'=>($input['enabled'] ?? false) === true || ($input['enabled'] ?? '') === '1'];
    $changed = $old === null;
    foreach (['host','ssh_port','ssh_user','runtime','credential_ref','host_fingerprint'] as $key) {
        if ($old !== null && $old[$key] !== $server[$key]) { $changed = true; }
    }
    $server['observations'] = $changed ? ['ssh'=>['status'=>'UNKNOWN'], 'docker'=>['status'=>'UNKNOWN'], 'fingerprint'=>['status'=>'NEEDS_TEST']] : $old['observations'];
    $server['updated_at_utc'] = gmdate('Y-m-d\TH:i:s\Z');
    return $server;
}

function save_server(array $input, int $expected, string $actor, string $mode): void {
    locked('inventory', function () use ($input, $expected, $actor, $mode): void {
        $data = read_json('inventory');
        if ($data['revision'] !== $expected) { throw new RevisionConflict('Konfiguraci mezitím někdo změnil. Obnovte stránku a zkuste to znovu.'); }
        $id = is_string($input['id'] ?? null) ? $input['id'] : '';
        $index = null;
        foreach ($data['servers'] as $i => $node) { if ($node['id'] === $id) { $index = $i; } }
        if (!in_array($mode,['create','edit'],true) || ($mode === 'create' && $index !== null) || ($mode === 'edit' && $index === null)) {
            throw new InputError('ID již existuje nebo upravovaný server nebyl nalezen.');
        }
        if ($index === null && count($data['servers']) >= 100) { throw new InputError('Byl dosažen limit 100 serverů.'); }
        $server = normalize_server($input, $index === null ? null : $data['servers'][$index]);
        if ($index === null) { $data['servers'][] = $server; } else { $data['servers'][$index] = $server; }
        $data['revision']++;
        $data['updated_at_utc'] = gmdate('Y-m-d\TH:i:s\Z');
        $data['audit'][] = ['utc'=>$data['updated_at_utc'],'actor'=>$actor,'action'=>$index === null ? 'server.add' : 'server.update','server_id'=>$server['id'],'revision'=>$data['revision']];
        $data['audit'] = array_slice($data['audit'], -100);
        // Config and its bounded audit commit together under the same lock.
        write_json('inventory', $data);
    });
}

function login_allowed(string $ip, bool $success = false): bool {
    return locked('login-limit', function () use ($ip, $success): bool {
        $path = admin_dir() . '/login-limit.json';
        $data = is_file($path) ? read_json('login-limit') : [];
        $now = time();
        $data = array_filter($data, fn($v) => $v['until'] > $now);
        $key = hash('sha256', $ip);
        if ($success) { unset($data[$key]); write_json('login-limit',$data); return true; }
        foreach ([$key=>5, 'global'=>50] as $bucket=>$limit) {
            if (($data[$bucket]['count'] ?? 0) >= $limit) { return false; }
        }
        foreach ([$key,'global'] as $bucket) {
            $data[$bucket] ??= ['count'=>0,'until'=>$now+600];
            $data[$bucket]['count']++;
        }
        if (count($data) > 128) { $data = array_slice($data, -128, null, true); }
        write_json('login-limit', $data);
        return true;
    });
}

function e(string|int $value): string { return htmlspecialchars((string)$value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'); }
