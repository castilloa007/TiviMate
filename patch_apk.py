#!/usr/bin/env python3
"""
Patch TiviMate APK:
 1. Replace LaunchActivity's LAUNCHER intent-filter with ServiceSelectorActivity
 2. Add ServiceSelectorActivity declaration
 3. Inject classes3.dex
 4. Output unsigned modified.apk ready for signing
"""
import zipfile, struct, shutil, os, sys

APK_IN  = "/Users/alfonsocastillo/Documents/github/TiviMate/TiviMate 5.1.6 __BannerM0d_Spydog.apk"
DEX3    = "/Users/alfonsocastillo/Documents/github/TiviMate/inject_src/classes3.dex"
APK_OUT = "/Users/alfonsocastillo/Documents/github/TiviMate/modified_unsigned.apk"

# ── helpers ──────────────────────────────────────────────────────────────────
def u32(b, o): return struct.unpack_from('<I', b, o)[0]
def u16(b, o): return struct.unpack_from('<H', b, o)[0]
def pack32(v): return struct.pack('<I', v)
def pack16(v): return struct.pack('<H', v)

def set_u32(ba, o, v): ba[o:o+4] = struct.pack('<I', v)
def set_u16(ba, o, v): ba[o:o+2] = struct.pack('<H', v)

# ── parse string pool ─────────────────────────────────────────────────────────
def parse_strings(data):
    sp_type   = u32(data, 8)
    sp_size   = u32(data, 12)
    count     = u32(data, 16)
    flags     = u32(data, 24)
    str_start = u32(data, 28)     # relative to string-pool chunk start (offset 8)
    is_utf8   = bool(flags & (1 << 8))

    offsets = [u32(data, 36 + i*4) for i in range(count)]
    base    = 8 + str_start       # absolute

    strings = []
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

# ── encode one UTF-16 string for the pool ────────────────────────────────────
def encode_utf16_str(s):
    enc = s.encode('utf-16-le')
    length = len(s)
    # length prefix as uint16, then chars, then null uint16
    return struct.pack('<H', length) + enc + b'\x00\x00'

# ── add a new string to the string pool and return its index ─────────────────
def add_string_to_pool(manifest_ba, new_str):
    """Inserts new_str into the string pool and returns its new index.
    Updates all relevant size/count fields in place."""
    count     = u32(manifest_ba, 16)
    flags     = u32(manifest_ba, 24)
    str_start = u32(manifest_ba, 28)    # relative to sp chunk (offset 8)
    sp_size   = u32(manifest_ba, 12)
    xml_size  = u32(manifest_ba, 4)
    is_utf8   = bool(flags & (1 << 8))

    assert not is_utf8, "UTF-8 string pools not supported in this patcher"

    new_encoded = encode_utf16_str(new_str)
    new_len     = len(new_encoded)

    # Current end of offset table = 36 + count*4
    # Current start of strings data (absolute) = 8 + str_start
    offsets = [u32(manifest_ba, 36 + i*4) for i in range(count)]

    # New string offset = after the last string
    # Find last string's end
    base = 8 + str_start
    last_str_end = 0
    for off in offsets:
        pos = base + off
        sl = u16(manifest_ba, pos)
        if sl & 0x8000: sl = ((sl & 0x7FFF) << 16) | u16(manifest_ba, pos+2); pos += 2
        end = pos + 2 + sl*2 + 2   # after null terminator
        last_str_end = max(last_str_end, end - base)

    new_str_offset = last_str_end   # offset within string data

    # We need to insert:
    #   1. One new uint32 offset entry in the offset table  (+4 bytes)
    #   2. The new encoded string in the string data block  (+new_len bytes)
    # Both inserts shift subsequent data.

    # Offset table entry insert position (absolute): 36 + count*4
    offset_table_insert_pos = 36 + count * 4

    # String data insert position (absolute): base + new_str_offset
    # But after we insert the offset table entry, positions shift by 4
    # So we do them in reverse order to keep indices valid

    # Step 1: insert new string into string data
    # Its absolute position BEFORE the offset-table insert = 8 + str_start + new_str_offset
    # After inserting 4 bytes for the offset entry (which comes BEFORE string data), add 4
    str_insert_abs = (8 + str_start + new_str_offset) + 4   # +4 for the upcoming offset entry

    # Actually, let's insert in order: first string data (doesn't affect offset table positions),
    # then offset entry.

    str_insert_abs_now = 8 + str_start + new_str_offset
    manifest_ba[str_insert_abs_now:str_insert_abs_now] = new_encoded

    # Step 2: insert offset entry (new string's offset) at end of offset table
    new_offset_entry = struct.pack('<I', new_str_offset)
    manifest_ba[offset_table_insert_pos:offset_table_insert_pos] = new_offset_entry

    # Step 3: update counts and sizes
    # string count += 1
    set_u32(manifest_ba, 16, count + 1)
    # str_start: the offset table grew by 4, so str_start also shifts by 4
    set_u32(manifest_ba, 28, str_start + 4)
    # sp_size grows by 4 (offset entry) + new_len (string data)
    set_u32(manifest_ba, 12, sp_size + 4 + new_len)
    # xml total size grows by same
    set_u32(manifest_ba, 4, xml_size + 4 + new_len)

    # The new string's index
    new_index = count
    return new_index, 4 + new_len   # (index, bytes_added)

