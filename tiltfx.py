#!/usr/bin/env python3

import sys
import argparse
from Crypto.Hash import SHA1

sys.path.append("Infinity/tools/psptools")
from psptool.pbp import is_pbp, PBP
from psptool.pack import pack_prx
from psptool.prx import decrypt, encrypt

# Check the SHA-1 of the original TiltFX EBOOT.PBP file
def checkInputEboot(executable):
    validHash = b'\xbb\xce\x51\xda\x3f\x99\xde\xae\xe3\xe0\x4a\x52\xc7\x2e\x49\x5b\xa7\xbb\xb2\x10'
    h = SHA1.new()
    h.update(executable)
    return h.digest() == validHash

# Patch the TiltFX ELF to make it license-free.
def patchTiltFxElf(elf):
    off = 0x60 # ELF header size
    patchedElf = elf[:0xd7e8+off]
    # Force set g_isLicenseValid to 1 in checkLicense() function (0x0000d79c).
    patchedElf += b'\x22\x01\x00\x10'
    patchedElf += elf[0xd7e8+4+off:]
    return patchedElf

parser = argparse.ArgumentParser(description="Datel TiltFX patcher")
parser.add_argument('input', type=argparse.FileType('rb'), help='Input file path of the original TiltFX PSP EBOOT to patch')
parser.add_argument('output', type=str, help='Output file path of the resulting patched updater EBOOT')
args = parser.parse_args()

executable = args.input.read()
if not is_pbp(executable):
    raise ValueError("Input file must be a PBP")
if not checkInputEboot(executable):
    raise ValueError("Input file data doesn't match the original TiltFX PSP EBOOT")

pbp = PBP(executable)
pbp.prx = patchTiltFxElf(decrypt(pbp.prx))
pbp.prx = encrypt(pack_prx(pbp.prx, is_pbp=True, psptag=lambda x: 0x0B000000), vanity="LICENSE-FREE PATCHED")

with open("assets/icon0.png", 'rb') as f:
    pbp.icon0 = f.read()

with open(args.output, 'wb') as f:
    f.write(pbp.pack())
    print("Successfully patched TiltFX PSP EBOOT")
