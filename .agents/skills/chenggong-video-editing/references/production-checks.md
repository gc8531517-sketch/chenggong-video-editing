# 当前状态与交付检查

沿用本作品已有状态文件；新项目在当前可写项目中为该作品建立状态。填写真实依据，供下次上下文接续与脚本检查使用。脚本核验文件、指纹、范围和证据是否匹配，评审者复核内容及听看质量。

## 当前状态的结构

根对象使用以下字段。文件记录统一为 `{"path":"绝对或相对状态文件的路径","sha256":"文件SHA-256"}`。

- `workflow_version` 固定为 1。
- `source` 最新输入的文件记录，另含 `duration` 和经探测得到的 `has_audio`。
- `request` 包含 `id`、`user_text`、`source_sha256`、`visual_scopes`、`visual_ranges` 和 `requirements`。范围用可读唯一ID；visual_ranges按范围ID列本轮源时间线上的秒数区间，例如 `{"片头":[[0,17]]}`。要求为 `id / user_text / acceptance`，内容直接对应本轮用户请求。要求 ID 避开 `technical`、`visual`、`audio`、`playback`，这四个是报告的固定检查项；例如用 `keep-original-audio` 表示保留原声。
- `reviews` 每条包含 `scope`、`source_sha256`、`request_sha256`、`ranges`、`frames`（文件记录列表）、`status` 和 `basis`。每张帧另记在本轮源时间线上的实际 `at` 秒。检查要求 `start <= at < end`，即出点仅表示截断。ranges 须与当前确认范围一致，request_sha256 用脚本函数 `request_fingerprint(request)` 计算。请求内容改变后重核确认依据。确认后 `status=approved`，basis 记录 `kind / user_text`。kind 可为 `keyframe_review`、`directed_change`、`explicit_skip`。精确修改可用 directed_change，explicit_skip 需要本人明确跳过看帧的指令。
- `output` 当前输出文件记录，导出后填写。附带SRT等交付项放在 `output.attachments`，逐个保存文件记录。
- `verification` 包含 `source_sha256`、`output_sha256`、`request_id`、`request_sha256`，以及 `requirements`（逐个要求ID对应检查）和 `technical / visual / audio / playback` 四项。
- 每个检查包含 `status`、`method`、`coverage`、`detail` 和 `evidence` 文件记录列表。status取 `passed / partial / failed / not_run / not_applicable`。visual和audio只有实际覆盖本次成片的连续观看、听审才记passed，method分别用 `continuous_visual_review` 和 `continuous_audio_review`；仅有自动分析或抽查时记partial并写覆盖范围。playback通过时用 `user_entry_playback`。视频的技术、画面和播放检查均必需；仅实际无声时，audio可注明not_applicable。
- `history` 可以保存旧状态文件的路径、旧源版本和失效原因；旧确认和验收不自动成为当前版本的证据。

参与本轮制作的录屏、图片、字幕等辅助文件以文件记录形式放在 `request.supporting_sources` 数组里。其指纹随请求保存。重新上传或原地替换时，从最新文件重新探测和校对再更新请求，重新核对受影响的范围。不要只更新指纹而沿用旧帧。只在本轮确实没有辅助输入时省略这项。

## 本轮确认如何记录

- 在 `request.approval_mode` 记录执行分支，未填写时默认 `keyframe_review`。录屏与口播对位、选素材、改变构图或补包装默认走这一路。首轮生成真帧，通过 `keyframes` 后以最终回复交付图片，`reviews.status` 保持 `pending`，等下一条用户消息。
- `keyframe_review` 使用当前聊天中从 1 开始的消息序号。`request.message_index` 是本轮原始请求的位置，`basis.preview_message_index` 是最终回复交付对应图片的位置，`basis.confirmation_message_index` 是用户在其后明确确认该范围的位置。三者按此顺序严格递增。收到确认后再填写 `basis.kind=keyframe_review`、`basis.user_text`（确认原话）和 `status=approved`。无真实用户回复时保留待确认。进度消息、内部抽帧和旧聊天引文不能登记为本轮确认。
- `directed_change` 用于这次用户已精确指定且无需作画面选择的局部修改，`explicit_skip` 用于这次用户明确要求跳过看帧。两者的 `basis.kind` 须与 `request.approval_mode` 一致，`basis.user_text` 必须逐字摘自本轮 `request.user_text`。用户要求先看时，按 `keyframe_review`。用待确认的旧状态发起新制作时，补充真实当轮凭据。
- 检查脚本验证状态字段、指纹和消息顺序，实际发送和确认需从聊天核对。用户同意的部分才能制作。旧状态可保留历史证据，无需把历史确认改写成新聊天消息。

