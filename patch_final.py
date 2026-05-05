#!/usr/bin/env python3
"""
Final TiviMate APK patcher:
 1. Add ServiceSelectorActivity to manifest string pool
 2. Replace LaunchActivity android:name attr with ServiceSelectorActivity
 3. Inject classes3.dex
 4. Output modified_unsigned.apk (needs signing)
"""
import zipfile, struct, os

APK_IN  = "/Users/alfonsocastillo/Documents/github/TiviMate/TiviMate 5.1.6 __BannerM0d_Spydog.apk"
DEX3    = "/Users/alfonsocastillo/Documents/github/TiviMate/inject_src/classes3.dex"
APK_OUT = "/Users/alfonsocastillo/Documents/github/TiviMate/modified_unsigned.apk"

def u32(b, o): return struct.unpack_from('<I', b, o)[0]
def u16(b, o): return struct.unpack_from('<H', b, o)[0]
def s32(ba, o, v): ba[o:o+4] = struct.pack('<I', v)
def s16(ba, o, v): ba[o:o+2] = struct.pack('<H', v)

# ── Parse string pool ─────────────────────────────────────────────────────────
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

# ── Add string to UTF-16 string pool ─────────────────────────────────────────
def add_string_to_pool(ba, new_str):
    count     = u32(ba, 16)
    sp_size   = u32(ba, 12)
    str_start = u32(ba, 28)
    xml_size  = u32(ba, 4)
    is_utf8   = bool(u32(ba, 24) & (1 << 8))
    assert not is_utf8, "UTF-8 pool not supported"

    offsets = [u32(ba, 36 + i*4) for i in range(count)]
    base    = 8 + str_start

    # Find last string end offset (relative to base)
    last_end = 0
    for off in offsets:
        pos = base + off
        sl = u16(ba, pos)
        if sl & 0x8000: sl = ((sl & 0x7FFF) << 16) | u16(ba, pos+2); pos += 2
        end = pos + 2 + sl*2 + 2 - base
        if end > last_end: last_end = end

    new_off  = last_end
    enc      = new_str.encode('utf-16-le')
    new_blob = struct.pack('<H', len(new_str)) + enc + b'\x00\x00'

    # 1. Insert string blob into string data section
    str_ins = 8 + str_start + new_off
    ba[str_ins:str_ins] = new_blob

    # 2. Insert new offset entry at end of offset table
    off_ins = 36 + count * 4
    ba[off_ins:off_ins] = struct.pack('<I', new_off)

    delta = 4 + len(new_blob)   # 4 (offset entry) + string bytes

    # 3. Update fields (str_start shifts by 4 due to new offset entry)
    s32(ba, 16, count + 1)
    s32(ba, 28, str_start + 4)
    s32(ba, 12, sp_size + delta)
    s32(ba, 4,  xml_size + delta)

    return count, delta   # new_index, bytes_added

# ── Patch body: swap launch_idx → selector_idx ────────────────────────────────
def patch_body(ba, launch_idx, selector_idx):
    sp_size    = u32(ba, 12)
    body_start = 8 + sp_size
    pos        = body_start
    total      = len(ba)
    patches    = 0

    while pos < total - 8:
        chunk_type  = u16(ba, pos)
        chunk_total = u32(ba, pos + 4)   # ← correct: total size
        if chunk_total == 0 or chunk_total > 0x200000: break

        if chunk_type == 0x0102:   # START_ELEMENT
            # ResXMLTree_node (16 bytes) + ResXMLTree_attrExt
            # lineNo  at pos+8
            # attrExt starts at pos+16:  ns(4) name(4) attrStart(2) attrSize(2) attrCount(2)
            elem_name  = u32(ba, pos + 20)
            attr_start = u16(ba, pos + 24)
            attr_size  = u16(ba, pos + 26)
            attr_count = u16(ba, pos + 28)

            for i in range(attr_count):
                ap      = pos + 16 + attr_start + i * attr_size
                a_dtype = ba[ap + 15]
                a_data  = u32(ba, ap + 16)

                if a_dtype == 0x03 and a_data == launch_idx:
                    s32(ba, ap + 8,  selector_idx)   # rawValue
                    s32(ba, ap + 16, selector_idx)   # data
                    line_no = u32(ba, pos + 8)
                    print(f"  Patched attr at {ap:#x} (chunk {pos:#x} line {line_no})")
                    patches += 1

        pos += chunk_total

    return patches

# ══ MAIN ═════════════════════════════════════════════════════════════════════
with zipfile.ZipFile(APK_IN, 'r') as z:
    manifest_bytes = z.read('AndroidManifest.xml')

ba = bytearray(manifest_bytes)

strings, _ = parse_strings(bytes(ba))
launch_idx = next(i for i,s in enumerate(strings) if s == 'com.andyhax.haxsplash.LaunchActivity')
print(f"LaunchActivity index: {launch_idx} ({len(strings)} strings)")

selector_idx, delta = add_string_to_pool(ba, 'com.andyhax.haxsplash.ServiceSelectorActivity')
print(f"Added ServiceSelectorActivity at index {selector_idx}, delta={delta}")

# Verify
strings2, _ = parse_strings(bytes(ba))
assert strings2[selector_idx] == 'com.andyhax.haxsplash.ServiceSelectorActivity', "verify failed"
print("Pool verified OK")

n = patch_body(ba, launch_idx, selector_idx)
print(f"Patched {n} attribute(s)")
if n == 0:
    print("WARNING: No patches applied — APK will not work as intended!")

patched_manifest = bytes(ba)
print(f"Manifest: {len(manifest_bytes)} → {len(patched_manifest)} bytes")

# ── Write output APK ─────────────────────────────────────────────────────────
if os.path.exists(APK_OUT): os.remove(APK_OUT)

with zipfile.ZipFile(APK_IN, 'r') as zin, \
     zipfile.ZipFile(APK_OUT, 'w', compression=zipfile.ZIP_STORED) as zout:
    for item in zin.infolist():
        name = item.filename
        if name == 'AndroidManifest.xml':
            zout.writestr(item, patched_manifest)
            print(f"  replaced AndroidManifest.xml")
        elif name == 'classes3.dex':
            print(f"  skipping existing classes3.dex")
        else:
            zout.writestr(item, zin.read(name))
    zout.write(DEX3, 'classes3.dex')
    print(f"  added classes3.dex ({os.path.getsize(DEX3)} bytes)")

print(f"\nOutput: {APK_OUT}")
print("Next: sign with apksigner")
