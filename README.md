# AI Short Drama Skill · 一个人拍 AI 短剧

> 一个给 Claude 用的技能包：把"我想做一集 AI 短剧"变成从剧本到成片的六阶段流水线，附带 9 个可直接复制的提示词模板、3 个填空模板和 1 个成本估算脚本。

## English

An [Agent Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills) for making AI short dramas solo: script format, shot breakdown, character/scene/prop asset sheets with a reusable character board, a shared five-block video prompt structure, platform render settings, voice consistency, CapCut-style editing, and cost control. The content is written in Chinese (the target audience is Chinese short-drama creators); all prompts are copy-paste ready.

The core idea: **cast the actors first, shoot second, edit last.** Character consistency is solved with reference images and written constraints, never left to the video model.

## 它解决什么问题

AI 短剧一个人做，难点从来不是"生成一段视频"，而是**几十段拼在一起还能看**：

- 每段角色长得不一样
- 场景每段都在变
- 角色张嘴把心里话念出来
- 同一个角色声音一会儿一个样
- 道具忽大忽小、人物瞬移
- 一集几十段，抽卡抽到成本失控

这个技能把上面每一条都对应到流水线上的一个具体动作，而不是靠"多抽几次"。

## 安装

技能是纯文本 + 一个 Python 脚本，没有依赖。

### Claude Code

```bash
git clone https://github.com/cheunghohoi/ai-short-drama-skill.git
mkdir -p ~/.claude/skills
cp -r ai-short-drama-skill/skills/ai-short-drama ~/.claude/skills/
```

Windows PowerShell：

```powershell
git clone https://github.com/cheunghohoi/ai-short-drama-skill.git
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills" | Out-Null
Copy-Item -Recurse .\ai-short-drama-skill\skills\ai-short-drama "$env:USERPROFILE\.claude\skills\"
```

### Claude.ai / 桌面端

把 `skills/ai-short-drama` 整个目录压成 zip，在设置里的 Skills（能力）页上传。具体入口以你所用客户端的最新说明为准。

### 其他兼容 Agent Skills 的客户端

把 `skills/ai-short-drama` 目录放进客户端的技能目录即可。`SKILL.md` 的 frontmatter 只有 `name`、`description`、`license`、`metadata` 四个键，不依赖特定实现。

## 怎么用

装好之后直接说人话，技能会自己判断你在哪一阶段：

```text
我想做一集 5 分钟的 AI 短剧，讲讲深夜面馆里的一次对峙，帮我从剧本开始。
```

```text
我的角色每段长得都不一样，怎么办？
```

```text
帮我把这份剧本写成能直接喂给视频模型的提示词。
```

```text
一集 50 段、每段 6 秒、每段抽 3 次，要花多少钱？怎么省？
```

## 六阶段流水线

| 阶段 | 产出 | 过关标准 |
|---|---|---|
| 0 立项 | 一句话故事、画风、单集时长 | 三样都定死 |
| 1 剧本 | `01-script.md` | 心理活动全部外化、台词 750–1000 字、声音分三类 |
| 2 分镜（可选） | `02-storyboard.csv` | 单镜头 ≤ 10 秒、合并出 5–15 秒素材段落 |
| 3 资产图 | 角色图 / 身份板 / 场景 / 道具 | 多角度同一张脸、场景无人、道具写尺寸 |
| 4 出片 | 提示词 + 片段 | 5 秒预览通过再出正式时长 |
| 5 后期 | 剪辑单 + 成片 | 无穿帮、字幕对得上、勾选 AI 声明 |

第一次做不要做整集：技能里有一条**一小时做出第一个 10 秒**的快速通道，跑通再上规模。

## 一致性靠四件套

| 维度 | 锁定手段 |
|---|---|
| 长相 | 角色身份板固定在参考图 1 号位 |
| 空间 | 一段只喂一张场景图，对话戏加站位大全景 |
| 声音 | 每个角色一句写死的声色卡，每段原样复制 |
| 位置 | 每段提示词开头先写【站位】 |

## 仓库结构

```text
ai-short-drama-skill/
├── skills/ai-short-drama/
│   ├── SKILL.md                  # 技能入口：阶段路由、闸门、铁律
│   ├── references/               # 11 篇按需加载的详细说明
│   ├── assets/prompts/           # 9 个可直接复制的提示词模板
│   └── assets/templates/         # 剧本、分镜表、剪辑单的空模板
├── scripts/
│   ├── verify_skill.py           # 结构校验（frontmatter、交叉引用、禁止词）
│   └── cost_estimate.py          # 一集视频成本估算
└── examples/                     # 示例项目
```

## 成本估算

```bash
python scripts/cost_estimate.py --segments 50 --avg-seconds 6 --takes 3
```

输出会给出三个画质档位的单段与整集消耗，并和按秒计费的商用 API 做数量级对比。脚本里所有价格都是**参考值**，用 `--coin-price`、`--api-price`、`--coins-per-clip` 换成你实际看到的价格。

## 校验

```bash
python scripts/verify_skill.py        # 加 -v 显示全部通过项
```

检查 frontmatter、description 长度、文档结构、提示词代码块、禁止词、TODO 残留，以及所有交叉引用是否真实存在。失败时退出码为 1。

## 贡献

欢迎 PR：新增提示词模板、补一个平台的操作说明、修正过时的价格。请遵守：

1. 不贴未经授权的内容；
2. 价格与平台参数标成参考值，并写清观察时间；
3. 提交前跑一遍 `python scripts/verify_skill.py`。

## 参考与致谢

工作流思路来自 X 上的一篇 AI 短剧实战长文（作者 [@TuyetloanP81840](https://x.com/TuyetloanP81840)），本仓库的文字、示例、提示词结构与脚本均为重写和补充，不包含原文段落。原文链接见 [这条推文](https://x.com/TuyetloanP81840/status/2119326884505043274)。

## License

MIT
