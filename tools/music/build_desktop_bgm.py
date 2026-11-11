"""Package the existing PCM theme for the editor's WebGL Lua runtime (no file IO)."""
import base64
import hashlib
from pathlib import Path
import wave

ROOT = Path(__file__).resolve().parents[2]


def build_module():
    path = ROOT / 'assets/music/dragonrest_theme.wav'
    with wave.open(str(path)) as wav:
        if wav.getsampwidth() != 2 or wav.getcomptype() != 'NONE':
            raise ValueError('Desktop music requires uncompressed signed 16-bit PCM')
        channels, rate, frames = wav.getnchannels(), wav.getframerate(), wav.getnframes()
        raw = wav.readframes(frames)
    size = 16384 * channels * 2
    chunks = [base64.b64encode(raw[i:i + size]).decode('ascii') for i in range(0, len(raw), size)]
    return ('-- Generated from assets/music/dragonrest_theme.wav; do not edit.\n'
            f'-- PCM sha256: {hashlib.sha256(raw).hexdigest()}\n'
            f'return {{ channels = {channels}, rate = {rate}, frames = {frames}, chunks = {{\n'
            + ''.join(f'"{chunk}",\n' for chunk in chunks) + '} }\n')


if __name__ == '__main__':
    import sys
    Path(sys.argv[1]).write_text(build_module())
