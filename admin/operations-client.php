<?php
declare(strict_types=1);
/** No SSH, shell or signing keys. Socket/capability come from trusted backend configuration. */
function operations_call(string $socket, array $request): array {
    if (!str_starts_with($socket,'/') || strlen($socket)>100 || str_contains($socket,"\0")) { throw new RuntimeException('Invalid operations socket.'); }
    // PHP associative decoding turns an empty JSON object into []; preserve signed params.
    if (array_key_exists('params',$request) && $request['params']===[]) { $request['params']=new stdClass(); }
    $body=json_encode($request,JSON_THROW_ON_ERROR);
    if (strlen($body)>16384) { throw new RuntimeException('Operations request too large.'); }
    $deadline=hrtime(true)+20000000000;
    $connection=@stream_socket_client('unix://'.$socket,$error,$message,2,STREAM_CLIENT_CONNECT);
    if ($connection===false) { throw new RuntimeException('Operations service unavailable.'); }
    try {
        $budget=function() use ($connection,$deadline): void {
            $remaining=($deadline-hrtime(true))/1000000000;
            if ($remaining<=0) { throw new RuntimeException('Operations deadline expired.'); }
            $seconds=(int)$remaining;
            stream_set_timeout($connection,$seconds,max(1,(int)(($remaining-$seconds)*1000000)));
        };
        $frame=pack('N',strlen($body)).$body;
        while ($frame!=='') {
            $budget();
            $written=@fwrite($connection,$frame);
            if ($written===false || $written===0) { throw new RuntimeException('Operations request incomplete.'); }
            $frame=substr($frame,$written);
        }
        $read=function(int $count) use ($connection,$budget): string {
            $value='';
            while (strlen($value)<$count) {
                $budget();
                $part=@fread($connection,$count-strlen($value));
                if ($part===false || $part==='') { throw new RuntimeException('Operations response incomplete.'); }
                $value.=$part;
            }
            return $value;
        };
        $length=unpack('Nlength',$read(4))['length'];
        if ($length<1 || $length>16384) { throw new RuntimeException('Operations response too large.'); }
        $result=json_decode($read($length),true,32,JSON_THROW_ON_ERROR);
        if (!is_array($result)) { throw new RuntimeException('Invalid operations response.'); }
        return $result;
    } finally { fclose($connection); }
}

// Explicit CLI fixture client only; including this file from PHP never auto-dispatches.
if (PHP_SAPI==='cli' && realpath($_SERVER['SCRIPT_FILENAME'] ?? '')===__FILE__) {
    try {
        $input=json_decode(stream_get_contents(STDIN,20000),true,32,JSON_THROW_ON_ERROR);
        if (!is_array($input) || array_keys($input)!==['socket','request'] || !is_string($input['socket']) || !is_array($input['request'])) { throw new RuntimeException('Invalid local input.'); }
        echo json_encode(operations_call($input['socket'],$input['request']),JSON_THROW_ON_ERROR)."\n";
    } catch (Throwable $failure) { fwrite(STDERR,"Operations request unavailable or invalid.\n"); exit(1); }
}
