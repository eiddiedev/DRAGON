# 重载一
public void Teleport(Vector3 pos)
## 参数
| 参数  | 参数描述 |
| --- | --- |
| pos | 指定传送的 Position |
## 描述
将当前的  [Actor  ](../../DouyinActor.md)传送到指定位置，且无旋转角度。

# 重载二
public void Teleport(Vector3 pos, Quaternion rot)
## 参数
| 参数 | 参数描述 |
| --- | --- |
| pos | 指定传送的 Position |
| rot | 指定传送后的旋转角度 |
## 描述
将当前的 [Actor ](../../DouyinActor.md)传送到指定位置，且可定义传送后的角度。

