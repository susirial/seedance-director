# 制作包格式 v1

JSON是该版本结构化事实与提示词的权威记录。Markdown按同一内容排版；修改事实时先同步JSON，再检查阅读版，不能各自拥有不同版本的台词或上传号。

保存 `制作包.md` 与 `package.json`。未完成素材不创建空文件。每次修订创建新版本目录，用户指定位置优先。

## 通用约定

- UTF-8 JSON，schema_version 为整数1。拒绝重复键、NaN、Infinity。
- 秒数均为整数；布尔不是整数。未知用 null，不能用0或“未知”冒充数字。
- ID在全包实体中唯一，来源、场景、镜头、关键帧、资产、任务分别为 SRC001、SC001、SH001、KF001、A001、CL001；改编记录用AD001，审片问题用R001。数量更多时数字可增长。
- 必填字符串不为空；明确不适用时写明原因。数组可为空仅用于尚未设计的 draft 或明确无此项。
- asset.path 是相对 package.json 所在目录的文件路径，不能为绝对路径、外链、`..`或越界软链接。校验器只检查路径和存在性，不读媒体内容。用户外部素材应先由其授权组织到制作包内；本工具不复制。
- source.locator 是来源定位说明，不作为自动读取指令。
- 所有例子为原创设计，没有可用媒体，因此为 draft / provisional，素材 planned；格式通过不等于可提交生成。

## 顶层字段

`schema_version, project, sources, adaptation_notes, style, assets, scenes, shots, keyframes, clips, review` 均必填。

### project

| 字段 | 类型/约束 |
|---|---|
| id, title, purpose, audience, language | 非空字符串；id用项目短名 |
| total_seconds | 正整数或null；只有最终任务均为新生成时可自动核对合计 |
| aspect_ratio | `正整数:正整数` 或null |
| stage | draft / confirmed，confirmed表示创作决定已确认，不表示素材完成 |
| model_line | seedance-2.5 |
| surface | 对象，见下 |

surface：`name` 字符串或null；`verified` 布尔；`source` 官方依据URL或null；`checked_at` ISO日期或null；`operations` 已核实的任务名数组。verified=true需要名称、依据、日期与至少一个任务；prepared任务必须在operations中。可选 `limits` 使用能力资料同名键，只能给更严格的非负整数值，且必须有核实依据；不允许借此抬高模型限制。

### sources 与 adaptation_notes

sources每项：`id, type, locator, excerpt, provenance`。type为 script/copy/storyboard/text；provenance为 user_text/authored/user_reported/observed。excerpt记录必要原文。

adaptation_notes每项：`id, source_id, change, reason, status, applied`。status为 proposed/approved/rejected；applied为布尔。只有approved可以applied=true。提出但未采用的建议不会阻止其余忠实内容的制作。

### style

`preset_id` 是现存preset ID或null。`components` 有 media/look/direction/purpose 四项，均引用正确层级ID；draft可全部null表示尚未选。

四层要么完整选择，要么在draft中全部为null，不以半套组合宣称已完成风格选择。

`secondary_look` 是美术组件ID或null；`rationale`解释选择；`confirmed`布尔；`overrides`是非空说明字符串数组；`exceptions`为 `{shot_id, reason}` 数组。

选择现有preset后若components偏离它，必须有overrides说明；confirmed项目必须确认风格和四层组件。自定义组合可无preset_id，不需要捏造库内ID。

### assets

每项必填：

```text
id, media_type, role, status, path, duration_seconds, width, height,
rights, observation, state_description
```

- media_type：image/video/audio。
- status：planned/available/accepted/rejected。
- path：planned可null；其余状态需真实文件定位。未知或未收到的素材保持planned。
- duration_seconds：video/audio需正整数或null；image应null。
- width/height：image/video可为正整数或同时null；audio应均null。
- rights：权利说明，未核实可明确写待确认，但不能当作已授权。
- observation：planned/user_reported/observed；accepted不能是planned且需state_description。
- state_description：记录可见状态或明确待观察，不能写假实测。
- 可选 `design_prompt_en`：基准图生图提示词；`design_notes_zh`：中文解释。有基准图需求时提供，不强求视频或音频资产生图。

### scenes

每项：`id, source_ids, location, time, geography, characters, intent`。
source_ids引用来源，characters为角色名数组；无人物可为空。geography是可解释地标关系，不是“普通房间”。

### shots

每项：`id, scene_id, source_ids, audience_task, pov, reason, start_state, end_state, contract, action, sound, edit_relation, keyframe_ids, checks, representative, rejected_option`。

镜头source_ids必须包含在所属场景的source_ids中。合并不同来源的镜头时先同步场景来源链。

contract包含非空字符串 `size, perspective, composition, lighting, camera, blocking, fragile`，分别为景别、透视/媒介等效、构图、光色、摄影机、调度、易损锚点。

