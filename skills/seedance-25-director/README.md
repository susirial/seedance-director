# Seedance 2.5 导演技能

把原文转成可拍、可生成、可检查的镜头方案。使用中文交互。生图提示词默认英文并附中文释义，视频提示词默认中文。

本技能不调用生成服务，不上传素材，不索取密钥。目录里的示例都没有实际出图或出视频。

## 安装

复制整个目录，不要只复制 `SKILL.md`。在本仓库中，目录是 `skills/seedance-25-director`。把它放进所用工具要求的技能路径：全局使用放到用户级技能目录，只给当前项目用时放到项目内的技能目录。`references/`、`assets/` 和 `scripts/` 都要留下。

放在课程仓库中不会自动变成已安装技能。复制到技能目录后，在新对话里要求使用它。

## 校验

```bash
python3 -B scripts/validate.py skill .
python3 -B scripts/validate.py package assets/examples/narrative-package.json
python3 -B -m unittest discover -s tests -v
```

`scripts/` 与 `tests/` 使用 MIT 许可证。其余说明与模板随课程使用 CC BY 4.0。课程仓库根目录的 `NOTICE.md` 写明分层许可。单独复制本目录后那个文件不在技能包内，已发布文本见 [NOTICE.md](https://github.com/susirial/seedance2.5-How-to-build/blob/main/NOTICE.md)。
