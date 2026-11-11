"""Regression checks for lossless PCM conversion and desktop-only playback."""
import array
import hashlib
from pathlib import Path
import sys
import unittest
import wave
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from music.build_desktop_bgm import build_module


class DesktopMusicTests(unittest.TestCase):
    def test_full_track_roundtrip(self):
        lua = LuaRuntime()
        module = lua.execute((ROOT / 'scripts/desktop_bgm.lua').read_text())
        data = lua.execute(build_module())
        result = hashlib.sha256()
        count = 0
        for chunk in data.chunks.values():
            samples = module.decode(chunk)
            pcm = array.array('h', (round(v * 32768) for v in samples.values()))
            if sys.byteorder != 'little':
                pcm.byteswap()
            result.update(pcm.tobytes())
            count += len(pcm)
        with wave.open(str(ROOT / 'assets/music/dragonrest_theme.wav')) as wav:
            self.assertEqual(count, wav.getnframes() * wav.getnchannels())
            self.assertEqual(data.rate, wav.getframerate())
            self.assertEqual(result.digest(), hashlib.sha256(wav.readframes(wav.getnframes())).digest())

    def test_mobile_and_native_do_not_load_fallback(self):
        code = (ROOT / 'scripts/world_main_v5.lua').read_text()
        gate = code[code.index('function UI.updateDesktopBgm()'):code.index('function OnDestroy()')]
        for mobile, platform in [(True, 17), (True, 11), (False, 2)]:
            lua = LuaRuntime()
            lua.execute('UI={root={}}; UnityEngine={Application={}, RuntimePlatform={WebGLPlayer=17}}; require=function() error("mobile must not require PCM") end')
            lua.globals().UnityEngine.Application.isMobilePlatform = mobile
            lua.globals().UnityEngine.Application.platform = platform
            lua.execute(gate)
            lua.globals().UI.updateDesktopBgm()
            self.assertTrue(lua.globals().UI.desktopBgmDisabled)

    def test_chunk_offsets_play_once_and_stop(self):
        lua = LuaRuntime()
        module = lua.execute((ROOT / 'scripts/desktop_bgm.lua').read_text())
        lua.globals().M = module
        lua.execute('''
        CS={UnityEngine={Debug={LogError=function() end}}}
        UnityEngine={Object={Destroy=function(o) o.destroyed=true end}}
        state={data={channels=2,chunks={"AIAAAAD///8=","AIAAAP9/AQA="}},chunk=1,offset=0,
          clip={length=1, SetData=function(self,samples,offset) assert(offset==self.written or offset==0); self.written=offset+#samples/2; return true end},
          source={Play=function(self) self.plays=(self.plays or 0)+1 end,Stop=function(self) self.stopped=true end},go={}}
        M.update(state); assert(state.source.plays==nil)
        M.update(state); assert(state.source.plays==1 and state.offset==4)
        state.source.time=2;state.source.isPlaying=true
        M.update(state);assert(state.source.plays==1)
        M.dispose(state);assert(state.source.stopped and state.go.destroyed and state.clip.destroyed)
        ''')


if __name__ == '__main__':
    unittest.main()
