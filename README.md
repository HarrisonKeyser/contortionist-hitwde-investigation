# Contortionist: why nobody has ever unlocked it

**Game:** Hole in the Wall Deluxe Edition (Xbox 360, USA)
**Achievement:** Contortionist (ID 206, 100G), "Successfully pass all walls in the game at least once."

## TL;DR

**The achievement can't be unlocked on an unmodified copy of the game.** The cause is a bug in how the game numbers its walls.

- The achievement check wants a "passed" bit for every wall in a theme. For a theme with 76 walls that means bits 0 to 75.
- Each wall's number is assigned when its wave file loads, and the numbering **restarts at 0 for every wave file**. A theme is split across 8 wave files of 5 to 16 walls each, so no wall ever gets a number above 15.
- So bits 16 and up can never be set, in any theme, in any mode, on any date. The check fails on the first theme every time.

The developers did try to number walls across the whole theme. The loader adds up a running total of walls and passes it into the function that loads each wave. **That function never uses it.** If the total were applied, the check would pass exactly, as the simulation below shows.

Your play history doesn't matter. Doing every wall perfectly, in solo and co-op, every mode, on a holiday, with Quick Survival finished, still can't unlock it.

---

## How the achievement works (from the disassembly)

All addresses are virtual addresses in the decrypted `default.xex` image (base `0x82000000`). Full annotated listings are in [`evidence/disassembly.txt`](evidence/disassembly.txt).

### 1. Unlock site: `0x821b8c10`
This is a virtual method (vtable slot 12) shared by the four game-mode classes (vtables at `0x8200eca0`, `0x8200edc8`, `0x8200eeb0` and `0x8200f098`). It runs once for each local player on the team when a wall is completed:

```
RecordWallPassed(player, currentWall->index, currentTheme)   ; 0x821b8c94
if (AllWallsPassed(player))                                   ; 0x821b8d0c
    UnlockAchievement(206, player)                            ; 0x821b8d30  (li r4,0xCE)
```

- `currentWall->index` is `wall+0x58`, read at `0x821bbcb0`.
- `currentTheme` is a global theme index from 0 to 25. It is set at `0x821f2eb8` to the position of the loaded theme's name in the table at `0x8282d950`.

### 2. Storage: a bitfield per profile
`SetBit` at `0x821b2eb0`:
```
profile[0x1dc + theme*0x14 + idx/8] |= 1 << (idx % 8)
```
That gives 20 themes × 20 bytes (160 bits per theme). The block is cleared once when the profile is initialised (`0x821b2bbc`: `memset(profile+0x1dc, 0, 0x190)`).

### 3. The check: `0x821b2ef8`
For each of the 20 themes, bits `0 … count-1` must all be set. `count` comes from a hard-coded table at `0x8200e930`:

| # | Theme | Walls required | # | Theme | Walls required |
|---|---|---|---|---|---|
| 0 | Everyday | 76 | 10 | Australia | 76 |
| 1 | Europe | 67 | 11 | Fantastic | 74 |
| 2 | WorkPlaces | 77 | 12 | Sport | 77 |
| 3 | Disco | 74 | 13 | Prehistory | 72 |
| 4 | Activities | 74 | 14 | Winter | 79 |
| 5 | Art | 64 | 15 | Human | 65 |
| 6 | USA | 72 | 16 | Extreme | 65 |
| 7 | SouthAm | 88 | 17 | China | 70 |
| 8 | Body | 69 | 18 | Russia | 75 |
| 9 | OtherThemes | 69 | 19 | SpecialLocations | 70 |

**Total: 1,453 walls.** BattleMode (theme 20) isn't counted. Each number matches the total `<WALL>` count across that theme's 8 wave files in `data.xpr`, so the table itself is correct. It assumes each wall has its own index within the theme.

### 4. Where the indices come from (the bug)

The theme loader is at `0x821bb280`. It loads `themes/<Theme>/Wave01-04.hitwr` and then `Wave06-09.hitwr` (no theme has a `Wave05`). It keeps a running total of walls loaded so far:

```
0x821bb2cc  li   r6, 0                 ; offset = 0
0x821bb2dc  bl   LoadWaves01to04       ; returns offset + walls in waves 1-4
0x821bb2e0  mr   r6, r3                ; offset carried into waves 6-9
0x821bb2f0  bl   LoadWaves06to09
```

Inside each of those (`0x821bafe8` and `0x821bb080`):
```
0x821bb048  mr   r5, r29               ; pass running offset to LoadWave
0x821bb054  bl   LoadWave              ; 0x821bbae0
0x821bb05c  bl   Round::count
0x821bb060  add  r29, r3, r29          ; offset += walls in this wave
```

