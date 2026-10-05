# 署名与许可

本仓库把课程文字、教学示意图、官方案例关键帧和导演技能分开许可。一张许可证不覆盖全部文件。

## 课程文字

`course/` 下 `00` 到 `09` 的教学与提示词、`course/模板/`、`course/附录/` 的文字，以及本页与 README 的说明文字，采用 [知识共享 署名 4.0 国际许可协议](LICENSE)（CC BY 4.0）。

署名时请注明：susirial，〈AI 电影导演教程〉，并链接到 https://github.com/susirial/seedance2.5-How-to-build 。

该地址是这套课程已经公开发布的历史仓库。本目录是同一课程的维护副本，补入了网站教材里的提示词配图。历史仓库里的课文与这里并不完全相同。

## 技能代码

[skills/seedance-25-director/scripts](skills/seedance-25-director/scripts) 与 [skills/seedance-25-director/tests](skills/seedance-25-director/tests) 采用 [MIT 许可证](skills/seedance-25-director/LICENSE)。仓库根目录的 [LICENSE-MIT](LICENSE-MIT) 是同一份许可证的副本。技能目录中的 Markdown、JSON 模板和风格数据属于课程方法的一部分，随课程文字使用 CC BY 4.0。

## 教学示意图

各课 `教学/图/` 与 `提示词/图/` 里的示意图由多种生图模型分别生成，包括 Nano Banana、GPT Image 等。仓库没有逐张记录模型名称。图注和英文静帧提示词记在 [course/meta/images-manifest.json](course/meta/images-manifest.json)。

这些图只用来说明镜头概念。不同模型的画面不能互相比较效果，也不能当作视频成片。静态图不能证明运镜稳定或音画同步。

在发布者有权许可的范围内，这些示意图随课程以 CC BY 4.0 提供。这不表示发布者对模型输出享有排他权利。使用时请保留上述模型说明。

人物、服装和街道在多数基础课里保持一致，是为了让读者只比较景别、构图、光和机位。构图课里的白线是后加的三分线或中轴线。

`01-景别/教学/图/L01-01-景别阶梯总览.jpg` 是九档景别拼图，没有单独的英文生图提示词，因此不在 images-manifest 里。`course/assets/social-preview.jpg` 是社交预览，同样不在该清单里。

`_生成/参考/` 是内部定妆试片，不作为教程成果发布，本仓库没有这个目录。

## 官方案例关键帧

[course/附录/图](course/附录/图) 中文件名以 `seedance25-` 开头的 12 张图，是 Seedance 2.5 官方发布文视频的取帧，不是本项目生成或复现的结果。引用记录见 [course/meta/official-frames.json](course/meta/official-frames.json)。

来源页面：https://seed.bytedance.com/zh/blog/one-take-creation-flexible-referencing-introducing-seedance-2-5

维护者于 2026-10-04 确认已取得允许公开教学引用的授权。本次只使用少量关键帧。未独立审核授权书。这些帧不纳入 CC BY 或 MIT，也不授予读者转载完整视频、转授权或其他商业用途的权利。图注中的时间是媒体文件时间。完整视频留在官方页面，本仓库不提供视频文件。

## 不在本仓库里的东西

本仓库不上传、不嵌入、不转存 mp4、mov、webm 等视频演示，也不提交网站用的 WebP、缩略图或搜索索引。
