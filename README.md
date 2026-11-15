# 橙功剪辑师

这套 Skill 用真实关键帧和你确认剪辑范围，再制作和检查成片。它包含工作步骤和检查脚本，媒体处理由客户端能调用的本地工具完成。

## 下载与安装

- **Codex** 用 GitHub 的「Code → Download ZIP」下载并解压仓库，保留 `.agents` 目录。在桌面客户端用「文件 → 打开文件夹」选择同时包含 `README.md` 和 `.agents` 的那一层。在项目的新聊天里输入 `$chenggong-video-editing`。如果出现同名项，选择标为「项目」的那一项。[Codex 官方文档](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)
- **WorkBuddy** 从「专家·技能·连接器 → 技能 → 添加技能 → 上传技能」选择仓库内的 `chenggong-video-editing-workbuddy.zip`，等待客户端完成检测并按提示安装。新建任务时，把自己的素材文件夹作为本地工作空间。用「＋ → 技能」搜索 `chenggong-video-editing` 并选中。[WorkBuddy 官方文档](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market#上传技能)

## 第一次剪辑

1. 确保客户端能读写工作区，并能运行 Python 3.11+、FFmpeg 和 FFprobe。口播字幕需要可用的转写工具或带时间点的稿件、字幕。字幕渲染还需要可用字体和支持字幕的剪辑工具，例如带 libass 的 FFmpeg。
2. 附加视频。客户端无法从附件读取原件时，把 MP4 放进已选工作区，并在消息里告诉它文件名。如果 WorkBuddy 提示 401 或登录失效，重新登录后再提交。选中技能后发送下面这类请求。

   > 这是我的口播视频和录屏素材。请按口播内容把录屏放到对应的地方，跳过无关操作，没有实操画面的地方加一点合适的包装。

3. 打开关键帧图片，回复你确认的镜头或区间。确认整组时，可以说「就按这组关键帧的画面和剪点做」。收到成片后打开 MP4，并核对标出的待核项。

给口播配录屏、调整构图或加包装时，第一轮默认只交关键帧。确认看过的范围后才剪和导出。你可以明确要求跳过这一步。口播剪辑默认带下方居中的白字黑描边字幕，想跳过新增字幕时写「不要加字幕」。

发布包包含 Skill 和检查脚本。执行能力取决于当前客户端能访问的文件和工具。Windows 上实测了口播截取、字幕、关键帧确认和多素材的检查流程。

用自己的视频试剪时，建议另开素材目录。若在仓库里试剪，Git 默认只收录 Skill、说明、许可证与导入包。使用网页手动上传时，请选择这几项，保留隐藏的 `.agents` 目录。
