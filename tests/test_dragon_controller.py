"""Exercise the authored transition timings without a running Unity editor."""
from pathlib import Path
import unittest
from lupa import LuaRuntime

class DragonTransitions(unittest.TestCase):
    def test_ride_landing_dismount_and_return(self):
        self.exercise_roundtrip(False)

    def test_mountain_perch_and_flat_ground_use_matching_clips(self):
        self.exercise_roundtrip(True)

    def test_flight_height_includes_mesh_mountains_but_not_rider(self):
        src=(Path(__file__).resolve().parents[1]/'scripts/world_main_v5.lua').read_text()
        lua=LuaRuntime()
        lua.execute("""
        Vector3=function(x,y,z)return {x=x,y=y,z=z}end
        Time={deltaTime=.04}
        DR={ground=function()return 40 end,rider={gameObject={transform={}}},yaw=0}
        local terrain={point={y=40},transform={IsChildOf=function()return false end}}
        local mountain={point={y=120},transform={IsChildOf=function()return false end}}
        local avatar={point={y=160},transform={IsChildOf=function()return true end}}
        UnityEngine={QueryTriggerInteraction={Ignore=2},Physics={RaycastAll=function()
            return {[0]=avatar,[1]=terrain,[2]=mountain,Length=3}
        end}}
        """)
        lua.execute(src[src.index('function DR.flightSurface'):src.index('function DR.setup()')])
        lua.execute("""
        assert(DR.flightSurface(100,200)==120)
        assert(DR.flightClearance(100,200)==120)
        UnityEngine.Physics.RaycastAll=function()error('physics unavailable')end
        assert(DR.flightSurface(100,200)==40)
        """)

    def test_idle_restarts_if_stopped_without_resetting_playing_loop(self):
        src=(Path(__file__).resolve().parents[1]/'scripts/world_main_v5.lua').read_text()
        lua=LuaRuntime()
        lua.execute("""
        UnityEngine={WrapMode={Loop=2,ClampForever=8}}
        dbg=function()end;report=function(s)error(s)end
        state={time=3,speed=0};playing=false;starts=0
        DR={clip='idle',an={enabled=false,
            IsPlaying=function()return playing end,
            get_Item=function()return state end,
            CrossFade=function()starts=starts+1;playing=true end}}
        """)
        lua.execute(src[src.index('function DR.play(clip, loop)'):src.index('function DR.homePose')])
        lua.execute("""
        DR.play('idle',true)
        assert(starts==1 and DR.an.enabled and state.speed==1 and state.time==0)
        assert(state.wrapMode==2 and DR.an.wrapMode==2)
        state.time=2.5
        DR.play('idle',true)
        assert(starts==1 and state.time==2.5,'playing loop must retain its time')
        playing=false
        DR.play('idle',true)
        assert(starts==2 and state.time==0,'stopped loop must restart')
        """)

    def exercise_roundtrip(self, perched):
        src=(Path(__file__).resolve().parents[1]/'scripts/world_main_v5.lua').read_text()
        code=src[src.index('function DR.play(clip, loop)'):src.index('function DR.update(actor, p)')]
        lua=LuaRuntime()
        lua.execute('''
        local mt={};mt.__sub=function(a,b)return Vector3(a.x-b.x,a.y-b.y,a.z-b.z)end
        Vector3=function(x,y,z)return setmetatable({x=x,y=y,z=z},mt)end
        UnityEngine={WrapMode={Loop=2,ClampForever=8}}
        Quaternion={Euler=function(v)return v end,Slerp=function(a,b,w)return w==1 and b or a end}
        Time={deltaTime=1/30};Input={GetKeyDown=function()return false end,GetKey=function()return false end}
        DouyinCameraService={SetDistance=function()end,GetYaw=function()return 0 end}
        moveX,moveY=0,0
        dbg=function()end;report=function(s)error(s)end;toast=function()end
        dist2d=function(p,x,z)return math.sqrt((p.x-x)^2+(p.z-z)^2)end
        played={}
        DR={state='perch',cool=0,jump=true,speed=0,roll=0,yaw=0,homeYaw=0,
            parts={{}},homeRot={x=.1,y=.2,z=.3,w=.9},ALTAR={48,150},pos=Vector3(100,40,100),home=Vector3(100,40,100),
            ground=function()return 40 end,flightClearance=function()return 40 end,place=function()end,align=function()end,
            mount=function()end,an={IsPlaying=function()return true end,get_Item=function()return {} end,CrossFade=function(_,clip)table.insert(played,clip)end}}
        actor={Immobilize=function(self,v)self.immobile=v end}
        DR.dismount=function(a)a.immobile=false;a.dismounts=(a.dismounts or 0)+1 end
        player=Vector3(48,40,150)
        ''')
        lua.execute(code)
        lua.globals().DR.perchClips = perched
        lua.execute('''
        DR.updateV8(actor,player)
        assert(DR.state=='takeoff' and actor.immobile)
        for i=1,55 do DR.updateV8(actor,player)end
        assert(DR.state=='ride')
        for i=1,20 do DR.updateV8(actor,player)end
        DR.jump=true;DR.updateV8(actor,player)
        assert(DR.state=='approach')
        for i=1,91 do DR.updateV8(actor,player)end
        assert(DR.state=='touchdown' and actor.immobile)
        for i=1,60 do DR.updateV8(actor,player)end
        assert(actor.immobile,'must wait through landing cushioning before dismount')
        for i=1,25 do DR.updateV8(actor,player)end
        assert(DR.state=='rest' and not actor.immobile and actor.dismounts==1)
        for i=1,1000 do DR.updateV8(actor,player)end
        assert(DR.state=='perch' and actor.dismounts==1)
        assert(DR.pos.x==DR.home.x and DR.pos.z==DR.home.z and DR.pos.y==DR.home.y)
        assert(DR.parts[1].rotation==DR.homeRot,'return must preserve the user tilt')
        local expected='idle,takeoff,fly,land,idle,takeoff,fly,land,idle'
        assert(table.concat(played,',')==expected)
        -- Prolonged no-input flight must turn back from every map edge.
        for _,heading in ipairs({0,90,180,270}) do
            DR.state='ride';DR.pos=Vector3(128,75,128);DR.yaw=heading
            for i=1,2000 do
                DR.updateV8(actor,player)
                assert(DR.pos.x>=8 and DR.pos.x<=248 and DR.pos.z>=8 and DR.pos.z<=248)
            end
        end
        ''')

if __name__=='__main__':unittest.main()
