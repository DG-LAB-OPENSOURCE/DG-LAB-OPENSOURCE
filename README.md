# DG-LAB 开源
DG-LAB设备在全球范围得到广大朋友的认可与喜爱.很多朋友们希望我们的设备可以参与到更多的场景中去,为此我们将DG-LAB 具有代表性的设备蓝牙协议以开源的形式分享出来，您可以通过无数种其他编程的方式将DG-LAB设备参与到您自己的娱乐场景中去.
> 开源蓝牙协议旨在让DG-LAB爱好者更加自由的使用设备，未经授权请勿将本内容用以任何商业用途,如有需要,请[联系我们](https://www.dungeon-lab.com)

## 郊狼情趣电击器
### 蓝牙协议
|  服务UUID | 特性UUID  | 属性  | 名称  | 大小(BYTE)  |
| :------------: | :------------: | :------------: | :------------: | :------------: |
|  0x180A | 0x1500  | 读/通知  | Battery_Level  | 1字节  |
| 0x180B  | 0x1504  | 读/写/通知  | 	PWM_AB2  | 3字节  |
|  0x180B | 0x1505  | 读/写  | PWM_A34  | 3字节  |
|  0x180B | 0x1506  | 读/写  | PWM_B34  | 3字节  |



### 基本原理

