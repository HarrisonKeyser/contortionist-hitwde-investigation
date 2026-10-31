import struct,sys,subprocess,os
def frames(d,p):
    while p+2<=len(d):
        cs=struct.unpack('>H',d[p:p+2])[0]
        yield d[p+2:p+2+cs]; p+=2+cs
def decode(path,out):
    d=open(path,'rb').read()
    assert d[:4]==b'\x0f\xf5\x12\xed'
    flags=struct.unpack('>I',d[12:16])[0]
    # find n such that framing from 0x10+4n consumes file exactly and sizes sum plausible
    best=None
    for n in range(0,80):
        st=0x10+4*n; p=st
        while p+2<=len(d):
            cs=struct.unpack('>H',d[p:p+2])[0]
            if cs==0: break
            p+=2+cs
        if p==len(d):
            ents=[struct.unpack('>I',d[0x10+i*4:0x14+i*4])[0] for i in range(n)]
            nfr=sum(1 for _ in frames(d,st))
            if sum((e+0x7fff)//0x8000 for e in ents)==nfr: best=(n,st,ents); break
    if best is None: return None
    n,st,ents=best
    fr=list(frames(d,st)); res=bytearray(); fi=0
    for e in ents:
        k=(e+0x7fff)//0x8000
        buf=b''.join(fr[fi:fi+k]); fi+=k
        open(out+'.lz','wb').write(buf+b'\0'*0x10000)
        r=subprocess.run([os.path.join(os.path.dirname(os.path.abspath(__file__)),'unlzx'),out+'.lz',out+'.part',str(e),'17'],capture_output=True,text=True)
        if r.returncode: raise Exception('lzx fail '+r.stderr)
        res+=open(out+'.part','rb').read()
    os.remove(out+'.lz'); os.remove(out+'.part')
    open(out,'wb').write(res)
    return n,len(res)
if __name__=='__main__':
    print(decode(sys.argv[1],sys.argv[2]))
