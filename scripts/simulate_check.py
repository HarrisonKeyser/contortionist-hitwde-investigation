"""
Re-implements Hole in the Wall Deluxe's Contortionist check (0x821b2ef8) and
feeds it every bit the game can actually set, given how wall indices are
assigned at load time (0x821bbd78: stw r4,0x58(r3) with r4 = index inside
the wave file).  Usage: python3 simulate_check.py <dir of UTF-8 wave XMLs>
"""
import re, glob, sys, os
THEMES = ['Everyday','Europe','WorkPlaces','Disco','Activities','Art','USA','SouthAm',
          'Body','OtherThemes','Australia','Fantastic','Sport','Prehistory','Winter',
          'Human','Extreme','China','Russia','SpecialLocations']          # 0x8282d950[0..19]
COUNTS = [76,67,77,74,74,64,72,88,69,69,76,74,77,72,79,65,65,70,75,70]  # 0x8200e930
MASK   = [0x00,0x01,0x03,0x07,0x0f,0x1f,0x3f,0x7f]                       # 0x8200e980 / 0x8200e98c
WAVES  = ['Wave01','Wave02','Wave03','Wave04','Wave06','Wave07','Wave08','Wave09']  # 0x821bb280

def check(bits):                      # bits: bytearray(20*0x14) == profile+0x1dc
    for t, n in enumerate(COUNTS):
        base = t * 0x14
        for b in range(n // 8):
            if bits[base + b] != 0xFF: return False, t, b
        r = n % 8
        if bits[base + n // 8] & MASK[r] != MASK[r]: return False, t, n // 8
    return True, None, None

def set_bit(bits, theme, idx):        # 0x821b2eb0
    bits[theme * 0x14 + (idx >> 3)] |= 1 << (idx & 7)

d = sys.argv[1]
as_shipped = bytearray(0x190); as_intended = bytearray(0x190)
print(f"{'theme':17} need  walls  max idx set (shipped)  max idx (intended)")
for t, name in enumerate(THEMES):
    offset = 0; mx = -1
    for w in WAVES:
        s = open(os.path.join(d, f'{name}_{w}.xml'), encoding='utf-8').read()
        n = len(re.findall(r'<WALL[ >]', s))
        for i in range(n):
            set_bit(as_shipped, t, i)            # what the game does
            set_bit(as_intended, t, offset + i)  # what the caller's running offset implies
            mx = max(mx, i)
        offset += n
    print(f'{name:17} {COUNTS[t]:4} {offset:6} {mx:12} {offset-1:20}')
print('\nshipped game  ->', check(as_shipped))
print('with offset   ->', check(as_intended))
