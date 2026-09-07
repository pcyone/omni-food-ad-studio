# Flow 联合参考生成合约

核查日期：2026-09-05。每次新运行重新看当前页面，不把以下信息当永久产品承诺。

Google 官方 [模型能力](https://support.google.com/flow/answer/16352836?hl=en) 列出 Omni Flash 1.1 的10秒及参考生成能力，当前标准输出720p、草稿360p。[视频编辑](https://support.google.com/flow/answer/16935718?hl=en) 支持选择最长10秒片段并加 ingredients。[参考添加](https://support.google.com/flow/answer/16353334?hl=en) 说明可以拖入视频/图片、通过资产选择附加。这不证明当前账户可同时用六项或提供1080p下载；实际页面预检为准。

## 先选择真实可用入口

优先复用已授权 HBG Gemini Flow Suite 容器的能力，遵守该 runtime 的 SKILL。读取 `./suite flow raw video --help` 和 `r2v --help`。本机2026-09-05检查：r2v支持最多7张图片、Omni 10秒，但只有图片 `--ref`；没有 v2v 命令。**禁止将MP4塞进图片参数或宣称视频被用了。**

用户要求视频＋五图，必须走支持它的 Flow 页面控制或未来经验证的联合参考接口。发现可用浏览器工具后完整读取其 Skill，复用用户授权会话；登录/MFA/风控留给用户，不读取Cookie内容。若容器授权与宿主浏览器授权不同，不能称“同一已登录会话”。不可用时仅把此阶段标为 blocked，继续完成本地研究/提示词/脚本工作。

若未来用户明确同意“仅图片参考”，可用 r2v 五次 `--ref`，但必须把变更写入项目且不可标成原联合参考流程通过。示意（不是本 Skill 默认替代方案）：

```bash
./suite flow raw video r2v "已核实的提示词" --ref /workspace/scene-01/01.jpg --ref /workspace/scene-01/02.jpg --ref /workspace/scene-01/03.jpg --ref /workspace/scene-01/04.jpg --ref /workspace/scene-01/05.jpg --model omni-flash --duration 10 --aspect 9:16 --count 1 --out-dir /data/outputs/菜品/scene-01 --json
```

使用 raw 可避免本地 wrapper 默认清理水印的行为；普通 `suite flow video` 当前可能默认去标记，应先禁用自动清理并保留原件。不要修改共享配置影响其它任务，也不要自动消除来源标识。

## 每段的页面检查

每次只生成当前待审的一段。第2、3、4段提交前，必须核对项目 `approval.json` 中上一段当前文件哈希对应的用户明确确认；未确认则暂停，不能提前提交或排队。完整规则见 SKILL.md 的“人工确认关口”。

1. 项目名称含菜名与独立运行ID。模型标签确认 **Gemini Omni Flash 1.1**；仅CLI别名 `omni-flash` 不证明具体版本。设10秒、9:16、一个输出，读取额度/成本。
2. 先检查 rights.json 的本地使用及外部上传依据，再上传 `references/scene-01.mp4` 和 `references/scene-01/01.jpg` 至 `05.jpg`。
3. 等待每个上传完成；资产库中存在不代表已加入提示词。逐个选入；页面上确认六个正确附件及标签，记录截图/可读状态。不允许四段混用参考。
4. 如果进入视频编辑模式，选完整0–10秒；逐张附加图。引用作用是工序/形态，不复制字幕、人物或布局。粘贴该段完整提示词。
5. 若界面有六项数量/文件格式限制，停止并如实说明；不偷偷丢图片、做拼图、换模型。执行权限/预算范围内提交一次。记录生成任务ID或页面结果ID；可得HTTP状态则记录，但HTTP200仅是接受，不代表视频完成。
6. 等待任务完成并预览关键动作。每段最多一次缺陷重做，保留旧版本理由。超限须得到用户新的费用授权。错误后先查已存在的结果，避免重复计费。
7. 下载最高可用版本。原件不能被升采样结果覆盖。记录下载菜单、分辨率、hash、生成结果ID；文件验证每段10秒。720p则保留720p原件，最终1080p注明 upscale；不要称“原生1080p”。
8. 展示当前段可观看文件及检查结果，等待用户确认无误。收到与当前版本对应的明确确认并记录后，才可生成下一段；第4段确认后才进入口播定稿。用户提出问题则先处理当前段，重做或替换后重新展示并等待确认。

## generation.json 字段

init 创建 capability 及四个 scene 模板。观察后填写：

- capabilities：checked_at、model_label、video_plus_five_images（true仅实证）、duration_10s、evidence。
- scenes：id、model_label、task_id、file（绝对路径）、sha256、reference_video、reference_images（5路径）、input_sha256（六个参考绝对路径到其SHA256的映射）、attachments_verified、evidence、quality_pass。

证据应对应当前请求，而非借用旧成片。`quality_pass` 需观察该段早/中/晚和关键动作：菜色、形态、器具、人手、熟度连续性；不合格返回重做。`quality_pass` 不是用户确认，不能据此自动生成下一段。模型/provider元数据若不可独立验证，记录证据等级，不作绝对声明。
