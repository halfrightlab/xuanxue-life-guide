# 让 AI 照书回答（skill）

装上这个 skill，Claude Code 或 Codex 就会在你问"咳嗽带黄痰怎么办""北边缺角怎么补""下个月哪天适合挪床"时，先去《玄学生活指南》里查条目再回答，注明出自第几节第几条、原书第几章。查不到就直说书里没写。

## 装到 Claude Code

在本仓库里开 Claude Code，不用装：根目录的 `CLAUDE.md` 已经把它指出来了。

想在任何目录下都能用：

```bash
mkdir -p ~/.claude/skills/xuanxue-life-guide && curl -fsSL -o ~/.claude/skills/xuanxue-life-guide/SKILL.md "https://raw.githubusercontent.com/halfrightlab/xuanxue-life-guide/main/skills/xuanxue-life-guide/SKILL.md"
```

之后直接问"牙痛有什么土办法""北边缺角怎么补"就会触发；也可以明说"用 xuanxue-life-guide 回答"。

## 装到 Codex

在本仓库里开 Codex，不用装：根目录的 `AGENTS.md` 已经把它指出来了。

想在任何目录下都能用，复制到 Codex 的个人 skill 目录 `~/.agents/skills`：

```bash
mkdir -p ~/.agents/skills/xuanxue-life-guide && curl -fsSL -o ~/.agents/skills/xuanxue-life-guide/SKILL.md "https://raw.githubusercontent.com/halfrightlab/xuanxue-life-guide/main/skills/xuanxue-life-guide/SKILL.md"
```

之后直接问问题就会自动触发，也可以输入 `$xuanxue-life-guide` 显式调用。没出现就重启一次 Codex。

## 它会怎么答

- 先找最对症的一两条，照条目写清怎么做、用多少；书里没写用量的，照说"书里没写"。
- 把禁忌带上；涉及身体的，提醒先看医生。
- 风水问题先说查哪里，再说怎么调。
- 每条后面注明「见第 N 节第 M 条」。

代码按 [MIT](../../LICENSE-CODE) 许可。