## 检查命令

需要 Python 3.11+，脚本不需要额外 Python 库。将下列 `SKILL_DIR` 与 `PROJECT_DIR` 换成实际目录。可以在任意工作目录调用，状态里的相对文件路径以状态文件所在目录为基准。

```text
python -X utf8 "SKILL_DIR/scripts/validate_edit_plan.py" --stage keyframes "PROJECT_DIR/当前确认位置.json"
python -X utf8 "SKILL_DIR/scripts/validate_edit_plan.py" --stage render "PROJECT_DIR/当前确认位置.json"
python -X utf8 "SKILL_DIR/scripts/validate_edit_plan.py" --stage render "PROJECT_DIR/当前确认位置.json" --scope "片头"
python -X utf8 "SKILL_DIR/scripts/validate_edit_plan.py" --stage deliver "PROJECT_DIR/当前确认位置.json"
```

用户本轮上传新文件时，加 `--expected-source "用户明确给出的文件路径"`，防止拿旧版本运行检查。不带stage的原调用仍检查工程时间线。

- keyframes检查最新输入与请求的版本绑定，不检查样帧文件是否已经生成。仅有视频还没有任务目标时，先确认目标，不运行本次请求检查。
- render进一步检查每个待制作范围是否有对应样帧和有效确认。
- deliver检查当前输出、逐项要求和四种检查是否有同版证据。退出码非零时，依据具体缺口修复或据实交付待核版本，不能把它写成完全通过。

只制作部分已确认范围时，给 `render` 传实际准备导出的每个 `--scope`，范围需来自当前请求。试片时间线只能覆盖这些时间段。复核试片后明确标注对应区间和未确认的部分。整片的 `render` 与 `deliver` 检查仍核对全部范围。

工程时间线的素材层可使用 `speech_end` 记录实测语句尾音。若素材比该时间早退出，检查会报错。句尾来自当前音频或已核对转写，不能照抄计划里的素材出点。

## 如何记录真实证据

- 技术报告保存实际输入、输出路径和检查范围；示例是全片解码、音频包比较或修改区间逐帧检查。
- 每项evidence须含一个 `kind=verification_report` 的JSON文件记录。报告正文保存检查当时的source_sha256、output_sha256、request_sha256，以及checks对象。checks按要求ID或technical/visual/audio/playback记录实际status、method、coverage，并关联当时的原始证据。多项可共用一个报告。脚本同时核对报告内部的被检对象及结果，禁止用更新状态摘要的方法把旧报告重新归给新文件。
- 先从实际检查填一份报告，再将相同结果写入状态并附上报告指纹。`checks` 是对象，例如 `{"keep-original-audio":{"status":"passed","method":"source_waveform_comparison","coverage":"full"}}`，键应与本轮要求 ID 或固定检查项一致。报告的 `checks` 不能用状态里的 `requirements` 数组代替。
- 画面记录写清观看的文件、完整范围或抽查点、发现的问题和修正；截帧对应导出后的文件。
- 听审记录写清实际使用的声音来源、听过的范围和所查内容。自动ASR复核可当辅助证据，并按其实际能力标注。
- 播放记录包含实际入口、播放器、播放时间推进与关键位置检查。只检测到窗口标题尚不足以认定视频已正常播放。
- 用户的确认原话保留在basis，不能由脚本检查通过代替。无法判断确认范围时，先做能做的工作，再问真正有影响的一点。

## 本片例子

“先给我看关键帧”得到的应是待看的真实图片。17秒小样通过而其余画面未确认时，仅覆盖已确认范围。“加字幕”且固定位置已由本人明确指定，按当前新视频出对应字幕预览并执行，不沿用旧视频时间轴。HTML文件在聊天里打开成源码时，交付检查应失败，改用能正常观看的入口后重验。
