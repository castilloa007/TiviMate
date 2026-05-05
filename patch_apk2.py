#!/usr/bin/env python3
"""
Patch TiviMate APK:
 1. Add ServiceSelectorActivity string to manifest string pool
 2. Replace LaunchActivity's android:name attribute with ServiceSelectorActivity
 3. Add classes3.dex
 4. Output unsigned modified_unsigned.apk
"""
import zipfile, struct, shutil, os, io

APK_IN  = "/Users/alfonsocastillo/Documents/github/TiviMate/TiviMate 5.1.6 __BannerM0d_Spydog.apk"
DEX3    = "/Users/alfonsocastillo/Documents/github/TiviMate/inject_src/classes3.dex"
APK_OUT = "/Users/alfonsocastillo/Documents/github/TiviMate/modified_unsigned.apk"

def u32(b, o): return struct.unpack_from('<I', b, o)[0]
def u16(b, o): return struct.unpack_from('<H', b, o)[0]
def set_u32(ba, o, v): ba[o:o+4] = struct.pack('<I', v)
def set_u16(ba, o, v): ba[o:o+2] = struct.pack('<H', v)

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
    assert not is_utf8, "UTF-8 pools not supported"

    offsets = [u32(ba, 36 + i*4) for i in range(count)]
    base    = 8 + str_start

    # Find end of last string
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

    # Insert string blob BEFORE inserting offset entry, to avoid double-shifting
    str_ins_abs = 8 + str_start + new_off
    ba[str_ins_abs:str_ins_abs] = new_blob

    # Insert offset entry at end of offset table
    off_ins_abs = 36 + count * 4
    ba[off_ins_abs:off_ins_abs] = struct.pack('<I', new_off)

    # Update fields
    set_u32(ba, 16, count + 1)            # string count
    set_u32(ba, 28, str_start + 4)        # str_start shifts by 4 (new offset entry)
    delta = 4 + len(new_blob)
    set_u32(ba, 12, sp_size + delta)      # string pool chunk size
    set_u32(ba, 4,  xml_size + delta)     # total XML size

    return count, delta  # new index, bytes added

# ── Patch body: replace launch_idx refs with selector_idx ────────────────────
def patch_body_refs(ba, launch_idx, selector_idx):
    sp_size    = u32(ba, 12)
    body_start = 8 + sp_size
    pos        = body_start
    total      = len(ba)
    patches    = 0

    while pos < total - 8:
        chunk_type = u16(ba, pos)
        chunk_size = u16(ba, pos + 2)
        if chunk_size == 0: break

        if chunk_type == 0x0102:  # START_ELEMENT
            attr_start = u16(ba, pos + 20)
            attr_size  = u16(ba, pos + 22)
            attr_count = u16(ba, pos + 24)

            for i in range(attr_count):
                ap      = pos + attr_start + i * attr_size
                a_dtype = ba[ap + 15]       # dataType byte
                a_data  = u32(ba, ap + 16)  # data uint32

                if a_dtype == 0x03 and a_data == launch_idx:
                    # rawValue (ap+8) and data (ap+16) both hold string index
                    set_u32(ba, ap + 8,  selector_idx)
                    set_u32(ba, ap + 16, selector_idx)
                    print(f"  Patched attr at {ap:#x} (line {u32(ba, pos+4)})")
                    patches += 1

        pos += chunk_size

    print(f"Total patches: {patches}")
    return patches

# ══ MAIN ═════════════════════════════════════════════════════════════════════
with zipfile.ZipFile(APK_IN, 'r') as z:
    manifest_bytes = z.read('AndroidManifest.xml')

ba = bytearray(manifest_bytes)

strings, _ = parse_strings(bytes(ba))
launch_idx = next(i for i,s in enumerate(strings) if s == 'com.andyhax.haxsplash.LaunchActivity')
print(f"LaunchActivity index: {launch_idx} ({len(strings)} total strings)")

selector_idx, delta = add_string_to_pool(ba, 'com.andyhax.haxsplash.ServiceSelectorActivity')
print(f"ServiceSelectorActivity index: {selector_idx}, delta: {delta} bytes")

# Verify
strings2, _ = parse_strings(bytes(ba))
assert strings2[selector_idx] == 'com.andyhax.haxsplash.ServiceSelectorActivity'
assert strings2[launch_idx]   == 'com.andyhax.haxsplash.LaunchActivity'
print("String pool verification OK")

patch_body_refs(ba, launch_idx, selector_idx)

patched_manifest = bytes(ba)
print(f"Manifest: {len(manifest_bytes)} -> {len(patched_manifest)} bytes")

# ── Build output APK (no duplicates) ─────────────────────────────────────────
print(f"\nBuilding {APK_OUT}...")
if os.path.exists(APK_OUT): os.remove(APK_OUT)

with zipfile.ZipFile(APK_IN, 'r') as zin, zipfile.ZipFile(APK_OUT, 'w', compression=zipfile.ZIP_STORED) as zout:
    for item in zin.infolist():
        if item.filename == 'AndroidManifest.xml':
            zout.writestr(item, patched_manifest)
        elif item.filename == 'classes3.dex':
            pass  # will add our own
        else:
            zout.writestr(item, zin.read(item.filename))

    # Add classes3.dex
    with open(DEX3, 'rb') as f:
        zout.write(DEX3, 'classes3.dex')

print("Done:", APK_OUT)
