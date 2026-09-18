#!/usr/bin/env python3
"""
Encode une HDRI Radiance en PNG RGBE, décodable en quelques lignes côté page.

Pourquoi pas le .hdr directement : three.js le lit avec RGBELoader, un module
d'extension qu'il faudrait vendoriser et replier dans le build d'un seul
fichier. Pourquoi pas le canal alpha, qui est l'emplacement habituel de
l'exposant : un canvas 2D prémultiplie l'alpha, ce qui détruirait les valeurs.

L'exposant est donc rangé sous la mantisse, dans une image deux fois plus
haute et entièrement opaque. La page lit les deux moitiés et reconstruit les
flottants. Le PNG reste compressé, contrairement à un binaire brut.

    usage : python3 encode_env.py source.hdr [largeur]
"""
import os
import sys
import cv2
import numpy as np

SITE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SITE, "assets", "web", "env-studio-rgbe.png")


def to_rgbe(rgb):
    """float32 HxWx3 (RGB) -> uint8 HxWx3 mantisses + uint8 HxW exposants."""
    peak = rgb.max(axis=2)
    mant, expo = np.frexp(np.maximum(peak, 0))       # peak = mant * 2**expo
    scale = np.where(peak > 1e-32, mant * 256.0 / np.maximum(peak, 1e-32), 0.0)
    mantissa = np.clip(rgb * scale[..., None], 0, 255).astype(np.uint8)
    exponent = np.where(peak > 1e-32, np.clip(expo + 128, 0, 255), 0).astype(np.uint8)
    return mantissa, exponent


def main():
    src = sys.argv[1]
    width = int(sys.argv[2]) if len(sys.argv) > 2 else 1024

    hdr = cv2.imread(src, cv2.IMREAD_ANYDEPTH | cv2.IMREAD_COLOR)
    if hdr is None:
        sys.exit(f"illisible : {src}")
    hdr = cv2.cvtColor(hdr, cv2.COLOR_BGR2RGB).astype(np.float32)
    hdr = cv2.resize(hdr, (width, width // 2), interpolation=cv2.INTER_AREA)

    mantissa, exponent = to_rgbe(hdr)
    sheet = np.vstack([mantissa, np.repeat(exponent[..., None], 3, axis=2)])

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cv2.imwrite(OUT, cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_PNG_COMPRESSION, 9])

    # contrôle : on redécode et on compare à la source
    back = mantissa.astype(np.float32) * np.power(2.0, exponent.astype(np.float32) - 128)[..., None] / 256.0
    ref = np.maximum(hdr, 0)
    err = np.abs(back - ref) / np.maximum(ref, 1e-3)
    print(f"{os.path.basename(OUT)} : {sheet.shape[1]}x{sheet.shape[0]}, "
          f"{os.path.getsize(OUT)//1024} Ko")
    print(f"  luminance max conservée : {back.max():.0f} (source {ref.max():.0f})")
    print(f"  erreur relative médiane : {np.median(err)*100:.2f} %")


if __name__ == "__main__":
    main()
