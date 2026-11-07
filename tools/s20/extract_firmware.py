#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0
"""Extract the proprietary firmware blobs this kernel embeds from YOUR OWN stock Samsung boot image.

The defconfig builds these blobs into the kernel (CONFIG_EXTRA_FIRMWARE / firmware/Makefile), but
they are Samsung binaries, not GPL source, so they are not shipped in this repository. Samsung's
stock kernel already contains them verbatim; this script copies them out at the offsets listed in
firmware_manifest_<build>.tsv and refuses any blob whose size or SHA-256 does not match.

usage:
  python3 tools/s20/extract_firmware.py <stock boot.img> [manifest.tsv]

Get boot.img from the AP_*.tar.md5 of the matching stock firmware (e.g. G981BXXSNHYB1):
  tar -xf AP_....tar.md5 boot.img.lz4 && lz4 -d boot.img.lz4 boot.img
"""
import hashlib, os, struct, sys

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.abspath(os.path.join(here, '..', '..'))
boot_path = sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__)
manifest = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, 'firmware_manifest_G981BXXSNHYB1.tsv')

b = open(boot_path, 'rb').read()
if b[:8] != b'ANDROID!':
    sys.exit(f'{boot_path}: not an Android boot image (decompress boot.img.lz4 first)')
kernel_size = struct.unpack_from('<I', b, 8)[0]
page = struct.unpack_from('<I', b, 36)[0]
kernel = b[page:page + kernel_size]

ok = True
for line in open(manifest):
    if not line.strip() or line.startswith('#'):
        continue
    rel, off, size, digest = line.split()
    off, size = int(off, 16), int(size)
    blob = kernel[off:off + size]
    if len(blob) != size or hashlib.sha256(blob).hexdigest() != digest:
        print(f'MISMATCH  {rel}  (is this the stock boot.img the manifest was made from?)')
        ok = False
        continue
    dst = os.path.join(root, 'firmware', rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, 'wb') as f:
        f.write(blob)
    print(f'ok        {rel}  {size} bytes')
sys.exit(0 if ok else 1)
