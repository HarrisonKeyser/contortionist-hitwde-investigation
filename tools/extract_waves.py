"""Unpack data.xpr (after xcompress_decode.py) and convert every themes/*/Wave*.hitwr to UTF-8.
Usage: python3 extract_waves.py data.bin out_dir"""
import struct, os, sys
d = open(sys.argv[1], 'rb').read(); out = sys.argv[2]
magic, hsz, dsz, n = struct.unpack('>4sIII', d[:16]); assert magic == b'XPR2'
for i in range(n):
    typ, off, sz, nameoff = struct.unpack('>4sIII', d[16+i*16:32+i*16])
    name = d[12+nameoff:d.index(b'\0', 12+nameoff)].decode()
    if name.startswith('themes\\') and name.endswith('.hitwr'):
        _, theme, wave = name.split('\\')
        txt = d[12+off:12+off+sz].decode('utf-16')
        os.makedirs(out, exist_ok=True)
        open(os.path.join(out, f'{theme}_{wave[:-6]}.xml'), 'w', encoding='utf-8').write(txt)
