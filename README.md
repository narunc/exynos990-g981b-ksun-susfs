# exynos990-g981b-ksun-susfs

**KernelSU-Next (legacy, v3.4.0-legacy / 33316) + SuSFS v2.0.0 for the Samsung Galaxy S20 5G (SM-G981B, Exynos 990).**
Stock Samsung kernel source (Linux 4.19.87, One UI 5.1 / Android 13), no custom ROM required.

Based on [enchantedglycerin/exynos990-KernelSU-Next-SuSFS](https://github.com/enchantedglycerin/exynos990-KernelSU-Next-SuSFS)
(KernelSU-Next v3.1.0-legacy + SuSFS v2.0.0). This tree moves the driver to the current KernelSU-Next
`legacy` branch and ports the SuSFS glue onto it.

> ⚠️ **Use at your own risk.** Unlocking the bootloader wipes the phone and permanently trips Knox
> (Samsung Wallet/Pay, Secure Folder and some banking apps stop working). Not affiliated with or
> endorsed by Samsung or the KernelSU-Next project.

## Status

| Model | `build.sh -m` | Status |
|:--|:--|:--|
| Galaxy S20 5G (SM-G981B) | `g981b` | ✅ **Boots**: G981BXXSNHYB1, manager shows *Working*, Manual hooks, SuSFS v2.0.0, modules + Zygisk Next work |
| S20+ (G985F), S20 (G980F), S20+ 5G (G986B), S20 Ultra (G988B) | `g985f` / `g980f` / `g986b` / `g988b` | ⚠️ Builds; not tested with this KernelSU-Next version |

Use with the official **KernelSU-Next manager v3.4.2** (`KernelSU_Next_v3.4.2_33355-release.apk`), which speaks
manager UAPI 5. Not for Snapdragon variants; Android 14+ is unsupported.

## What changed from upstream

* `KernelSU-Next/`: vendored KernelSU-Next **legacy** branch at `465490a2` (v3.4.0-legacy + 21 commits,
  including the fix "never sleep while holding the policy rwlock write side"), plus the patches in
  `KernelSU-Next/s20-patches/`:
  1. **SuSFS v2.0.0 (non-GKI) glue** ported from the 3.1.0 tree onto the new driver layout
     (`core/init.c`, `hook/setuid_hook.c`, `selinux/*`, `supercall/*`, `Kconfig`, `Kbuild`).
     SuSFS SIDs are now cached *after* the SELinux policy write lock is released.
  2. **`strscpy_pad` detection**: Samsung's 4.19.87 lacks `strscpy_pad()` even though its version number is
     above 4.14.222; Kbuild now detects the function instead of trusting `LINUX_VERSION_CODE`.
  See `KernelSU-Next/UPSTREAM.txt` for why the base stops before *module preinit* (UAPI 6).
* `security/selinux/hooks.c`: the `selinux_cred()` accessor rewrite that KernelSU-Next's Kbuild applies at
  build time, committed so a fresh clone builds identically.
* `build.sh`: pins the KernelSU-Next version (the vendored copy isn't a git repo) and checks firmware blobs.
* `tools/s20/`: firmware extraction from your stock image, and stock `boot.img` repacking for Odin.

## Build

```sh
# 1. Toolchain: AOSP Clang r370808 (10.0.1) + GCC 4.9 at ../tc/clang10 and ../tc/gcc49
#    (or export CLANG_DIR / GCC_DIR).  DO NOT use Clang 14+ (bootloops Exynos 990).
#    Host packages (Ubuntu): git make bc bison flex libssl-dev libelf-dev python3 zip lz4 cpio

# 2. Samsung firmware blobs (NPU, touchscreen, wireless charging, side key) are built into the kernel
#    but are proprietary, so they are NOT in this repo. Extract them from YOUR stock firmware
#    (AP_G981BXXSNHYB1_...tar.md5 -> boot.img.lz4); every blob is size- and SHA-256-checked:
tar -xf AP_G981B*.tar.md5 boot.img.lz4 vbmeta.img.lz4 && lz4 -d boot.img.lz4 && lz4 -d vbmeta.img.lz4
python3 tools/s20/extract_firmware.py boot.img

# 3. Build
./build.sh -m g981b            # -> out_g981b/arch/arm64/boot/Image
```

## Flash

Requires an **unlocked bootloader** (Developer options → OEM unlocking, then long-press Vol Up in
Download mode). In Download mode check **KG STATE is not `Prenormal`**.

**Option A: Odin, no custom recovery (tested).** Repack your stock boot image with the new kernel.
Samsung's ramdisk, device tree and command line are kept, and `vbmeta` verification is disabled:

```sh
python3 tools/s20/repack_boot.py boot.img out_g981b/arch/arm64/boot/Image vbmeta.img odin/
(cd odin && tar -H ustar -cf ../AP_G981B_KSUNext.tar boot.img vbmeta.img)
```

Flash `AP_G981B_KSUNext.tar` in Odin's **AP** slot (leave BL/CP/CSC empty). Data is kept.
**Rollback:** tar your stock `boot.img` + `vbmeta.img` the same way and flash that in AP.

**Option B: AnyKernel3 zip** (TWRP / OrangeFox, or the zip from Releases):

```sh
./mkzip.sh -m g981b            # -> AnyKernel3_KSUNext_SUSFS_G981B_S20_5G_EXPERIMENTAL.zip
```

The zip keeps your device's own dtb + ramdisk. It checks `ro.product.device` (`x1s`), which the
4G G980F shares, so **check your exact model before flashing**.

Then install the KernelSU-Next manager v3.4.2 from the
[official releases](https://github.com/KernelSU-Next/KernelSU-Next/releases).

## Licensing

* Kernel source: **GPL-2.0** (`COPYING`). KernelSU-Next kernel driver: **GPL-2.0** (`KernelSU-Next/kernel/LICENSE`).
  SuSFS (`fs/susfs.c`): **GPL-2.0**. AnyKernel3: its own license (`anykernel/LICENSE`).
* Samsung firmware blobs and stock images are **not** included and are not covered by the GPL.
  `firmware/.gitignore` keeps them out of git; please don't force-add them.

## Credits

[KernelSU-Next](https://github.com/KernelSU-Next/KernelSU-Next) team ·
[simonpunk](https://gitlab.com/simonpunk/susfs4ksu) / sidex15 / backslashxx (SuSFS) ·
JackA1ltman (non-GKI 4.19 SuSFS backport) ·
[enchantedglycerin](https://github.com/enchantedglycerin/exynos990-KernelSU-Next-SuSFS) (Exynos 990 KernelSU-Next + SuSFS tree) ·
[osm0sis](https://github.com/osm0sis/AnyKernel3) (AnyKernel3) ·
Samsung Open Source Release Center.

See `PROVENANCE.md` for the upstream Samsung source packages.
