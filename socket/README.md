## SOCKET控制-控制端开源

### 更新
time : 2024-06-03

desc :

前端 WSConnection.js文件：
function sendCustomMsg()方法中，发送消息的形式从一次性发送AB数据变为分别发送AB
const dataA = { type: "clientMsg", message: msg1, time: timeA, channel: "A" }
const dataB = { type: "clientMsg", message: msg2, time: timeB, channel: "B" }
sendWsMsg(dataA)
sendWsMsg(dataB)

后端 webSocketNode.js文件：
修改了当收到的消息type为 case "clientMsg": 的逻辑
1.当data.channel不存在时 报错406

2.本来会一次发送两个clear命令分别清除AB当前队列, 现在会根据消息里的data.channel来分别发送清除指令, 同时 AB通道的发信计时器独立管理

3.修改了function delaySendMsg(clientId, client, target, sendData, totalSends, timeSpace, channel)

此方法本来是建立一个计时器 一次发送两个通道的数据.
现在是根据data.channel分别创建AB各自的计时器，只有收到对应通道的覆盖消息时才会清除计时器重新开始发信

### 说明

SOCKET控制功能，是DG-LAB APP通过Socket服务连接到外部第三方控制端，控制端通过SOCKET向APP发送数据指令使郊狼进行脉冲输出的功能。开发者可以通过网页，游戏，脚本或其他终端在局域网环境或公网环境中对郊狼进行控制。

该功能仅支持 郊狼脉冲主机 3.0

### 项目

我们提供的官网示例分为两部分，前端控制部分(逻辑控制，数据展示，行为操作，指令数据生成等)和SOCKET后端部分(关系绑定，数据转发等)。

我们设计的方案是 N(APP终端)-SOCKET服务-N(第三方终端)的 N对N 模式，方便开发者制作的控制端可以同时多人使用。

### 项目结构

/socket/BackEnd(Node) -> SOCKET控制后端代码，部署文档可见 /socket/BackEnd(Node)/document.txt

/socket/FrontEnd(Html+Css+Js) -> SOCKET控制前端代码，部署文档可见 /socket/FrontEnd(Html+Css+Js)/document.txt

![项目结构](/image/socket_project.png)

### 两端连接流程

由于我们设计的方案是 N对N的模式，所以两端需要通过关系绑定的流程来连接到一起。

![两端连接流程](/image/socket_bind.png)

### 协议

#### 总则

1. 所有的消息全部都是json格式
2. json格式: {"type":"xxx","clientId":"xxx","targetId":"xxx","message":"xxx"}
3. type指令: 
   1. heartbeat -> 心跳包数据
   2. bind -> ID关系绑定
   3. msg -> 波形下发/强度变化/队列清空等数据指令
   4. break -> 连接断开
   5. error -> 服务错误
4. clientID: 第三方终端ID
5. targetId: APP ID
6. message: 消息/指令
7. json数据的字符最大长度为1950，若超过该长度，APP收到数据将会丢弃该消息
8. 除SOCKET连接时由SOCKET向终端返回ID的json数据targetId可以为空外，其他所有指令都必须且仅包含type,clientId,targetId,message这4个key，并且value不能为空
9. SOCKET服务生成的ID必须保证唯一，长度推荐32位(uuidV4)

#### 关系绑定

1. SOCKET通道与终端绑定：终端或APP连接SOCKET服务后，生成唯一ID，并与终端或APP的websocket对象绑定存储在Map中，向终端或APP返回ID
   
   SOCKET向终端或APP返回的数据: {"type":"bind","clientId":"xxxx-xxxxxxxxx-xxxxx-xxxxx-xx","targetId":"","message":"targetId"}
   
   终端或APP收到 type = bind，message = targetID时，表明为SOCKET服务返回的clientId为当前终端或APP的ID，本地保存。
2. 两边终端的关系绑定: DG-LAB APP将两边终端的ID发送给SOCKET服务后，服务将两个ID绑定存储在Map中
   
   APP向上发送的ID数据: {"type":"bind","clientId":"xxxx-xxxxxxxxx-xxxxx-xxxxx-xx","targetId":"xxxx-xxxxxxxxx-xxxxx-xxxxx-xx","message":"DGLAB"}
   
   SOCKET服务收到 type = bind，message = DGLAB，且clientId，targetId不为空时，会将clientId(第三方终端ID)和targetId(APP ID)进行绑定。
3. 绑定结果由SOCKET服务下发绑定关系的两个ID对应的终端或APP
   
   SOCKET下发的结果数据: {"type":"bind","clientId":"xxxx-xxxxxxxxx-xxxxx-xxxxx-xx","targetId":"xxxx-xxxxxxxxx-xxxxx-xxxxx-xx","message":"200"}
   
   终端或APP收到 type = bind，message = 200(或其他指定数据，详细请见错误码)时，执行对应UI逻辑

