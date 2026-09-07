# Omni 高端美食广告工作室


https://github.com/user-attachments/assets/1548d344-792a-4fd9-beaa-f0c7c8373906



https://github.com/user-attachments/assets/12f596cd-1403-494c-9810-a0bb17bc424f



`omni-food-ad-studio` 是由 Codex 编排的美食广告制作 Skill：从菜名或自有素材开始，完成资料研究、参考剪辑、Flow 联合参考生成、连续豆包旁白、40秒竖屏合成，以及人工确认后的封面嵌入。

## 两份中文教程

- [教程一：安装与详细使用说明](docs/01-中文版安装与详细使用说明.md)
- [教程二：完整实现教程与推文串](docs/02-完整实现教程与推文串.md)

## 使用

公开仓库：[pcyone/omni-food-ad-studio](https://github.com/pcyone/omni-food-ad-studio)。下载完整目录后安装到当前Codex的skills目录；具体依赖、配置、安装及更新方法见教程一。

安装后对 Codex 说：

> 使用 $omni-food-ad-studio，菜名：客家碌鹅。制作40秒竖屏广告，按规则等待我逐段确认视频、确认口播稿和封面。

有自己的素材时直接提供文件，并说明允许的本地处理和外部AI上传范围。

## 四个不能跳过的人工关口

1. 候选视频先列出，由用户选择并确认使用范围，再下载。
2. 每段生成视频必须经用户确认，才生成下一段；第四段也需确认。
3. 完整口播稿确认后，才配音、合成；改稿后重新确认。
4. 封面确认后，直接嵌入MP4并另存带封面视频，时长和配音不变。

这些关口由 Codex 依据 Skill 执行并记录；当前命令行脚本本身不是审批系统。不能绕过用户确认直接批量运行命令。

## 真实能力与边界

- 本地入口：`scripts/pipeline.py` 的 init / prepare / finish / verify，及 `scripts/doubao.mjs`。
- Flow 联合参考生成依赖当前可用、已授权的浏览器操作；不是附带脚本自动完成网页生成。
- 模型、10秒能力、六项参考、分辨率、额度以实际账户页面为准；不保证所有账户可用。
- 1080p交付不代表模型原生1080p生成；升采样须披露。
- 技术检查、创意审核、商用权利状态独立记录；不承诺“完美”或无条件可商用。
- 内嵌封面可能被发布平台忽略，仍提供独立封面图。
- 仓库只发布规则、脚本与教程，不包含用户媒体、密钥、Cookie或私人配置。

## 验证

```bash
python3 -m unittest discover -s tests -v
node --check scripts/doubao.mjs
```

历史及版本边界见 [验证记录](references/validation.md)。安装前请阅读 [SKILL.md](SKILL.md) 与教程；外部工具、服务账户和额度需自行准备，安装Skill不会自动授予登录或使用权限。
关于作者： 2019年加入Crypto，ETH & BTC Holder | Alpha在职 | Defi | 空投 | 打新 | 早期项目研究 | 港股打新 | 持续分享 AI 内容、自动化、开发与产品实践； 实用教程｜工作流｜创意实验｜构建记录 个人站：http://ryanai.top 微信：ryanpeng999
