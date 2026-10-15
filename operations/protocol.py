"""One bounded Unix-socket request. No listener/service is installed by this module."""
import socket
import struct
from .core import Denied, canonical, decode_json
MAX_FRAME=16384


def read_exact(connection,count):
    chunks=[]
    while count:
        piece=connection.recv(count)
        if not piece:raise Denied('INCOMPLETE_FRAME')
        chunks.append(piece);count-=len(piece)
    return b''.join(chunks)


def serve_connection(connection,broker):
    connection.settimeout(2)
    try:
        _,uid,_=struct.unpack('3i',connection.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))
        length=struct.unpack('!I',read_exact(connection,4))[0]
        if not 1<=length<=MAX_FRAME:raise Denied('FRAME_TOO_LARGE')
        request=decode_json(read_exact(connection,length))
        response=broker.read(request,uid) if isinstance(request,dict) and request.get('kind') in {'view','job_status'} else broker.submit(request,uid)
    except Denied as error:response={'error':error.code}
    except Exception:response={'error':'PROTOCOL_FAILURE'}
    encoded=canonical(response).encode()
    if len(encoded)>MAX_FRAME:encoded=b'{"error":"OUTPUT_TOO_LARGE"}'
    try:connection.sendall(struct.pack('!I',len(encoded))+encoded)
    finally:connection.close()
