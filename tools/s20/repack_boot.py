#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0
"""Swap the kernel in a Samsung boot image (header v2) and make a vbmeta with AVB verification disabled.

usage: python3 tools/s20/repack_boot.py <stock boot.img> <new Image> <stock vbmeta.img> <out_dir>
then:  (cd <out_dir> && tar -H ustar -cf AP_custom.tar boot.img vbmeta.img)   # flash in Odin's AP slot

boot:   header fields and ramdisk/second/recovery_dtbo/dtb are copied unchanged from the stock image;
        only the kernel section, kernel_size and the header id (AOSP SHA-1 of the sections) change.
        Samsung's signature block and the AVB footer no longer match a modified image, so they are
        dropped; the bare "SEANDROIDENFORCE" marker is appended (as Magisk does on Samsung).
vbmeta: identical to stock except the header flags field (offset 120, big-endian u32) is set to 3
        (HASHTREE_DISABLED | VERIFICATION_DISABLED), equivalent to
        `fastboot --disable-verity --disable-verification flash vbmeta`.
Requires an unlocked bootloader. Keep your stock boot.img + vbmeta.img to roll back.
"""
import hashlib, os, struct, sys

if len(sys.argv) != 5:
    sys.exit(__doc__)

def pad(data, page):
    return data + b'\0' * ((page - len(data) % page) % page)

boot_path, image_path, vbmeta_path, out = sys.argv[1:5]
os.makedirs(out, exist_ok=True)
b = open(boot_path, 'rb').read()
assert b[:8] == b'ANDROID!', 'stock boot is not an Android boot image'
ksz, kaddr, rsz, raddr, ssz, saddr, tags, page, hver, osver = struct.unpack_from('<10I', b, 8)
assert hver == 2, f'expected header v2, got v{hver}'
dtbo_sz, dtbo_off, hdr_sz = struct.unpack_from('<IQI', b, 1632)
dtb_sz, dtb_addr = struct.unpack_from('<IQ', b, 1648)
assert hdr_sz == 1660

def take(offset_pages, size):
    o = offset_pages * page
    return b[o:o + size], offset_pages + (size + page - 1) // page

p = 1
_, p = take(p, ksz)
ramdisk, p = take(p, rsz)
second, p = take(p, ssz)
rdtbo, p = take(p, dtbo_sz)
dtb, p = take(p, dtb_sz)

kernel = open(image_path, 'rb').read()
assert kernel[56:60] == b'ARMd', 'new kernel is not an arm64 Image'

sha = hashlib.sha1()
for blob in (kernel, ramdisk, second, rdtbo, dtb):
    sha.update(blob)
    sha.update(struct.pack('<I', len(blob)))

hdr = bytearray(b[:hdr_sz])
struct.pack_into('<I', hdr, 8, len(kernel))
hdr[576:608] = sha.digest() + b'\0' * 12
out_boot = pad(bytes(hdr), page) + pad(kernel, page) + pad(ramdisk, page) + pad(second, page) \
    + pad(rdtbo, page) + pad(dtb, page) + b'SEANDROIDENFORCE'
open(os.path.join(out, 'boot.img'), 'wb').write(out_boot)
print(f'boot.img: {len(out_boot)} bytes, kernel {ksz} -> {len(kernel)}, ramdisk {rsz} + dtb {dtb_sz} kept')

v = bytearray(open(vbmeta_path, 'rb').read())
assert v[:4] == b'AVB0', 'stock vbmeta lacks AVB0 magic'
struct.pack_into('>I', v, 120, 3)
open(os.path.join(out, 'vbmeta.img'), 'wb').write(v)
print('vbmeta.img: flags -> 3 (verity + verification disabled)')
