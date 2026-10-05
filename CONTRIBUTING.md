# 贡献

改 `course/` 里的 Markdown 或原图，以及 `skills/seedance-25-director/` 里的技能文件。不要提交视频、WebP、缩略图或网站构建产物。

## 改课

- 教学文件放在对应模块的 `教学/`，提示词放在同模块的 `提示词/`。文件名以课号 `L00-01` 这类编号开头，提示词文件名以 `-提示词.md` 结尾。
- 课内图片继续用相对路径，例如 `图/L01-01-练习01-图1.jpg`。不要改成网站哈希文件名。
- 新增或更换 `教学/图/`、`提示词/图/` 里的 JPG 时，同步更新 [course/meta/images-manifest.json](course/meta/images-manifest.json)。每条包含相对 `course/` 的 `rel`、`caption`、英文 `prompt`、`ratio`。
- `01-景别/教学/图/L01-01-景别阶梯总览.jpg` 是拼图封面，没有单独生图提示词，不要写进 manifest。社交预览 `course/assets/social-preview.jpg` 同样除外。
- 文件名以 `seedance25-` 开头的图只放在 `course/附录/图/`，并记入 [course/meta/official-frames.json](course/meta/official-frames.json)。它们不是 CC BY 素材。

## 提交前

在仓库根目录运行：

```bash
python3 -B scripts/validate_repo.py
cd skills/seedance-25-director
python3 -B scripts/validate.py skill .
python3 -B scripts/validate.py package assets/examples/narrative-package.json
python3 -B -m unittest discover -s tests -v
```

校验只检查结构、配对和文件是否存在，不判断画面好不好。
