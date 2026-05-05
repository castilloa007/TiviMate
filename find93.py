#!/usr/bin/env python3
"""Find all occurrences of value 93 (LaunchActivity index) in body."""
import zipfile, struct

APK_IN = "/Users/alfonsocastillo/Documents/github/TiviMate/TiviMate 5.1.6 __BannerM0d_Spydog.apk"

def u32(b, o): return struct.unpack_from('<I', b, o)[0]
def u16(b, o): return struct.unpack_from('<H', b, o)[0]

with zipfile.ZipFile(APK_IN, 'r') as z:
    data = bytearray(z.read('AndroidManifest.xml'))

sp_size = u32(data, 12)
body_start = 8 + sp_size

# Find all uint32 = 93 (0x5d) in body
target = struct.pack('<I', 93)
pos = body_start
while True:
    idx = bytes(data).find(target, pos)
    if idx == -1: break
    # print context
    ctx_start = max(body_start, idx-16)
    ctx = data[ctx_start:idx+20]
    print(f"Found at offset {idx:#x}: ...{ctx.hex()}...")
    pos = idx + 1

print("Done.")
