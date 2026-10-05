# 预制风格提示词

机器可用的完整提示词位于 `assets/styles/prompt-presets.json`。该库与30套导演方案分工不同：

- 导演方案回答为什么这样拍、人物和空间怎样调度、动作怎样完成。
- 风格提示词回答画面由什么媒介、材质、线条、光色和运动观感呈现。
- 先确定导演方案，再选一个主风格提示词。不能用风格词替代镜头设计。

所有预设均为原创整理，未生成实测。它们不是Seedance官方风格枚举，也不代表平台存在同名按钮。

## 两张参考图识别

用户提供的两张截图是同一真人写实风格面板的上下部分，可识别为：

| 参考图 | 可识别子风格 |
|---|---|
| 图1 | 人像写实、古风写实、古代战场、现代都市、玄幻修仙、悬疑恐怖、未来科幻、中式梦境、国风古典、年代剧、伪纪录片、中世纪奇幻 |
| 图2 | 古风武侠、邵氏电影、民国剧、惊悚压抑、暗黑哥特、中式华丽 |

截图中的“伪纪录片”首字显示较小，预设另保留“观察纪录感”作为检索别名。图片只用于识别分类名称和视觉方向，不能据此宣称知道原产品内部提示词。

## 八大类

| 类别ID | 中文 | 预设数量 | 内容 |
|---|---|---:|---|
| live-action-realistic | 真人写实 | 18 | 完整覆盖两张参考图 |
| animation-3d | 3D动画 | 4 | 写实三维、风格化角色、低多边形、微缩玩具 |
| anime-2d | 二次元 | 4 | 清新青春、热血动作、复古赛璐璐、漫画图形 |
| photographic-art | 摄影艺术 | 4 | 胶片纪实、黑白艺术、低调光编辑、梦幻长曝光 |
| illustration-art | 插画艺术 | 4 | 编辑插画、绘本、电影概念、矢量图形 |
| punk-art | 朋克艺术 | 4 | 赛博、蒸汽、柴油、太阳朋克 |
| traditional-fine-art | 传统美术 | 4 | 水墨、工笔、敦煌壁画、木版画 |
| craft-art | 工艺美术 | 4 | 剪纸、黏土、刺绣、景泰蓝 |

## 使用方法

### 1. 选择

根据原文信息任务选择一个主预设。需要混合时最多再选一个次预设，并限定它只控制某个维度：

```text
主预设：live.future-scifi，控制空间、服装和技术材质。
次预设：photo.monochrome-fine-art，只控制黑白明暗，不带入其人物和场景。
```

不要把“真人写实、赛博朋克、水墨、黏土”同时堆入一条提示词。媒介冲突时先确认主实现。

### 2. 替换槽位

每条英文生图提示词使用这些槽位：

```text
{subject}       主体身份与稳定外观
{scene}         具体空间与地标
{pose}          单一静态姿态
{composition}   景别、视角和画面位置
{lighting}      有来源的光线
{aspect_ratio}  画幅
```

视频提示词使用：

```text
{action}        有触发、过程和完成态的动作
{camera}        摄影机或画面层运动
{sound}         对白、环境声、动作声和音乐
{end_state}     可观察末态
```

替换后删掉花括号，检查主体、持物手、空间方向和光源没有冲突。

### 3. 编译示例

选择 `live.modern-city`，原文为“她在地铁出口停下，抬头确认路牌”：

```text
Contemporary live-action cinematic still of an original short-haired woman in a navy coat in a concrete metro exit with the stairway behind her and a route sign above frame right, standing still with her chin slightly lowered before looking up, medium-wide eye-level view with her at frame left and the sign readable at frame right. Credible modern wardrobe, real street depth, practical urban light, subtle reflections, cool overhead station light balanced by soft daylight from the exit, natural documentary detail, aspect ratio 16:9.
```

```text
现代都市写实，保持短发、藏蓝外套、楼梯和路牌方向不漂移。0–3秒：她走到地铁出口边缘停下；3–6秒：抬头看向画右上方路牌；6–8秒：确认后保持站位。摄影机固定平视中全景；保留脚步、站内底噪和出口车流声，无对白、无配乐；结束于她站在画左、目光落在画右上路牌。
```

这里的路牌文字若必须准确，应由获授权素材或后期完成；不要让模型凭空生成关键信息。

## 输出规则

1. 在导演提案中给出预设ID、中文名和选择理由。
2. 在关键帧中输出替换完成的英文提示词，并附中文释义。
3. 在视频任务中输出替换完成的中文风格段，再接时间轴、素材绑定、保持项和排除项。
4. `exclude`是画面约束，不是平台负面提示词参数；入口没有负面框时，把必要项改写进主提示词。
5. 用户提供参考图时，先说明观察到的线条、材质、光色和构图，再选择最接近预设；不能只凭文件名判断。
6. 预设不覆盖角色和场景基准。身份由接受的角色图控制，空间由场景图或白模控制，风格图不得转移其中人物与文字。