`LoadWave` (`0x821bbae0`) saves `r3` (round) and `r4` (path) but **never reads `r5`**. The first `bl` overwrites it, and it's later reused for something else at `0x821bbb30`. The offset is lost here.

The XML parser (`0x821bba08`) then numbers walls with a plain loop counter that starts at 0 for every file:
```
0x821bba98  li   r31, 0
...
0x821bbabc  mr   r4, r31               ; index = position inside this .hitwr file
0x821bbac4  bl   Wall::Init            ; 0x821bbd68
0x821bbac8  addi r31, r31, 1
```
and `Wall::Init` stores it:
```
0x821bbd78  stw  r4, 0x58(r3)          ; the only write to wall->0x58 in the executable
```

### 5. Result

The largest wave in the game is SouthAm `Wave04` with 16 walls. So **no wall ever has an index above 15**. Most themes top out at 9. Every theme needs indices up to at least 63. Bytes 2–19 of every theme's bitfield stay 0 forever, and the check fails at theme 0, byte 1. That's the very first test.

[`scripts/simulate_check.py`](scripts/simulate_check.py) re-implements the check exactly and feeds it every bit the game can set ([output](evidence/simulation_output.txt)):

```
theme             need  walls  max idx set (shipped)  max idx (intended)
Everyday            76     76            9                   75
...
SouthAm             88     88           15                   87
...
shipped game  -> (False, 0, 1)      <- impossible
with offset   -> (True, None, None) <- unlocks if the dropped offset were applied
```

## Answers to the forum theories

- **"Do all solo and co-op walls."** That's the right idea, and it's what the game *meant* to require. The numbering bug makes it unreachable. The report from "Dont Copy Mine" (every wall done, no unlock) is exactly what this code predicts.
- **Holiday / date conditions.** The check reads only the bitfield and the wall-count table. Nothing in the unlock path depends on the date.
- **Unlock other achievements first / finish Quick Survival.** The unlock path has no such requirement. Every mode records walls through the same function, with the same broken indices.
- **Someone on TA once had it.** On an unmodified game that looks impossible. A modded or hacked profile is the more likely explanation.

## Side note: a small out-of-bounds write
`RecordWallPassed` doesn't bounds-check the theme. In Battle mode the theme is 20 (BattleMode, whose `Wave06` has 92 walls). That writes bits at `profile+0x36c…0x377`, just past the 20-theme bitfield. It doesn't affect Contortionist. It's just another sign this code path wasn't tested much.

## Reproducing

Requirements: Python 3 with `cryptography`, gcc, and [libmspack](https://github.com/kyz/libmspack) (only `lzxd.c` is used).

```sh
git clone --depth 1 https://github.com/kyz/libmspack tools/libmspack
gcc -O2 -I tools/libmspack/libmspack/mspack tools/unlzx.c tools/libmspack/libmspack/mspack/lzxd.c -o tools/unlzx

# 1. Executable: XEX2 -> PE image (AES retail key + LZX)
python3 tools/xexdec.py <game>/default.xex default.pe

# 2. Data: 0x0FF512ED XCompress container -> XPR2 -> UTF-8 wave XMLs
python3 tools/xcompress_decode.py <game>/data/data.xpr data.bin
python3 tools/extract_waves.py data.bin waves/

# 3. Run the check
python3 scripts/simulate_check.py waves/

# 4. Disassembly helpers (capstone)
HITW_PE=default.pe python3 -c "import sys; sys.path.insert(0,'tools'); from disasm_helpers import *; pr(0x821bbae0, 48)"
```

No game files are included in this repo.

## Caveats
- This is static analysis of the build in the dump (`default.xex`, media ID `381DB4FA`). Title updates weren't available to examine. Given the unlock statistics, it seems unlikely one fixed this.
- None of this was tested on hardware or an emulator. A good confirmation would be to dump a profile's title-specific save data after playing. Only the low 2 bytes of each 20-byte theme block should ever be non-zero.

## Possible fix (not implemented)
The rounds for a theme sit next to each other in the wall manager (`mgr+0x80 + k*0x1a4`, k = 0..7). A patch could add the wall counts of the earlier rounds to `wall->0x58` before it's recorded. Another option is to make `LoadWave` pass its `r5` through to the parser's starting index. Either one would require a small code cave. This is only useful for emulator or modded play, and it doesn't help on retail Xbox Live.
