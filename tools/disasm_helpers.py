import struct
from capstone import *
BASE=0x82000000
D=open(__import__('os').environ.get('HITW_PE','default.pe'),'rb').read()
TEXT=(0x170000,0x170000+0x697080)
md=Cs(CS_ARCH_PPC, CS_MODE_32|CS_MODE_BIG_ENDIAN)
md.detail=False
def u32(va): o=va-BASE; return struct.unpack('>I',D[o:o+4])[0]
def word(off): return struct.unpack('>I',D[off:off+4])[0]
def dis(va,n):
    o=va-BASE
    return list(md.disasm(D[o:o+4*n],va))
def pr(va,n):
    for i in dis(va,n): print('%08x: %08x  %s %s'%(i.address,u32(i.address),i.mnemonic,i.op_str))
def cstr(va,maxn=200):
    o=va-BASE; e=D.find(b'\0',o,o+maxn); return D[o:e]
PDATA=[]
_o=0x143200
for _i in range(0x1ad70//8):
    b,f=struct.unpack('>II',D[_o+_i*8:_o+_i*8+8])
    if b==0: continue
    PDATA.append((b,b+((f>>8)&0x3fffff)*4))
PDATA.sort()
import bisect
_starts=[p[0] for p in PDATA]
def func(va):
    i=bisect.bisect_right(_starts,va)-1
    if i>=0 and PDATA[i][0]<=va<PDATA[i][1]: return PDATA[i]
    return None
def prf(va):
    f=func(va); print('--- func %x-%x'%f); pr(f[0],(f[1]-f[0])//4)
def callers(target):
    res=[]
    for off in range(TEXT[0],TEXT[1],4):
        w=word(off)
        if (w>>26)==18 and (w&3)==1:
            li=w&0x3fffffc
            if li&0x2000000: li-=0x4000000
            if BASE+off+li==target: res.append(BASE+off)
    return res
