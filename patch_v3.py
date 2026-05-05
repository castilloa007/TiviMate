#!/usr/bin/env python3
"""
TiviMate APK patcher v3:
 - Patch AndroidManifest.xml (binary): replace LaunchActivity with ServiceSelectorActivity
 - Strip old META-INF V1 signatures (CERT.RSA/SF/MANIFEST.MF)
 - Inject classes3.dex
 - Preserve all other entries with original compression (no re-compress)
 - Output modified_unsigned.apk ready for zipalign + sign
"""
import zipfile, struct, os

APK_IN  = "/Users/alfonsocastillo/Documents/github/TiviMate/TiviMate 5.1.6 __BannerM0d_Spydog.apk"
DEX3    = "/Users/alfonsocastillo/Documents/github/TiviMate/inject_src/classes3.dex"
APK_OUT = "/Users/alfonsocastillo/Documents/github/TiviMate/modified_unsigned.apk"

STRIP   = {'META-INF/CERT.RSA', 'META-INF/CERT.SF', 'META-INF/MANIFEST.MF'}

def u32(b, o): return struct.unpack_from('<I', b, o)[0]
def u16(b, o): return struct.unpack_from('<H', b, o)[0]
def s32(ba, o, v): ba[o:o+4] = struct.pack('<I', v)

def parse_strings(data):
    count     = u32(data, 16)
    flags     = u32(data, 24)
    str_start = u32(data, 28)
    is_utf8   = bool(flags & (1 << 8))
    offsets   = [u32(data, 36 + i*4) for i in range(count)]
    base      = 8 + str_start
    strings   = []
    for off in offsets:
        pos = base + off
        if is_utf8:
            cl = data[pos] & 0x7F
            if data[pos] & 0x80: cl = ((cl & 0x3F) << 8) | data[pos+1]; pos += 1
            pos += 1
            bl = data[pos] & 0x7F
            if data[pos] & 0x80: bl = ((bl & 0x3F) << 8) | data[pos+1]; pos += 1
            pos += 1
            strings.append(data[pos:pos+bl].decode('utf-8', errors='replace'))
        else:
            sl = u16(data, pos)
            if sl & 0x8000: sl = ((sl & 0x7FFF) << 16) | u16(data, pos+2); pos += 2
            pos += 2
            strings.append(data[pos:pos+sl*2].decode('utf-16-le', errors='replace'))
    return strings, is_utf8

def add_string_to_pool(ba, new_str):
    count     = u32(ba, 16)
    sp_size   = u32(ba, 12)
    str_start = u32(ba, 28)
    xml_size  = u32(ba, 4)
    assert not bool(u32(ba, 24) & (1 << 8)), "UTF-8 pool not supported"

    offsets = [u32(ba, 36 + i*4) for i in range(count)]
    base    = 8 + str_start
    last_end = 0
    for off in offsets:
        pos = base + off
        sl = u16(ba, pos)
        if sl & 0x8000: sl = ((sl & 0x7FFF) << 16) | u16(ba, pos+2); pos += 2
        end = pos + 2 + sl*2 + 2 - base
        if end > last_end: last_end = end

    new_off  = last_end
    raw = struct.pack('<H', len(new_str)) + new_str.encode('utf-16-le') + b'\x00\x00'
    # Pad to 4-byte boundary so string pool chunk size stays aligned
    pad = (4 - (len(raw) % 4)) % 4
    new_blob = raw + b'\x00' * pad

    str_ins = 8 + str_start + new_off
    ba[str_ins:str_ins] = new_blob
    off_ins = 36 + count * 4
    ba[off_ins:off_ins] = struct.pack('<I', new_off)

    delta = 4 + len(new_blob)
    s32(ba, 16, count + 1)
    s32(ba, 28, str_start + 4)
    s32(ba, 12, sp_size + delta)
    s32(ba, 4,  xml_size + delta)
    return count, delta

def patch_body(ba, launch_idx, selector_idx):
    sp_size    = u32(ba, 12)
    body_start = 8 + sp_size
    pos        = body_start
    patches    = 0
    while pos < len(ba) - 8:
        chunk_type  = u16(ba, pos)
        chunk_total = u32(ba, pos + 4)
        if chunk_total == 0 or chunk_total > 0x200000: break
        if chunk_type == 0x0102:
            attr_start = u16(ba, pos + 24)
            attr_size  = u16(ba, pos + 26)
            attr_count = u16(ba, pos + 28)
            for i in range(attr_count):
                ap = pos + 16 + attr_start + i * attr_size
                if ba[ap + 15] == 0x03 and u32(ba, ap + 16) == launch_idx:
                    s32(ba, ap + 8,  selector_idx)
                    s32(ba, ap + 16, selector_idx)
                    patches += 1
        pos += chunk_total
    return patches

# ── Patch manifest ────────────────────────────────────────────────────────────
with zipfile.ZipFile(APK_IN, 'r') as z:
    manifest_bytes = z.read('AndroidManifest.xml')

ba = bytearray(manifest_bytes)
strings, _ = parse_strings(bytes(ba))
launch_idx = next(i for i,s in enumerate(strings) if s == 'com.andyhax.haxsplash.LaunchActivity')
selector_idx, delta = add_string_to_pool(ba, 'com.andyhax.haxsplash.ServiceSelectorActivity')
strings2, _ = parse_strings(bytes(ba))
assert strings2[selector_idx] == 'com.andyhax.haxsplash.ServiceSelectorActivity'
n = patch_body(ba, launch_idx, selector_idx)
print(f"Manifest patched: {n} attr(s), {len(manifest_bytes)}→{len(ba)} bytes")
assert n > 0, "No patches applied!"
patched_manifest = bytes(ba)

# ── Build output APK (verbatim copy, no re-compress, strip old sigs) ──────────
if os.path.exists(APK_OUT): os.remove(APK_OUT)

with zipfile.ZipFile(APK_IN, 'r') as zin, \
     zipfile.ZipFile(APK_OUT, 'w') as zout:
    for item in zin.infolist():
        name = item.filename
        if name in STRIP:
            print(f"  stripped  {name}")
            continue
        if name == 'AndroidManifest.xml':
            zout.writestr(item, patched_manifest)
            print(f"  replaced  {name}")
        elif name == 'classes3.dex':
            print(f"  skipped   {name} (will add ours)")
        else:
            # Copy verbatim WITHOUT decompressing (preserves original compression)
            buf = zin.read(name)
            zout.writestr(item, buf)
    zout.write(DEX3, 'classes3.dex', compress_type=zipfile.ZIP_STORED)
    print(f"  added     classes3.dex")

print(f"\nOutput: {APK_OUT}")
