# 橙功剪辑师使用指南

第一次来可以先看[仓库首页的两步试用](../README.md)。这里放具体安装步骤、试剪用语和常见问题。

## 安装和选用

### Codex

[首页的安装请求](../README.md)里已经带上 Skill 链接，整段发给 Codex 就可以。装好后开一个新聊天，输入 `$chenggong-video-editing`，选中「橙功视频制作流程」。列表里没找到时，重启 Codex 再试。

也可以在仓库首页点「Code → Download ZIP」，解压后用 Codex 的「文件 → 打开文件夹」打开同时含有 `README.md` 和 `.agents` 的那一层。输入技能名，选标为「项目」的条目。[Codex 官方说明](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)

### WorkBuddy

1. [下载专用 ZIP](https://github.com/gc8531517-sketch/chenggong-video-editing/raw/refs/heads/main/chenggong-video-editing-workbuddy.zip)。
2. 在左侧打开「专家·技能·连接器 → 技能 → 添加技能 → 上传技能」，选择下载下来的 ZIP。
3. 新建任务，打开你放素材的文件夹。在聊天框点「＋ → 技能」，选择 `chenggong-video-editing`。

WorkBuddy 的自定义 ZIP 通过「上传技能」导入。[WorkBuddy 官方说明](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market#上传技能)

### 其他助手

发首页的安装请求，让助手检查能否安装。支持 Skill 的客户端可以按自己的安装方式读取[完整 Skill 文件夹](../.agents/skills/chenggong-video-editing)。实际剪辑需要客户端能访问素材、运行剪辑工具并保存输出。已实测的桌面入口为 Windows 上的 Codex 和 WorkBuddy。

## 剪第一条时可以这么说

| 你想做什么 | 可以直接发给助手的话 |
| --- | --- |
| 只发口播视频 | 帮我剪掉明显的停顿，保留我的原声和原构图，先给我看关键帧。 |
| 口播配录屏 | 按口播内容把录屏放到对应的位置，缺实操画面时给我一个轻包装建议。 |
| 只看开头 | 先给我看开头这一组关键帧，其他部分等我看完再说。 |
| 只确认其中一段 | 开头按这组关键帧剪，正文先等我确认。 |
| 跳过新增字幕 | 保留原声，这次不要加字幕。 |
| 只要字幕文件 | 这次只给我 SRT 字幕文件。 |

给口播配录屏、调整构图或加包装时，第一轮默认只交真实关键帧。图片会标出台词和素材取自哪里。你可以逐镜、成组或整段确认。成片默认保留原声原速，给口播加下方居中的白字黑描边字幕。

## 卡住时看这里

- **视频读不到**。打开一个存放素材的本地文件夹，把视频放进去，再告诉助手文件名。视频本身无法播放时，换一份可播放的原件。
- **能看关键帧，导不出视频**。把助手的报错原样发给它，让它检查缺了什么。本地剪辑需要 FFmpeg 和 FFprobe，制作检查需要 Python 3.11+，字幕还需要转写工具或带时间点的稿件，以及能显示字幕语言的字体。
- **WorkBuddy 提示 401 或登录失效**。重新登录后再试。若当前仓库目录在受限模式下，换成一个干净的素材文件夹，再选已导入的 Skill。
- **中途换了视频或录屏**。告诉助手哪个文件更新了，先看受影响的帧，再确认新版本。

想了解助手具体怎么做，可以看 [Skill 执行规则](../.agents/skills/chenggong-video-editing/SKILL.md)。反馈时可以附一段可公开的示例，或用文字描述画面和报错。
