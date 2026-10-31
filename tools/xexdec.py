import struct,sys,subprocess,os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
d=open(sys.argv[1],'rb').read()
magic,flags,pe_off,res,sec_off,cnt=struct.unpack('>4sIIIII',d[:24])
hdrs={}
for i in range(cnt):
    k,v=struct.unpack('>II',d[24+i*8:32+i*8]); hdrs[k]=v
ffi=hdrs[0x3ff]
size,enc,comp=struct.unpack('>IHH',d[ffi:ffi+8])
imgsize=struct.unpack('>I',d[sec_off+4:sec_off+8])[0]
key=d[sec_off+0x150:sec_off+0x160]
retail=bytes.fromhex('20B185A59D28FDC340583FBB0896BF91')
def ecb_dec(k,data):
    c=Cipher(algorithms.AES(k),modes.ECB()).decryptor(); return c.update(data)+c.finalize()
sk=ecb_dec(retail,key)
body=d[pe_off:]
body=body[:len(body)//16*16]
c=Cipher(algorithms.AES(sk),modes.CBC(b'\0'*16)).decryptor()
p=c.update(body)+c.finalize()
window=struct.unpack('>I',d[ffi+8:ffi+12])[0]
blksize=struct.unpack('>I',d[ffi+12:ffi+16])[0]
print('window',hex(window),'first block',hex(blksize),'img',hex(imgsize))
out=bytearray(); pos=0
while blksize:
    blk=p[pos:pos+blksize]
    nxt=struct.unpack('>I',blk[:4])[0]
    q=24
    while True:
        cs=struct.unpack('>H',blk[q:q+2])[0]; q+=2
        if cs==0: break
        out+=blk[q:q+cs]; q+=cs
    pos+=blksize; blksize=nxt
open(sys.argv[2]+'.lzx','wb').write(out)
wb=window.bit_length()-1
r=subprocess.run([os.path.join(os.path.dirname(os.path.abspath(__file__)),'unlzx'),sys.argv[2]+'.lzx',sys.argv[2],hex(imgsize),str(wb)])
print('rc',r.returncode)
