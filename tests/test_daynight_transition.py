from pathlib import Path
from lupa import LuaRuntime


def test_dial_requires_exit_and_transition_is_continuous():
    source=(Path(__file__).parents[1]/'scripts/world_main_v5.lua').read_text()
    segment=source[source.index('local function setDay(day)'):source.index('---------------------------------------------------------------- 骨骼动画')]
    lua=LuaRuntime()
    lua.execute('''
        Time={deltaTime=.1}; skyReady=true; clock=0; isDay=false; blend=0
        NIGHT_SECONDS=240;DAY_SECONDS=240;FADE_SECONDS=12
        dialCooldown=0;dialInside=false;DIALS={{121,57}};DIAL_RADIUS=2.2
        function setupEnv() end
        function applyEnv(t) value=t end
        function dbg() end
    '''+segment+'''\nstep=updateDayNight''')
    actor=lua.table_from({'position':lua.table_from({'x':121,'z':57})})
    values=[]
    for _ in range(150):
        lua.globals().step(actor);values.append(lua.globals().value or 0)
    assert lua.globals().isDay
    assert all(a<=b for a,b in zip(values,values[1:]))
    assert max(b-a for a,b in zip(values,values[1:]))<.02
    actor.position.x=130;lua.globals().step(actor)
    actor.position.x=121;lua.globals().step(actor)
    assert not lua.globals().isDay
