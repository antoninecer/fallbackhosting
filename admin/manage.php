<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
umask(0077);
require __DIR__ . '/lib.php';
try {
    $input = json_decode(stream_get_contents(STDIN, 65536), true, 32, JSON_THROW_ON_ERROR);
    if (!is_array($input)) { throw new InputError('Invalid input.'); }
    $dir = admin_dir();
    $command = $argv[1] ?? '';
    if ($command === 'bootstrap') {
        locked('auth', function () use ($input, $dir): void {
            if (file_exists($dir . '/auth.json')) { throw new InputError('Admin already provisioned; no overwrite.'); }
            $user = field($input, 'username', 40);
            $password = $input['password'] ?? '';
            if (!is_string($password) || strlen($password) < 14 || strlen($password) > 256) { throw new InputError('Password needs 14–256 bytes.'); }
            if (!is_dir($dir . '/sessions') && !mkdir($dir . '/sessions',0700)) { throw new RuntimeException('Session directory creation failed.'); }
            if ((fileperms($dir . '/sessions') & 0077) !== 0) { throw new RuntimeException('Session directory must be private.'); }
            write_json('auth', ['username'=>$user,'password_hash'=>password_hash($password, PASSWORD_ARGON2ID),'created_at_utc'=>gmdate('c')]);
        });
        echo "Administrator provisioned; credential not displayed.\n";
    } elseif ($command === 'seed') {
        locked('inventory', function () use ($input, $dir): void {
            if (file_exists($dir . '/inventory.json')) { throw new InputError('Inventory exists; no overwrite.'); }
            $servers = [];
            foreach ($input['servers'] ?? [] as $row) {
                $observations = $row['observations'] ?? null;
                unset($row['observations']);
                $node = normalize_server($row);
                if ($observations !== null) { $node['observations'] = $observations; }
                if (isset($servers[$node['id']])) { throw new InputError('Duplicate server ID.'); }
                $servers[$node['id']] = $node;
            }
            if (!$servers || count($servers) > 100) { throw new InputError('Expected 1–100 server records.'); }
            write_json('inventory', ['schema_version'=>1,'revision'=>1,'gateway'=>['id'=>'oracle','name'=>'Oracle · veřejný vstup','url'=>'https://lab.ventureout.cz'],'servers'=>array_values($servers),'audit'=>[],'updated_at_utc'=>gmdate('Y-m-d\TH:i:s\Z')]);
        });
        echo "Private inventory initialized.\n";
    } else { throw new InputError('Use bootstrap or seed, JSON input on stdin.'); }
} catch (Throwable $error) { fwrite(STDERR, "Setup refused: " . $error->getMessage() . "\n"); exit(1); }
