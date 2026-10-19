# 玄学生活指南 skill · 半对实验室 halfrightlab

让 Claude Code、Codex 这类 AI 助手照着《玄学生活指南》回答问题：先查书、再算数、最后用大白话答，每一句都注明出自第几节第几条、原书第几章。书里没写的，直说没写，不编用量、不编日子。

## 能做什么

**查书**：353 条方法、73 篇长文、992 章逐章笔记一起搜，自动带近义词（问"睡不着"也会找"失眠""鬼压床"）。

**现场算**（只用 Python 标准库，规则全部来自书里）：

| 问题 | 命令 |
|---|---|
| 命宫、东四命西四命、两人婚配 | `minggong` |
| 两个数字成什么星 | `star` |
| 卧室门、床头、命宫，床头朝哪最好，学习位 | `room` |
| 手机号、微信号、锁屏密码 | `number` |
| 车牌（八星、河图、外五行、相冲八绝） | `plate` |
| 八字四柱、日干本性、喜用神、财库、床头朝向 | `bazi` |
| 某一年顺不顺 | `liunian` |
| 称骨（公历自动换农历） | `chenggu` |
| 九星吉日、偷修日 | `zeri` |
| 这个年纪看房子哪一角 | `age` |
| 公历农历互换 | `lunar` |

**守底线**：急症先叫 120，提到不想活先给心理援助热线 12356，有人借"改运""还阴债"要钱先讲防骗；身体相关的都提醒"先看医生，这些最多当辅助"。

## 装到 Claude Code

在本仓库里开 Claude Code，不用装：根目录的 `CLAUDE.md` 已经把它指出来了。

想在任何目录下都能用：

```bash
git clone --depth 1 https://github.com/halfrightlab/xuanxue-life-guide.git ~/.cache/xuanxue-life-guide
mkdir -p ~/.claude/skills
cp -r ~/.cache/xuanxue-life-guide/skills/xuanxue-life-guide ~/.claude/skills/
```

第一行顺便把指南内容放到了 skill 默认会找的位置。之后直接问"牙痛有什么土办法""北边缺角怎么补""下个月哪天适合挪床"就会触发；也可以明说"用玄学生活指南回答"。

## 装到 Codex

在本仓库里开 Codex，不用装：根目录的 `AGENTS.md` 已经把它指出来了。

想在任何目录下都能用，复制到 Codex 的个人 skill 目录：

```bash
git clone --depth 1 https://github.com/halfrightlab/xuanxue-life-guide.git ~/.cache/xuanxue-life-guide
mkdir -p ~/.agents/skills
cp -r ~/.cache/xuanxue-life-guide/skills/xuanxue-life-guide ~/.agents/skills/
```

之后直接问问题就会自动触发，也可以输入 `$xuanxue-life-guide` 显式调用。没出现就重启一次 Codex。

## 自己用命令行

不用 AI 也能直接跑：

```bash
cd skills/xuanxue-life-guide
python3 scripts/xxlg.py search 失眠
python3 scripts/xxlg.py minggong 1990 女
python3 scripts/xxlg.py zeri 2026 11 --good
python3 scripts/xxlg.py --help          # 全部命令
python3 -m unittest discover -s tests   # 自测
```

## 目录

```
xuanxue-life-guide/
├── SKILL.md              给 AI 的说明：怎么查、怎么算、怎么答
├── scripts/
│   ├── xxlg.py           查书和计算的命令行工具
│   └── cal.py            节气、干支、农历（天文公式自算）
├── references/
│   ├── safety.md         什么时候先停下
│   ├── answer-format.md  回答模板和示例
│   └── topics.md         常见问题从哪查
└── tests/test_xxlg.py    自测，用例取自书里的例子
```

## 精度

节气和朔用天文公式自算，误差在十几分钟以内。出生时间离交节、合朔很近时，月柱或农历日期可能差一天，脚本会提示。

---

半对实验室 halfrightlab 出品 · 代码 [MIT](../../LICENSE-CODE) · 来源《改命记实录》