#### 接收强度数据
   
APP中的通道强度或强度上限变化时，会向上同步当前最新的通道强度和强度上限。

APP向上发送强度数据: {"type":"msg","clientId":"xxxx-xxxxxxxxx-xxxxx-xxxxx-xx","targetId":"xxxx-xxxxxxxxx-xxxxx-xxxxx-xx","message":"strength-x+x+x+x"}

SOCKET根据对应的ID将json转发给第三方终端，终端收到 type = msg，message = strength-x+x+x+x 的数据时，更新UI(更新最新的设备通道强度和强度上限)
   
指令解释: 
1. strength-A通道强度+B通道强度+A强度上限+B强度上限
2. 通道强度和强度上限的值范围在 0 ～ 200

举例：

数据：{"type":"msg","clientId":"xxxx-xxxxxxxxx-xxxxx-xxxxx-xx","targetId":"xxxx-xxxxxxxxx-xxxxx-xxxxx-xx","message":"strength-11+7+100+35"}

解释：strength-11+7+100+35 表示：当前设备A通道强度=11，B通道强度=7，A通道强度上限=100，B通道强度上限=35

#### 强度操作

第三方终端要修改设备通道强度时，发送指定的json指令。

终端向下发送强度操作数据: {"type":"msg","clientId":"xxxx-xxxxxxxxx-xxxxx-xxxxx-xx","targetId":"xxxx-xxxxxxxxx-xxxxx-xxxxx-xx","message":"strength-x+x+x"}

SOCKET服务根据对应的ID将json转发给APP，APP收到 type = msg，message = strength-x+x+x 的数据时，执行指定强度变化操作
   
指令解释:
1. strength-通道+强度变化模式+数值
2. 通道: 1 - A通道；2 - B通道
3. 强度变化模式: 0 - 通道强度减少；1 - 通道强度增加；2 - 通道强度变化为指定数值
4. 数值: 范围在(0 ~ 200)的整型

举例：

1. A通道强度+5 -> strength-1+1+5
2. B通道强度归零 -> strength-2+2+0
3. B通道强度-20 -> strength-2+0+20
4. A通道强度指定为35 -> strength-1+2+35

* Tips 指令必须严格按照协议编辑，任何非法的指令都会在APP端丢弃，不会执行

#### 波形操作

第三方终端要下发通道波形数据时，发送指定的json指令

终端向下发送波形数据: {"type":"msg","clientId":"xxxx-xxxxxxxxx-xxxxx-xxxxx-xx","targetId":"xxxx-xxxxxxxxx-xxxxx-xxxxx-xx","message":"pulse-x:[\"xxxxxxxxxxxxxxxx\",\"xxxxxxxxxxxxxxxx\",......,\"xxxxxxxxxxxxxxxx\"]"}

SOCKET服务根据对应的ID将json转发给APP，APP收到 type = msg，message = pulse-x:[] 的数据时，执行波形输出操作

指令解释:
1. pulse-通道:[波形数据,波形数据,......,波形数据]
2. 通道: A - A通道；B - B通道
3. 数据[波形数据,波形数据,......,波形数据]: 数组最大长度为100，若超出范围则APP会丢弃全部数据
4. 波形数据必须是8字节的HEX(16进制)形式。波形数据详情请参考 [郊狼情趣脉冲主机V3的蓝牙协议](image/README_V3.md)

* Tips 每条波形数据代表了100ms的数据，所以若每次发送的数据有10条，那么就是1s的数据，由于网络有一定延时，若要保证波形输出的连续性，建议波形数据的发送间隔略微小于波形数据的时间长度(< 1s)
* Tips 数组最大长度为100,也就是最多放置10s的数据，另外APP中的波形队列最大长度为500，即为50s的数据，若后接收到的数据无法全部放入波形队列，多余的部分会丢弃。所以谨慎考虑您的数据长度和数据发送间隔

#### 清空波形队列

APP中的波形执行是基于波形队列，遵循先进先出的原则，并且队列可以缓存500条波形数据(50s的数据)。

当波形队列中还有尚未执行完的波形数据时，第三方终端希望立刻执行新的波形数据，则需要先将对应通道的波形队列执行清空操作后，再发送波形数据，即可实现立刻执行新的波形数据的需求。

终端向下发送清空波形队列数据: {"type":"msg","clientId":"xxxx-xxxxxxxxx-xxxxx-xxxxx-xx","targetId":"xxxx-xxxxxxxxx-xxxxx-xxxxx-xx","message":"clear-x"}

SOCKET服务根据对应的ID将json转发给APP，APP收到 type = msg，message = clear-x 的数据时，执行指定通道波形队列清空操作

指令解释:
1. clear-通道
2. 通道: 1 - A通道；2 - B通道

