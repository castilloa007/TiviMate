#!/usr/bin/env python3
"""Debug: scan binary manifest for LaunchActivity attribute reference."""
import zipfile, struct

APK_IN = "/Users/alfonsocastillo/Documents/github/TiviMate/TiviMate 5.1.6 __BannerM0d_Spydog.apk"

def u32(b, o): return struct.unpack_from('<I', b, o)[0]
def u16(b, o): return struct.unpack_from('<H', b, o)[0]

with zipfile.ZipFile(APK_IN, 'r') as z:
    data = bytearray(z.read('AndroidManifest.xml'))

# String pool
sp_size   = u32(data, 12)
count     = u32(data, 16)
flags     = u32(data, 24)
str_start = u32(data, 28)
is_utf8   = bool(flags & (1 << 8))
print(f"SP: size={sp_size}, count={count}, is_utf8={is_utf8}, str_start={str_start}")

offsets = [u32(data, 36 + i*4) for i in range(count)]
base = 8 + str_start

strings = []
for off in offsets:
    pos = base + off
    sl = u16(data, pos)
    if sl & 0x8000: sl = ((sl & 0x7FFF) << 16) | u16(data, pos+2); pos += 2
    pos += 2
    strings.append(data[pos:pos+sl*2].decode('utf-16-le', errors='replace'))

launch_idx = next(i for i,s in enumerate(strings) if s == 'com.andyhax.haxsplash.LaunchActivity')
print(f"LaunchActivity index: {launch_idx}")

# Scan body
body_start = 8 + sp_size
pos = body_start
print(f"Body starts at: {body_start:#x}")

while pos < len(data) - 8:
    chunk_type = u16(data, pos)
    chunk_size = u16(data, pos + 2)
    if chunk_size == 0: break

    if chunk_type == 0x0102:  # START_ELEMENT
        elem_name = u32(data, pos + 16)
        attr_start= u16(data, pos + 20)
        attr_size = u16(data, pos + 22)
        attr_count= u16(data, pos + 24)

        for i in range(attr_count):
            ap = pos + attr_start + i * attr_size
            a_ns     = u32(data, ap)
            a_name   = u32(data, ap + 4)
            a_raw    = u32(data, ap + 8)
            # offset 12 = value size (uint16), offset 14 = res0 (byte), offset 15 = dataType (byte), offset 16 = data (uint32)
            a_vsize  = u16(data, ap + 12)
            a_res0   = data[ap + 14]
            a_dtype  = data[ap + 15]
            a_data   = u32(data, ap + 16)

            if a_dtype == 0x03 and a_data == launch_idx:
                print(f"\n*** FOUND LaunchActivity ref at attr_pos={ap:#x}")
                print(f"    elem chunk at {pos:#x}, line {u32(data, pos+4)}")
                print(f"    a_ns={a_ns}, a_name={a_name}, a_raw={a_raw}, a_dtype={a_dtype:#x}, a_data={a_data}")
                elem_name_str = strings[elem_name] if elem_name < len(strings) else f"?{elem_name}"
                print(f"    element name: [{elem_name}] {elem_name_str}")
                if a_name < len(strings): print(f"    attr name: [{a_name}] {strings[a_name]}")
            elif a_data == launch_idx:
                print(f"  (non-string ref to launch_idx at {ap:#x}, dtype={a_dtype:#x})")

    pos += chunk_size

print("Scan complete.")