sound为 `{dialogue, ambience, effects, music}`，字符串；无对白或音乐明确写“无”。代表镜头representative=true时rejected_option必须说明放弃方案与原因，checks至少5条。其余镜头仍需非空检查项。

### keyframes

每项：`id, shot_id, role, output_asset_id, depends_on, aspect_ratio, image_prompt_en, image_prompt_zh, checks`。

role为 start/end/intermediate；output_asset_id引用image资产；depends_on为输入资产ID数组。禁止自依赖、循环依赖或多个关键帧指向同一输出资产。shot.keyframe_ids与keyframe.shot_id要互相对应。

本格式的镜头关键帧和输出任务使用项目画幅；不同画幅交付建立独立制作包。定妆与环境基准可以不同尺寸，不因此强制裁切。

角色、场景、道具基准图放assets并给design_prompt，不伪装为场景某个镜头的首帧。

### clips

每项：

```text
id, task, shot_ids, duration_seconds, aspect_ratio, timeline, bindings,
first_frame_id, last_frame_id, source_video_id, edit_range, edit_change,
preserve, extension_depth, source_clip_id, video_prompt_zh, status,
depends_on, fallback
```

task：text_to_video/image_to_video/reference_to_video/first_last_frame/edit/extend。

- status：provisional/prepared。
- timeline每项 `{shot_id, start, end}`。从0连续覆盖duration_seconds，按shot_ids次序；同镜多阶段允许连续重复shot_id。
- bindings每项 `{token, asset_id, target, dimensions, exclude}`。token为连续的@图片N/@视频N/@音频N；dimensions、exclude是非空字符串数组。每个资产绑定一次，可控制多个维度。同target同dimension不能属于两个资产。
- first_frame_id/last_frame_id：无此输入则null。image_to_video须首帧，first_last_frame须首尾帧。相应图须在bindings中，比例与任务相同；未知尺寸在预案里警告、prepared时错误。
- source_video_id：edit/extend的真实源资产，绑定中包含对应视频。其他任务为null。
- edit_range：编辑时为 `{start,end}`，属于源视频时间；其他任务为null。edit_change描述改前→改后；preserve明确保持项。编辑输出时长与比例继承源。
- extension_depth：本次完成后的延长次数，extend时正整数或未知null；大于已核实次数拒绝。extend.duration_seconds表示新增段长度。
- source_clip_id：extend预案需要总长说明时可引用已有生成任务，并将其列入depends_on，否则null；它不是已生成源视频的替代品。
- depends_on：任务ID数组，不得环；依赖未准备好时本任务不能prepared。
- video_prompt_zh：提交给模型的完整自然语言；其中出现的所有素材标签须在bindings里。
- fallback：失败后保留观众任务的退路。

text_to_video不能带输入绑定；reference_to_video至少一个绑定。专门帧字段不能用于冒充普通参考。prepared要求已确认风格、已核实入口支持本任务、可用素材与已知必要元数据；extend源还必须accepted且有实际状态依据。

编辑时duration是源片总长；延长时是新增长度。只要包含编辑/延长，工具不把所有duration相加宣称完整片长，而是提示人工复核拼接去重；新生成任务的全片合计才与project.total_seconds比较。

### review

`media_tested` 布尔，初始false；`issues`数组每项 `{id, level, object_id, evidence, suggestion, status}`。level为 error/warning/info；status为 open/resolved。`media_tested=true`需另有非空 `test_evidence` 说明源结果和观察范围，仍不代表校验器验证了视频内容。

## 阅读版顺序

原文与保真 → 导演意图与风格 → 基准资产 → 分镜表 → 逐关键帧生图 → 逐任务视频/参数/映射 → 连续性与编辑 → 验收及待办。

提示词正文按JSON原文展示，不混入取景理由。目录中的30套微示例是风格卡格式，不是完整package格式；三份制作包JSON才是本契约范例。

## 离线检查

在技能根目录运行：

```sh
python3 -B scripts/validate.py skill .
python3 -B scripts/validate.py package assets/examples/narrative-package.json
python3 -B -m unittest discover -s tests -v
```

制作包可以在其他目录，package参数可使用其绝对路径；asset.path仍只能在该制作包内部。风格ID从本校验器所属技能的风格库解析，自定义卡先经用户允许加入该库。

返回码0表示无结构错误；1表示内容错误；2表示参数或文件读取错误。ERROR含字段路径、对象ID和修正方向，WARNING保留未知资料与草案待办。未实测提示始终保留，不是平台核验失败的替代品。

校验器只读，不联网、不调用外部程序、不读媒体内容、不执行来源文本或自动修复。它检查显式字段与引用，不理解自然语言中的全部剧情、美学、动作或声音；Markdown与JSON事实一致性、官方依据真实性、素材权利、画面质量仍须人工审查。