* Tips 建议清空波形队列指令下发后，设定一个时间间隔后再下发新的波形数据，避免由于网络波动等原因导致 清空队列指令晚于波形数据执行造成波形数据丢失 的情况

#### APP反馈

APP中有多个不同形状的图标按钮，点击可以上发当前按下按钮的指令，第三方终端可以拟定不同形状图标代表的感受状态。

APP向上发送强度数据: {"type":"msg","clientId":"xxxx-xxxxxxxxx-xxxxx-xxxxx-xx","targetId":"xxxx-xxxxxxxxx-xxxxx-xxxxx-xx","message":"feedback-x"}

SOCKET根据对应的ID将json转发给第三方终端，终端收到 type = msg，message = feedback-x 的数据时，更新UI(显示APP 用户的反馈)

指令解释:
1. feedback-index
2. index: A通道5个按钮(从左至右)的角标为:0,1,2,3,4;B通道5个按钮(从左至右)的角标为:5,6,7,8,9

* Tips 您可以在自己开发的终端自由拟定每个形状代表了APP用户的某种反馈

#### 前端协议(重要)

如果您希望自己开发前端但完全使用我们的后端代码，那么您的前端协议与以上内容有所不同。

1. 强度操作：
   
   type : 1 -> 通道强度减少; 2 -> 通道强度增加; 3 -> 通道强度指定为某个值

   strength: 强度值变化量/指定强度值(当type为1或2时，该值会被强制设置为1)
   
   message: 'set channel' 固定不变

   channel: 1 -> A通道; 2 -> B通道

   clientId: 终端ID

   targetId: APP ID

   A通道强度减5 : { type : 1,strength: 5,message : 'set channel',channel:1,clientId:xxxx-xxxxxxxxx-xxxxx-xxxxx-xx,targetId:xxxx-xxxxxxxxx-xxxxx-xxxxx-xx }

   B通道强度加1 : { type : 2,strength: 1,message : 'set channel',channel:2,clientId:xxxx-xxxxxxxxx-xxxxx-xxxxx-xx,targetId:xxxx-xxxxxxxxx-xxxxx-xxxxx-xx }

   B通道强度变0 : { type : 3,strength: 0,message : 'set channel',channel:2,clientId:xxxx-xxxxxxxxx-xxxxx-xxxxx-xx,targetId:xxxx-xxxxxxxxx-xxxxx-xxxxx-xx }

2. 波形数据:
   
   后端代码中默认波形数据发送间隔为200ms，您可以根据您的波形数据来调整后端的波形数据发送间隔(修改后端代码 timeSpace 的变量值)
   
   type : clientMsg 固定不变

   message : A通道波形数据(16进制HEX数组json,具体见上面的协议说明)

   message2 : B通道波形数据(16进制HEX数组json,具体见上面的协议说明)

   time1 : A通道波形数据持续发送时长

   time2 : B通道波形数据持续发送时长

   clientId: 终端ID

   targetId: APP ID

3. 清空波形队列:

   type : msg 固定不变

   message: clear-1 -> 清除A通道波形队列; clear-2 -> 清除B通道波形队列

   clientId: 终端ID

   targetId: APP ID

#### 终端二维码

第三方终端的二维码必须按照协议指定方式来生成，否则APP将无法识别该二维码

第三方终端需要先连接SOCKET服务，并收到服务返回的终端ID，并存储。

二维码内容为: https://www.dungeon-lab.com/app-download.php#DGLAB-SOCKET#xxxxxxxxx

内容解释:

1. 二维码必须包含我们的APP官网下载地址: https://www.dungeon-lab.com/app-download.php
2. 二维码必须包含标签: DGLAB-SOCKET
3. 二维码必须包含SOCKET服务地址,且含有终端ID信息,且服务地址与ID信息之间不得再有其他内容
   
   举例：
   1. 正确 -> wss://ws.dungeon-lab.cn/xxxx-xxxxxxxxx-xxxxx-xxxxx-xx
   2. 错误 -> wss://ws.dungeon-lab.cn/xxxx/xxxx-xxxxxxxxx-xxxxx-xxxxx-xx
4. 二维码有且仅有两个#来分割1.2.3.提到的内容，否则APP将无法识别内容
5. 二维码除以上描述的必须包含的内容外，不可再涉及其他内容，否则APP可能无法识别

#### 错误码

200 - 成功

209 - 对方客户端已断开

210 - 二维码中没有有效的clientID

211 - socket连接上了，但服务器迟迟不下发app端的id来绑定

400 - 此id已被其他客户端绑定关系

401 - 要绑定的目标客户端不存在

402 - 收信方和寄信方不是绑定关系

403 - 发送的内容不是标准json对象

404 - 未找到收信人（离线）

405 - 下发的message长度大于1950

500 - 服务器内部异常

> 如有问题，请咨询service@dungeon-lab.com 或 发起issues