# ── patch intent-filter attribute in manifest body ───────────────────────────
def patch_manifest_body(manifest_ba, launch_idx, selector_idx, bytes_added):
    """After string pool changes, body XML references shift.
    Scan START_ELEMENT tags looking for android:name attribute with value=launch_idx
    that appears near android.intent.action.MAIN.
    Then change that value to selector_idx.

    Binary XML element format:
      0x0102 type (2), size (2), lineNo (4), comment (4), ns (4), name (4),
      attrStart (2), attrSize (2), attrCount (2), idIdx (2), classIdx (2), styleIdx (2)
      then attrCount * (ns(4), name(4), rawVal(4), valueType(2+2), data(4))
    """
    sp_size = u32(manifest_ba, 12)
    sp_start_abs = 8   # string pool starts at offset 8
    # Body starts after the string pool chunk
    body_start = sp_start_abs + sp_size
    body_start += bytes_added   # account for our additions (already reflected in sp_size)
    # Actually sp_size is already updated, so body_start = 8 + sp_size
    body_start = 8 + u32(manifest_ba, 12)

    pos = body_start
    total = len(manifest_ba)

    ANDROID_NS_HASH = None
    found_main = False
    target_pos = None

    while pos < total - 8:
        chunk_type = u16(manifest_ba, pos)
        chunk_size = u16(manifest_ba, pos + 2)
        if chunk_size == 0: break

        if chunk_type == 0x0102:  # START_ELEMENT
            line_no  = u32(manifest_ba, pos + 4)
            elem_ns  = u32(manifest_ba, pos + 12)
            elem_name= u32(manifest_ba, pos + 16)
            attr_start= u16(manifest_ba, pos + 20)
            attr_size = u16(manifest_ba, pos + 22)
            attr_count= u16(manifest_ba, pos + 24)

            attrs = []
            for i in range(attr_count):
                ap = pos + attr_start + i * attr_size
                a_ns   = u32(manifest_ba, ap)
                a_name = u32(manifest_ba, ap + 4)
                a_raw  = u32(manifest_ba, ap + 8)
                a_type = u16(manifest_ba, ap + 12)
                a_data = u32(manifest_ba, ap + 16)
                attrs.append((ap, a_ns, a_name, a_raw, a_type, a_data))

            for ap, a_ns, a_name, a_raw, a_type, a_data in attrs:
                # Look for android:name attribute (name index in pool) with value = launch_idx
                # android:name is a well-known attribute; we identify it by the string value
                if a_data == launch_idx and a_type == 0x03:  # TYPE_STRING
                    # Found! Replace with selector_idx
                    set_u32(manifest_ba, ap + 8, selector_idx)   # rawValue
                    set_u32(manifest_ba, ap + 16, selector_idx)  # data
                    print(f"  Patched android:name at attr offset {ap:#x} line {line_no}")

        pos += chunk_size

# ══ MAIN ═════════════════════════════════════════════════════════════════════
with zipfile.ZipFile(APK_IN, 'r') as z:
    manifest_bytes = z.read('AndroidManifest.xml')

manifest_ba = bytearray(manifest_bytes)

strings, is_utf8 = parse_strings(bytes(manifest_ba))
print(f"String pool: {len(strings)} strings, utf8={is_utf8}")

# Print relevant strings
for i, s in enumerate(strings):
    if any(x in s for x in ['LaunchActivity', 'MainActivity', 'ServiceSelector', 'haxsplash']):
        print(f"  [{i:4d}] {s}")

# Find LaunchActivity index
launch_idx = next(i for i, s in enumerate(strings) if s == 'com.andyhax.haxsplash.LaunchActivity')
print(f"\nLaunchActivity string index: {launch_idx}")

# Add ServiceSelectorActivity string
print("Adding ServiceSelectorActivity string to pool...")
selector_idx, bytes_added = add_string_to_pool(manifest_ba, 'com.andyhax.haxsplash.ServiceSelectorActivity')
print(f"ServiceSelectorActivity index: {selector_idx}, bytes added: {bytes_added}")

# Verify it was added
strings2, _ = parse_strings(bytes(manifest_ba))
print(f"New string count: {len(strings2)}")
print(f"New string at [{selector_idx}]: {strings2[selector_idx]}")

# Patch manifest body: replace LaunchActivity name reference with ServiceSelectorActivity
print("Patching manifest body...")
patch_manifest_body(manifest_ba, launch_idx, selector_idx, bytes_added)

# Write patched manifest
patched_manifest = bytes(manifest_ba)
print(f"Patched manifest size: {len(patched_manifest)} (was {len(manifest_bytes)})")

# Build new APK: copy original, replace AndroidManifest.xml, add classes3.dex
print(f"\nBuilding {APK_OUT}...")
shutil.copy2(APK_IN, APK_OUT)

with zipfile.ZipFile(APK_OUT, 'a') as z:
    # Replace manifest (add overwrites)
    z.writestr('AndroidManifest.xml', patched_manifest)
    # Add classes3.dex
    with open(DEX3, 'rb') as f:
        z.writestr('classes3.dex', f.read())

print("Done! Output:", APK_OUT)
