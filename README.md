# 橙功剪辑师

这套 Skill 用真实关键帧和你确认剪辑范围，再制作和检查成片。它包含工作步骤和检查脚本，媒体处理由客户端能调用的本地工具完成。

## 用 Codex？把这两行发给它

```text
请帮我安装这个「橙功剪辑师」Skill。装好后告诉我怎么在新聊天里选用它。
https://github.com/gc8531517-sketch/chenggong-video-editing/tree/main/.agents/skills/chenggong-video-editing
```

Codex 如果提示需要联网或写入技能目录，按界面提示操作。它确认装好后，开一个新聊天，输入 `$chenggong-video-editing`，选中「橙功视频制作流程」。如果列表里还找不到，重启 Codex 再试。

## 用 WorkBuddy？下载一个 ZIP

[下载 WorkBuddy 安装包](https://github.com/gc8531517-sketch/chenggong-video-editing/raw/refs/heads/main/chenggong-video-editing-workbuddy.zip)。在 WorkBuddy 左侧点「专家·技能·连接器 → 技能 → 添加技能 → 上传技能」，选中这个 ZIP。装好后，在聊天框点「＋ → 技能」，选择 `chenggong-video-editing`。[WorkBuddy 官方说明](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market#上传技能)

用其他助手，也可以先把上面的安装请求发给它。能否直接安装，取决于它是否支持加载 Skill。下面的剪辑流程需要它能访问视频并调用剪辑工具。

## 第一次剪辑

1. 选中 Skill，把一段短口播和录屏素材发给助手。如果助手读不到附件，把视频放进当前打开的项目或工作空间，再告诉它文件名。
2. 发送下面这类请求。

   > 这是我的口播视频和录屏素材。请按口播内容把录屏放到对应的地方，跳过无关操作，没有实操画面的地方加一点合适的包装。

3. 打开关键帧。确认整组时，可以说「就按这组关键帧剪」。收到成片后打开 MP4 看一遍。

给口播配录屏、改构图或加包装时，助手会先发关键帧，等你确认后才剪。口播默认有字幕，想跳过就说「不要加字幕」。

## 装不上或导不出视频？

- **Codex 装不上**：也可以点本页「Code → Download ZIP」，解压后用 Codex 打开包含 `README.md` 和 `.agents` 的那一层文件夹，再在项目聊天里选择 Skill。[Codex 官方说明](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)
- **助手说缺工具**：把提示发给助手，让它检查哪一项缺了。本地导出需要 FFmpeg 和 FFprobe，检查脚本需要 Python 3.11+。做字幕还需要转写工具或你提供的带时间点的字幕，以及可用字体。

用自己的视频试剪时，建议另开素材文件夹。公开仓库用 Git 提交时，忽略规则会排除素材、截图等临时文件。网页手动上传时请自己核对文件清单。
