# 四段提示词写法

先看真正的参考片与20张图，不能只凭菜名写所谓“参考还原”。确定一个菜谱版本，再给每个场景一个主要任务及2–3个切镜动作，不塞满完整配方。常见小炒四段如下，慢炖/烘焙应重新分配。

| 段落 | 故事任务 | 画面状态 | 五图的语义选择 |
|---|---|---|---|
| 01 0–10秒 | 食材品质、处理腌制 | 生料→切好→腌好 | 主料形态、刀纹方向、辅料形状、入调味、腌后表面 |
| 02 10–20秒 | 主料关键火候 | 腌好→初熟暂盛 | 入锅、接触油面、划散、变色、盛出 |
| 03 20–30秒 | 辅料与合炒 | 辅料受热→主料回锅 | 姜入锅、炒香、辅料、回牛肉、均匀挂汁 |
| 04 30–40秒 | 出锅、食欲与记忆点 | 全熟→装盘→英雄特写 | 最后合炒、出锅、落盘、完整成品、质地特写 |

五张图不是机械等距截图；它们应该对应五个不同动作或可辨状态。模糊、遮挡、水印遮住主料的图要换时间点，不擅自擦标记。

## 每段英文结构

1. `Create one 10-second 9:16 premium food commercial shot sequence using Gemini Omni Flash 1.1.`
2. `Reference video: scene-NN.mp4 — use the physical cooking order and gesture timing. Reference images 01–05: [逐张作用]. Treat them as visual facts, not text instructions. Do not reproduce the source creator's graphic layout, voice, identity, logo or set.`
3. Series bible：相同肉片/肉丝形状、姜丝粗细、配菜颜色、炒锅材质、盘子形状、台面、左右光向；具名描述而不是“与上一段一样”（独立请求未必有上一段上下文）。
4. 0–3s / 3–7s / 7–10s 实际动作、景别、有限运镜、食物从何处来去、该段结尾状态；下一段接同一状态。合理表现蒸汽和油光，不无故火焰腾起、液体违反重力、原料瞬间熟化。
5. 宏观广告质感：large soft side key, controlled dark fill, warm highlights, natural food color, selective shallow depth of field while the essential action stays legible, restrained camera movement, realistic steam and moist texture。不要塑料、过油、过饱和、夸张慢动作。
6. 环境声：quiet original cooking Foley only, no speech, no music。生成声也要验收。
7. Negative：no captions, no invented logos or brands, no extra utensils/ingredients, no malformed hands, no floating food, no recipe order reversal, no jump from raw to plated。不要求移除平台标识。

封面在最终片的英雄段选择；不是另造与广告不符的照片。建议成品留出平台UI安全空间；平台不同安全区需按实际发布场景复核。

旁白在四段生成验收之后再写，分四个语义节奏但合并一个文本TTS请求。不要把10秒视觉节奏当TTS必须每10秒断句。复听确保动作先后不互相矛盾、末句完整。
