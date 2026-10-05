# 成对提示词示范

以下均为原创设计，未生成图像或视频，不能作为成功率证据。静态图交给另行选定的生图模型；Seedance 2.5用于视频。这里的普通参考不是专门首帧输入。

## 同一原文的三种处理

原文：夜班店员拿起柜台上的旧钥匙，门铃响，她看向门口，没有离开柜台。

不可变项：拿起旧钥匙；门铃响；铃后看门；没有离开柜台。不补来者身份、危险事件或对白。短发、蓝针织衫、右手拿取为导演设计，不声称出自原文。

共用地理：北侧柜台、东侧入口；摄影机在柜台西侧，入口投影在画右。先设计角色基准，再设计无人物场景及单把旧铜钥匙，检查地理后制作对应风格的单幅起始关键帧。风格切换需重新制作对应媒介的基准，不把摄影图直接叫作已锁定二维角色。

每个例子独立使用 `@图片1`，绑定本例待制作的起始关键帧；控制身份、柜台地理、钥匙和初始姿态，不转移多视图布局或图中文字。建议任务为 `reference_to_video`，8秒、16:9；入口待核实，状态为 provisional。

### 自然纪实

意图：观察一次日常行动被声音打断，保留门外信息。平视中全景容纳手、头、柜台与入口；放弃门外反打，因为原文没有提供来者，反打容易新增事实。

关键帧英文：

```text
Photographic medium-wide view from the west end of a shop counter. An original short-haired woman in a blue cardigan stands behind it, her right hand resting beside one old brass key. The east doorway remains visible at frame right. Cool overhead practical light, faint window fill, readable room depth, natural fabric texture. Aspect ratio 16:9.
```

中文释义：西侧中全景，蓝衫短发店员右手在单把旧钥匙旁；入口画右，冷顶灯与微弱窗光。此刻尚未拿起钥匙。

视频中文：

```text
@图片1 参考店员身份、柜台地理与起始构图，不改变钥匙数量。写实生活质感。0–3秒：固定中全景，她用右手拿起旧钥匙。3–5秒：画右入口传来门铃，她转头看向那里。5–8秒：她仍站在柜台后，右手留着钥匙。顶灯不变，保留钥匙轻响和店内电流声，无对白、无配乐，不切镜。
```

末态：右手有钥匙，身体留柜台后，目光朝画右。验收：单把钥匙；右手拿取；先铃后转头；入口不换边；没有离柜台；不出现来者。退路：拿取失败时用独立手部插入镜头证明拿起，再回中景看门，不删除动作。

### 冷峻几何悬疑

意图：以框架和铃声引导注意，不编造威胁。柜台水平线和背景框架形成限定区；轻推进只在铃后开始。放弃大幅环绕，因为会改变入口可见性并丢失手部证据。

关键帧英文：

```text
Photographic medium-wide view from the west side of a shop counter. An original short-haired woman in a blue cardigan stands within the rectangle of a door frame behind her. One old brass key lies beside her right hand. The east entrance is at the far right edge. Cool overhead practicals, precise counter lines, restrained grey palette. Aspect ratio 16:9.
```

中文释义：同地理、同角色与道具，强调柜台线条和背景框架，入口位于右边缘，冷光有顶灯来源。不加科幻设备。

视频中文：

```text
@图片1 参考店员、柜台与入口地理。0–3秒：她右手拿起旧钥匙，摄影机固定。3–5秒：画右门铃响，她转头看入口，摄影机沿柜台外轻微推进。5–8秒：停在仍能看见握钥匙右手的中景，她没有离开柜台。冷顶灯稳定，只有钥匙声、门铃和店内低噪，不加人物、对白或配乐。
```

末态：中景仍有右手钥匙和柜台边，目光朝画右。验收：四个原文事实全部保留；没有提前转头；铃后才推进；手始终可读；没有越轴；没有额外人物。退路：取消推进保留转头，不增加危险音效代替悬念。

