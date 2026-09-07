# 中文安装与使用说明

公开仓库：[pcyone/omni-food-ad-studio](https://github.com/pcyone/omni-food-ad-studio)。本页是Skill执行时使用的简明说明；面向用户的逐步操作见 [中文版安装与详细使用说明](../docs/01-中文版安装与详细使用说明.md)，实现原理与可发布文稿见 [完整实现教程与推文串](../docs/02-完整实现教程与推文串.md)。

## 一、安装 Skill

将完整 `omni-food-ad-studio` 文件夹放入 Codex 的 skills 目录（通常 `~/.codex/skills/`，自定义 CODEX_HOME 时使用其 skills 子目录）。不要只复制 SKILL.md；保留 scripts、references、examples、tests 和 agents。新开任务或刷新后选择“Omni 高端美食广告”。

若同名目录已经存在，先备份再更新，不覆盖用户修改。旧的 `food-ad-doubao-video` 和 `omni-food-ad-prompts` 可以共存。此 Skill 已包含独立剪辑/配音/验收脚本，不依赖这两个旧 Skill 的绝对路径。

## 二、一次性环境准备

- Python3.10+、Node20+、FFmpeg及ffprobe。macOS可用可信包管理器安装，如 `brew install ffmpeg node python`，先检查已装版本。Windows也可运行Python/Node/FFmpeg脚本，路径与浏览器支持按本机调整。
- Agent Reach：先检查是否已安装，阅读其SKILL并doctor；缺失时阅读官方[安装说明](https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md)，检查安装脚本内容后按其当前说明安装，不直接执行未经读取的远程脚本。
- B站下载器：见 [bili-dl-cli](https://github.com/qingsheng-git/bili-dl-cli)。仓库以Node运行，按README克隆、`npm install`，用 `node cli.js --url BV号 --output 路径`；本机已包装成 `bili-dl`。浏览器登录由用户控制，不复制Cookie到Skill。
- YouTube：优先已有 MeTube。本机已确认服务在 `http://127.0.0.1:8081`。新机器参照 [MeTube](https://github.com/alexta69/metube) 安装Docker服务，绑定回环地址、只挂载专用下载目录，不公开到外网。先检查端口和同名容器，不能覆盖其它服务。
- Flow：访问 [Google Flow](https://labs.google/fx/tools/flow)，完成用户登录、地区和套餐资格及额度检查。容器用已有 HBG Gemini Flow Suite 时先读它的SKILL/README，参照[上游](https://github.com/Mr-funny/hbg-gemini-flow-suite)完成一次性授权；不要导出认证目录。视频加五图需当前页面入口或经验证的联合参考接口，不能凭r2v别名假定支持视频。
- ChatCut可选：必须有当前可调用的插件工具及会话。没有连接时仍可用本Skill附带的FFmpeg剪辑脚本，结果和来源映射相同。
- 豆包：将有效配置保存在用户自己的私密 .env 文件；仅引用路径。需 `DOUBAO_TTS_API_KEY`、`DOUBAO_TTS_RESOURCE_ID`、`DOUBAO_TTS_SPEAKER`；可选 `DOUBAO_TTS_MODEL`、`DOUBAO_TTS_SPEECH_RATE`。这些值来自用户已经开通的服务，不在教程里编造。环境变量优先，也可设 `DOUBAO_TTS_ENV_FILE` 或传 `--env`。本Skill不自动扫描用户全部磁盘找密钥。

豆包配置结构（占位符不能直接使用）：

```dotenv
DOUBAO_TTS_API_KEY=YOUR_PRIVATE_KEY
DOUBAO_TTS_RESOURCE_ID=YOUR_RESOURCE_ID
DOUBAO_TTS_SPEAKER=YOUR_LICENSED_SPEAKER
```

配置不要放在公开仓库或压缩包。设置文件仅本人可读。音色使用范围需另行核实。

## 三、日常只需一句话

“使用 $omni-food-ad-studio，子姜炒牛肉。”

默认执行完整40秒流程，但先列出候选视频的链接、作者、时长、完整度及授权情况，等待你选择并确认下载剪辑和AI上传的使用范围；未确认前不下载、不制作、不上传。你不需要填写分镜、时间戳或提示词，确认素材后由代理负责EDL、20图、Flow生成、口播及验收。直接提供实拍素材可跳过选片和下载；若只要求本地剪辑取图，本次不会自动上传。登录/验证码、额外权利声明、额度超支等仍可能需要用户处理。

如果自己有完整拍摄素材，可说：“做子姜炒牛肉，参考视频在这个路径，我有权将该素材上传AI服务并用于广告。”代理仍检查其中音乐、人像、标识和授权范围。

## 四、完整操作教程

本流程包含必经人工确认：每生成一段视频，展示给你确认无误后才生成下一段；第四段也需确认。四段全部确认后展示完整口播稿，等你确认定稿才配音和合成。未确认会暂停，不会提前排队生成。你仅发修改稿时会再请你确认；如同条消息明确说“此版定稿，开始配音合成”，则按该授权继续。

1. 输入菜名，新项目保存配置及doctor结果。
2. 输出研究及候选视频表，推荐做法版本和参考视频，暂停等待用户选片与确认使用范围，不代选。
3. 确认后仅下载选定视频，核对文件、时长和完整工序；换视频须重新让用户选择。用户已提供实拍文件则直接检查该文件，不另行下载。
4. 观察视频后编EDL，压成40秒，再分4×10秒；选每段5个必要状态，导出共20图。
5. 形成四个详细提示词，明确视频＋五图作用、分秒动作、系列连续性。
6. Flow设置Omni1.1Flash/10秒/9:16/一条输出，每段分别上传并实际附加六项参考；逐段生成、检查、下载最高可用画质，并暂停让用户确认，确认后才生成下一段。当前720p标准输出如需1080p交付会标注升采样。
7. 四段均经人工确认后，按实得画面写完整旁白稿，等待用户确认无误，再一次豆包生成连续声音；自动测时，允许轻微变速，不裁尾字。需要改稿时重新确认后才生成声音。
8. 四段按顺序合并成40秒1080×1920，人声为前景，低音量保留合规环境声。
9. 从最后成品镜头导出封面，检查MP4、黑场、音频、转场和末句；写独立审核记录。展示封面图片并暂停，等待你明确确认可用；如需修改，重新选图后再请你确认。
10. 封面确认后直接将该图嵌入MP4作为封面，另存带封面视频，不再重复询问保存许可；保留原成片和独立图片，不插入片头、不改40秒时长或配音。检查封面确已嵌入、画面与音频未变，保存独立封面验收记录。
11. 交付带封面视频、独立封面及验收记录。部分平台会忽略内嵌封面，发布时可能仍需手动选择封面。未经商业许可审核通过的版本标注待审核，不冒充可以直接商用。

## 五、文件与故障

主要输出：`outputs/菜名_40秒_带封面.mp4`（封面确认后保存）、`outputs/final.mp4`、`outputs/封面.jpg`、`outputs/关键帧检查.jpg`、`outputs/verification.json`、`outputs/cover-verification.json`、`narration.txt`。项目还保留 `approval.json`、`research.md`、`rights.json`、`edl.json`、`generation.json`、`review.json`、40秒参考和20图。

B站412/验证码：暂停网络阶段，保留候选BV，按平台正常验证或使用用户自有素材；不反复高频请求。Flow任务完成但下载失败：恢复下载，不重复生成。只有720p：保留原件并披露升采样。旁白太长：改稿，不把结尾硬切掉。没有上传许可：先交研究和分镜，等待合法参考。

本机回归测试使用已有素材，不会消耗Flow/TTS额度：

```bash
python3 -m unittest discover -s /绝对路径/omni-food-ad-studio/tests -v
node --check /绝对路径/omni-food-ad-studio/scripts/doubao.mjs
```

新 Skill 的建立和本地测试，不等于已经完成一次新的在线四段生成。查看 [validation.md](validation.md) 区分实际验证和待在线验收项目。
