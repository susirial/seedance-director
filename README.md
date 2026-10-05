# AI 电影导演教程与 Seedance 2.5 技能

English: A Chinese course on directing for AI video, practiced with Seedance 2.5, plus an installable agent skill. Lessons, prompts, and stills live in [`course/`](course/index.md). The skill is [`skills/seedance-25-director`](skills/seedance-25-director/SKILL.md). Course text and teaching stills are CC BY 4.0. Skill scripts and tests are MIT. Twelve official Seedance frames are not under those licenses. This repository has no video files.

从小白到资深导演的镜头语言课，外加一个可安装的导演技能。方法可以迁移；Seedance 2.5 是当前的视频实践示例。

[从导演思维开始](course/00-导论与工作流/教学/L00-01-导演思维.md) · [完整目录](course/index.md) · [安装技能](course/使用技能.md) · [署名](NOTICE.md)

![课程静帧：大远景、浅景深、黄金时刻、霓虹雨夜](course/assets/social-preview.jpg)

这些示意图由多种生图模型分别生成（包括 Nano Banana、GPT Image 等），只用来说明镜头概念。不同模型的画面不能互相比较效果，也不能当作视频成片。本仓库没有视频演示。静态图不能证明运镜稳定或音画同步。

## 两条路

**按课学。** 打开 [course/](course/index.md)。每个模块分成 `教学/` 和 `提示词/`。先读教学，再做提示词。练习图和提示词放在同一课里。

**把技能装进编辑器。** 技能不调用生成服务，不上传素材，也不索取密钥。内置示例没有出过图，也没有出过视频。复制整个目录，不要只复制 `SKILL.md`。

在仓库根目录执行：

```bash
mkdir -p ~/.cursor/skills
cp -R skills/seedance-25-director ~/.cursor/skills/seedance-25-director
```

复制之后，在新对话里说明要使用这个导演技能。文件放在本仓库里，不等于工具已经发现它。

## 五个段位

| 段位 | 你能做到 | 对应模块 |
|---|---|---|
| 一段 · 入门 | 说清每个镜头拍多大、拍哪里、用什么光 | 00、01 |
| 二段 · 基础 | 用景深、焦段、构图控制观众看哪里 | 02、03 |
| 三段 · 进阶 | 用光和运镜表达情绪，每个选择都有动机 | 04、05 |
| 四段 · 高级 | 写分镜表，在一次生成里切出 3–5 个镜头并保持连续 | 06、07 |
| 五段 · 大师 | 形成自己的导演风格，独立完成类型短片 | 08、09 |

## 十个模块

00、06、09 的封面借用其他课的静帧，目录里写明了出处。

| 模块 | 进入 |
|---|---|
| 00 导论与工作流 | [导演思维](course/00-导论与工作流/教学/L00-01-导演思维.md) |
| 01 景别 | [八种基本景别](course/01-景别/教学/L01-01-八种基本景别.md) |
| 02 景深与焦段 | [景深三要素](course/02-景深与焦段/教学/L02-01-景深三要素.md) |
| 03 构图 | [三分法与黄金比例](course/03-构图/教学/L03-01-三分法中心构图与黄金比例.md) |
| 04 光影与色彩 | [光的基础](course/04-光影与色彩/教学/L04-01-光的基础.md) |
| 05 运镜 | [固定镜头](course/05-运镜/教学/L05-01-固定镜头.md) |
| 06 镜头语言与分镜 | [镜头合同](course/06-镜头语言综合与分镜/教学/L06-01-镜头合同.md) |
| 07 世界导演风格 | [风格拆解](course/07-世界导演风格/教学/L07-00-风格拆解方法论.md) |
| 08 类型片实战 | [悬疑惊悚](course/08-类型片实战/教学/L08-01-悬疑惊悚.md) |
| 09 毕业项目 | [从剧本到成片](course/09-毕业项目/教学/L09-01-从剧本到成片.md) |

71 课的教学和提示词对照表在 [course/index.md](course/index.md)。术语、速查和官方案例在 [course/附录](course/附录/A-01-术语中英对照表.md)。

## 仓库里有什么

- 10 个模块，71 课教学，71 组配套提示词
- 提示词和教学图的 JPG 原图；英文静帧提示词在 [course/meta/images-manifest.json](course/meta/images-manifest.json)
- 12 张官方案例关键帧，记录在 [course/meta/official-frames.json](course/meta/official-frames.json)
- 可安装技能 [skills/seedance-25-director](skills/seedance-25-director)

没有 WebP 衍生图，也没有视频。来源说明见 [ORIGIN.md](ORIGIN.md)。

## 许可

课程文字和教学示意图为 CC BY 4.0，见 [LICENSE](LICENSE)。技能的 `scripts/` 与 `tests/` 为 MIT，见 [LICENSE-MIT](LICENSE-MIT)。官方案例帧两者都不覆盖。边界见 [NOTICE.md](NOTICE.md)。

## 校验

```bash
python3 -B scripts/validate_repo.py
cd skills/seedance-25-director
python3 -B scripts/validate.py skill .
python3 -B scripts/validate.py package assets/examples/narrative-package.json
python3 -B -m unittest discover -s tests -v
```