### 清新青春二维

意图：用手部姿态与目光的小变化表达同一事件；亲密感来自观察注意力，不来自臆造心理。仍用中全景保留地理，但线稿、色块、两级阴影取代摄影皮肤质感。放弃夸张表情特写，避免改变原文的日常动作。

关键帧英文：

```text
Hand-drawn 2D cel illustration, medium-wide layout from the west end of a shop counter. An original short-haired woman in a blue cardigan stands behind it, right hand beside one brass key. The east entrance sits at frame right. Clean thin outlines, two-tone cool overhead shadows, painted background layers, readable hands and doorway. Aspect ratio 16:9.
```

中文释义：单幅二维起点，细线、两级冷顶光阴影、分层背景；蓝衫与单把铜钥匙稳定，尚未拿起。不把生图写成转头全过程。

视频中文：

```text
@图片1 参考角色线稿、服装色块、柜台布局与起始姿态。保持手绘二维与两级阴影。0–3秒：固定中全景，店员右手拿起旧钥匙。3–5秒：画右门铃响，她转头看门口。5–8秒：保持站位，右手仍握钥匙，背景层不移动。声音为钥匙轻响、门铃和店内低噪，无对白、无配乐，不切镜。
```

末态：右手握钥匙，头朝画右，身体仍在柜台后。验收：线条粗细不漂；色块与发型不变；右手拿取；铃先于转头；东入口不换边；未离柜台。退路：放大手和钥匙在构图中的占比，仍保留面部及门的方向。

## 三套完整制作包

JSON是完整逐字段示例，本节解释读法，不另造第二份提示词权威记录。复制示例开始创作时替换来源与项目资料，不能把原创示例的素材状态改成已有结果。

| 制作包 | 媒介与手法 | 制作重点 |
|---|---|---|
| [旅店交钥匙](../assets/examples/narrative-package.json) | 摄影、古典构图 | 原文交接与“谢谢”拆成两任务，第一镜证明物件从谁到谁，第二镜承接左手钥匙后说话 |
| [水瓶材质展示](../assets/examples/product-package.json) | 写实三维、图形形式主义 | 基于材质精工方案显式覆盖导演层，以中轴、留白、光带时序组织完整产品，不增加功能主张 |
| [二维跨低箱](../assets/examples/animation-package.json) | 二维赛璐璐、动感本能 | 固定侧面全身保留预备、跨越、缓冲、停稳的可见证据，动感不等于摄影机必动 |

### 剧情包

读 SRC001 的交接与台词，再看 SC001 的北柜台、东入口、西机位。A001/A002/A003分别准备店主、旅人和环境，KF001输出A004。SH001选择双人中景，不用纯面部特写遮掉交接。

CL001为8秒推与接，CL002为6秒反应与“谢谢”；二者不是官方最长时长的演示。KF002/A005只是接续起点预案。收到并接受CL001结果后，核对旅人左手、钥匙、视线、灯和机位，再修订KF002；没有成片时CL002继续 provisional。

### 产品包

原文只证明外形与拉丝材质。A001先定义瓶盖、圆柱比例、无标识表面；KF001输出单幅A002。图形导演覆盖写在style.overrides，落实到中心轴、相等侧留白及5秒扫光后3秒停留，不只更换标签。

瓶与摄影机固定，光移动。验收全瓶、轮廓、拉丝方向、光带方向与无新增标识。设计图和生成图都不能证明保温、防漏等未给定功效。

### 动画包

A001角色、A002箱与落点先建立，KF001输出A003。SH001不套摄影光圈；以侧面剪影、两级阴影和脚箱接触判断可读性。CL001用0–2秒准备、2–5秒跨越、5–8秒缓冲停稳，速度线只辅助动作。

失败时先检查脚箱关系与起始姿态，必要时提出降低箱高或拆镜并确认改变；不能剪掉落地后直接假称完成。三个包均未有真实素材，校验通过只表示结构与显式约束通过。
