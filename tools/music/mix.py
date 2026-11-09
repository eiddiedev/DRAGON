#!/usr/bin/env python3
"""把各声部混成立体声：声像、人造厅堂混响、母带压限。用法：mix.py <声部目录> <长度秒> <输出.wav>"""
import sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, butter, sosfilt
D, L, OUT = sys.argv[1], float(sys.argv[2]), sys.argv[3]
SR = 44100
# 声部: (音量, 声像 -1..1, 混响送量)
MIX = dict(basses=(1.0, 0, .5), cello=(1.0, -.12, .4), strings=(.8, .1, .9), choir=(.72, 0, 1.2), brass=(.7, .18, .8), horn=(.95, -.25, .9),
           trumpet=(.62, .22, .9), violin=(.8, -.3, 1.0), harp=(.55, .35, 1.0), timp=(.9, .05, .7), taiko=(1.05, 0, .55), cym=(.42, .2, 1.2))
n = int(L * SR)
tail = int(3 * SR)
dry = np.zeros((n + tail, 2))
wet = np.zeros((n + tail, 2))
for k, (g, pan, send) in MIX.items():
    try:
        sr, x = wavfile.read(f'{D}/{k}.wav')
    except FileNotFoundError:
        continue
    x = x.astype(np.float64)
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    x = x[:n + tail]
    a = np.array([np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)]) * 1.41
    y = x * a * g
    dry[:len(y)] += y
    wet[:len(y)] += y * send
# 厅堂混响：指数衰减的噪声，2 个声道不相关，高频衰减更快
rng = np.random.default_rng(5)
irn = int(3.4 * SR)
t = np.arange(irn) / SR
irs = []
for ch in range(2):
    e = rng.normal(size=irn) * np.exp(-t * 2.1)
    lp = sosfilt(butter(2, 5200 / (SR / 2), 'low', output='sos'), e)
    hp = sosfilt(butter(2, 160 / (SR / 2), 'high', output='sos'), lp)
    hp[:int(.02 * SR)] = 0
    irs.append(hp / np.sqrt((hp ** 2).sum()))
rev = np.stack([fftconvolve(wet[:, c], irs[c])[:n + tail] for c in range(2)], 1)
mix = dry + rev * .55
# 混响尾巴叠回开头，首尾无缝
mix[:tail] += mix[n:n + tail]
mix = mix[:n]
# 增强低频分量与轻度压缩
mix /= np.abs(mix).max()
env = np.maximum(np.abs(mix[:, 0]), np.abs(mix[:, 1]))
win = int(.05 * SR)
env = np.convolve(env, np.ones(win) / win, 'same')
gain = (np.clip(env, .02, 1) / .28) ** -.28
gain = np.convolve(gain, np.ones(win) / win, 'same')
mix = mix * gain[:, None]
mix = np.tanh(mix / np.abs(mix).max() * 1.25) * .92
# 首尾 10ms 淡变避免爆音
f = int(.01 * SR)
mix[:f] *= np.linspace(0, 1, f)[:, None]
mix[-f:] *= np.linspace(1, 0, f)[:, None]
wavfile.write(OUT, SR, (mix * 32767).astype(np.int16))
print('mixed', round(len(mix) / SR, 1), 's', 'rms', round(float(np.sqrt((mix ** 2).mean())), 3))
