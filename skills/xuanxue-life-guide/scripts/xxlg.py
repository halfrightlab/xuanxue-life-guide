#!/usr/bin/env python3
"""玄学生活指南 查书与计算工具 · 半对实验室 halfrightlab

只用 Python 3.8+ 标准库。所有规则来自《改命记实录》，出处写在每个命令的输出里。

  查书
    xxlg.py where                         指南内容在哪（没有就提示怎么取）
    xxlg.py fetch                         把指南内容浅克隆到 ~/.cache/xuanxue-life-guide
    xxlg.py search 失眠 [词2…] [--in book|docs|chapters] [--limit 12]
    xxlg.py entry 4 1                     第 4 节第 1 条全文
    xxlg.py entry --title 烤大蒜          按标题找条目
    xxlg.py doc 八颗星 [--section 凶星怎么化]   长文全文或其中一节
    xxlg.py chapter 827                   原书第 827 章的白话笔记
    xxlg.py sections                      14 节和长文目录

  计算
    xxlg.py minggong 1990 男              命宫、东四/西四命
    xxlg.py star 3 7                      两个数字组成哪颗星
    xxlg.py room --door 东北 --bed 北 [--birth 1990 --sex 女]   卧室门、床头、命宫的八星；床头朝哪最好
    xxlg.py number 13812345678 --sex 男   手机号/微信号/密码的八星
    xxlg.py plate 粤B141 --sex 男         车牌：八星 + 河图 + 外五行 + 相冲/八绝
    xxlg.py bazi 1990-08-15 14:30 [--sex 男]   四柱、日干本性、月令、喜用神、财库、床头朝向
    xxlg.py liunian 2026 --birth 1990 --sex 男 [--xiyong 木,火]
    xxlg.py chenggu 1990-08-15 14:30      称骨（自动换算农历；也可 --lunar 1990-6-25 --hour 未）
    xxlg.py zeri 2026 11 [--good]         九星吉日（去金神七煞、红煞，标偷修日）
    xxlg.py age 45                        这个年龄对应房子的哪一宫
    xxlg.py lunar 2026-10-20 | lunar --to-solar 2026-9-11 [--leap]
"""
import argparse
import datetime as dt
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cal  # noqa: E402

BRAND = '玄学生活指南 · 半对实验室 halfrightlab'
REPO = 'https://github.com/halfrightlab/xuanxue-life-guide.git'
CACHE = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')) / 'xuanxue-life-guide'
SRC = '《改命记实录》'


# ════════════════ 指南内容位置 ════════════════
def find_root(quiet=False):
    cands = []
    if os.environ.get('XXLG_ROOT'):
        cands.append(Path(os.environ['XXLG_ROOT']))
    here = Path(__file__).resolve()
    cands += list(here.parents)
    cands += [Path.cwd()] + list(Path.cwd().parents)
    cands.append(CACHE)
    for c in cands:
        if (c / 'book').is_dir() and (c / 'docs').is_dir() and (c / 'README.md').is_file():
            return c
    if quiet:
        return None
    sys.exit('找不到指南内容。运行 `python3 xxlg.py fetch` 取一份（需要 git 和网络），'
             '或者设置环境变量 XXLG_ROOT 指向仓库根目录。')


def cmd_where(a):
    r = find_root(quiet=True)
    print(r if r else '没有找到指南内容；运行 fetch 取一份。')


def cmd_fetch(a):
    if (CACHE / '.git').is_dir():
        subprocess.run(['git', '-C', str(CACHE), 'pull', '--ff-only', '-q'], check=False)
    else:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', 'clone', '--depth', '1', '-q', REPO, str(CACHE)], check=True)
    print('指南内容在', CACHE)


# ════════════════ 解析 ════════════════
def book_sections(root):
    out = []
    for p in sorted((root / 'book').glob('*.md')):
        m = re.match(r'(\d+)-(.+)\.md$', p.name)
        if not m:
            continue
        text = p.read_text(encoding='utf-8')
        entries = []
        for em in re.finditer(r'^### (\d+)\. (.+?)\n(.*?)(?=^### |\Z)', text, re.S | re.M):
            body = re.sub(r'<!--.*?-->\n?', '', em.group(3)).strip()
            entries.append(dict(no=int(em.group(1)), title=em.group(2).strip(), body=body))
        out.append(dict(no=int(m.group(1)), name=m.group(2), path=p, entries=entries,
                        intro=text.split('### ', 1)[0]))
    return out


def docs(root):
    out = []
    for p in sorted((root / 'docs').rglob('*.md')):
        if p.name == 'README.md':
            continue
        text = p.read_text(encoding='utf-8')
        t = re.search(r'^# (.+)$', text, re.M)
        out.append(dict(title=t.group(1).strip() if t else p.stem, path=p, text=resolve_notes(text)))
    return out


def chapters(root):
    out = []
    for p in sorted((root / 'chapters').rglob('*.md')):
        if p.name == 'README.md':
            continue
        text = p.read_text(encoding='utf-8')
        for m in re.finditer(r'^## (.+?)\n(.*?)(?=^## |\Z)', text, re.S | re.M):
            out.append(dict(head=m.group(1).strip(), body=m.group(2).strip(), path=p))
    return out


def resolve_notes(text):
    """把长文里的 [^N] 换成（第X章），并去掉文末脚注定义。"""
    defs = {}
    for m in re.finditer(r'^\[\^(\d+)\]: (.+)$', text, re.M):
        chs = re.findall(r'(第\d+章|番外[^《]*)《', m.group(2))
        defs[m.group(1)] = '、'.join(dict.fromkeys(c.strip() for c in chs)) or '原书'
    text = re.sub(r'^\[\^\d+\]: .+$\n?', '', text, flags=re.M)
    return re.sub(r'\[\^(\d+)\]', lambda m: f"（{defs.get(m.group(1), '原书')}）", text)


def rel(root, p):
    return str(p.relative_to(root))


def strip_md(s):
    s = re.sub(r'!\[[^\]]*\]\([^)]*\)', '[图]', s)
    s = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', s)
    return s


# ════════════════ 搜索 ════════════════
SYN = [
    ['失眠', '睡不着', '睡不好', '睡不踏实', '多梦', '噩梦', '鬼压床', '早醒'],
    ['咳嗽', '咳', '有痰', '黄痰', '嗓子', '喉咙', '扁桃体'],
    ['牙痛', '牙疼', '牙龈', '口腔', '口腔溃疡', '护牙'],
    ['拉肚子', '腹泻', '便秘', '肠胃', '胃痛', '胃不好', '消化', '肠道', '胃胀'],
    ['腰痛', '腰疼', '腰不好', '颈椎', '肩周', '肩膀', '膝盖', '关节', '背痛'],
    ['脚气', '灰指甲', '皲裂', '干裂', '湿疹', '皮肤', '起疹子', '痘', '掉头发', '脱发'],
    ['痔疮', '便血'],
    ['抑郁', '焦虑', '情绪', '想不开', '生气', '烦躁', '内耗', '心情不好'],
    ['缺角', '缺宫', '补角', '凸角'],
    ['鱼缸', '养鱼', '水'],
    ['床', '床头', '卧室', '睡向'],
    ['大门', '门', '入户门', '窗户', '窗'],
    ['厕所', '卫生间', '洗手间'],
    ['厨房', '炉灶', '灶'],
    ['镜子', '镜'],
    ['煞', '化煞', '路冲', '尖角', '穿堂煞'],
    ['手机号', '电话号码', '微信号', '密码', '尾号', '号码'],
    ['车牌', '车牌号'],
    ['名字', '姓名', '起名', '改名'],
    ['头像', '微信头像'],
    ['择日', '吉日', '挑日子', '哪天', '好日子', '偷修', '动土', '搬家'],
    ['八字', '日干', '月令', '喜用神', '排盘'],
    ['命宫', '东四命', '西四命', '婚配', '合不合'],
    ['流年', '运势', '哪年顺', '今年'],
    ['八星', '八颗星', '延年', '天乙', '天医', '生气', '伏位', '绝命', '五鬼', '六煞', '祸害'],
    ['象数', '念数字'],
    ['骗', '骗局', '大师', '师父', '改运', '收费', '法事', '还阴债'],
    ['孩子', '小孩', '宝宝', '长个', '夜哭', '考试', '学习'],
    ['财运', '财库', '求财', '赚钱', '破财', '存不住钱'],
    ['借钱', '借给', '借出', '借了', '担保', '欠钱', '还钱', '借款'],
    ['桃花', '婚姻', '对象', '分手', '感情', '离婚'],
    ['站桩', '练功', '功法', '六字诀', '升阳'],
    ['烧香', '供奉', '神像', '佛像', '还愿', '烧纸', '祖先'],
    ['端午', '正阳水', '午时水', '阴阳水'],
    ['香蕉', '大蒜', '蜂蜜', '醋', '冰糖'],
]


def expand(terms):
    out = []
    for t in terms:
        out.append(t)
        for g in SYN:
            if t in g:
                out += [x for x in g if x != t and len(x) >= 2]
    seen, res = set(), []
    for t in out:
        if t not in seen:
            seen.add(t)
            res.append(t)
    return res


def score(text, title, terms, primary):
    s = 0
    for t in terms:
        w = 3 if t in primary else 1
        if t in title:
            s += 6 * w
        s += min(text.count(t), 5) * w
    return s


def snippet(text, terms, width=60):
    text = strip_md(text).replace('\n', ' ')
    for t in terms:
        i = text.find(t)
        if i >= 0:
            a = max(0, i - width // 2)
            return ('…' if a else '') + text[a:a + width] + ('…' if a + width < len(text) else '')
    return text[:width]


def cmd_search(a):
    root = find_root()
    terms = expand(a.words)
    primary = set(a.words)
    where = a.within
    hits = []
    if where in ('all', 'book'):
        for s in book_sections(root):
            for e in s['entries']:
                sc = score(e['title'] + e['body'], e['title'], terms, primary)
                if sc:
                    hits.append((sc, 'book', f"第 {s['no']} 节第 {e['no']} 条", e['title'], rel(root, s['path']), snippet(e['body'], terms)))
    if where in ('all', 'docs'):
        for d in docs(root):
            for sec in re.split(r'(?=^## )', d['text'], flags=re.M):
                h = re.match(r'## (.+)', sec)
                head = h.group(1).strip() if h else '开头'
                sc = score(sec, d['title'] + head, terms, primary)
                if sc:
                    hits.append((sc * 0.9, 'docs', f"长文《{d['title']}》", head, rel(root, d['path']), snippet(sec, terms)))
    if where in ('all', 'chapters'):
        for c in chapters(root):
            sc = score(c['body'], c['head'], terms, primary)
            if sc:
                hits.append((sc * 0.6, 'chapters', '逐章笔记', c['head'], rel(root, c['path']), snippet(c['body'], terms)))
    hits.sort(key=lambda x: -x[0])
    print(f'【{BRAND}】搜索：{" ".join(a.words)}（连同近义词：{"、".join(t for t in terms if t not in primary)[:80] or "无"}）')
    if not hits:
        print('三处都没有找到。换个说法再搜；仍然没有，就照实说书里没写。')
        return
    for kind, label in (('book', '方法条目'), ('docs', '长文'), ('chapters', '逐章笔记')):
        group = [h for h in hits if h[1] == kind][:a.limit]
        if not group:
            continue
        print(f'\n== {label} ==')
        for sc, _, ref, title, path, snip in group:
            print(f'- {ref}｜{title}  （{path}）\n    {snip}')


def cmd_entry(a):
    root = find_root()
    secs = book_sections(root)
    found = []
    for s in secs:
        for e in s['entries']:
            if a.title and a.title in e['title']:
                found.append((s, e))
            elif not a.title and s['no'] == a.section and e['no'] == a.item:
                found.append((s, e))
    if not found:
        sys.exit('没有这一条。用 search 先查条号。')
    for s, e in found[:5]:
        print(f"【{BRAND}】第 {s['no']} 节《{s['name']}》第 {e['no']} 条：{e['title']}\n{strip_md(e['body'])}\n")


def cmd_doc(a):
    root = find_root()
    ds = [d for d in docs(root) if a.title in d['title']]
    if not ds:
        sys.exit('没有这篇长文。可用的标题见 `sections`。')
    d = ds[0]
    text = d['text']
    if a.section:
        parts = re.split(r'(?=^## )', text, flags=re.M)
        parts = [p for p in parts if p.startswith('## ') and a.section in p.split('\n', 1)[0]]
        if not parts:
            heads = re.findall(r'^## (.+)$', text, re.M)
            sys.exit('这篇里没有这一节。小标题有：' + '、'.join(heads))
        text = '\n'.join(parts)
    print(f"【{BRAND}】长文《{d['title']}》（{rel(root, d['path'])}）\n")
    print(strip_md(text))


def cmd_chapter(a):
    root = find_root()
    key = str(a.no)
    for c in chapters(root):
        if re.match(rf'第{key}章\b', c['head']) or (not key.isdigit() and key in c['head']):
            print(f"【{BRAND}】{SRC}{c['head']}（逐章笔记，{rel(root, c['path'])}）\n\n{strip_md(c['body'])}")
            return
    sys.exit('没找到这一章。')


def cmd_sections(a):
    root = find_root()
    print(f'【{BRAND}】方法（book/）')
    for s in book_sections(root):
        print(f"  {s['no']:>2}. {s['name']}（{len(s['entries'])} 条）")
    print('长文（docs/）')
    for d in docs(root):
        print(f"  - {d['title']}  （{rel(root, d['path'])}）")


# ════════════════ 八颗星 ════════════════
STAR_PAIRS = {
    '延年': ['19', '34', '78', '26'], '天乙': ['13', '49', '68', '27'], '生气': ['14', '39', '67', '28'],
    '六煞': ['16', '47', '29', '38'], '祸害': ['17', '23', '89', '46'], '五鬼': ['18', '36', '79', '24'],
    '绝命': ['12', '37', '48', '69'],
}
STAR_INFO = {
    '延年': ('吉', '金', '能干、有担当、升职', '强势、压力大；心脏、头、睡眠、肩颈背扛压'),
    '天乙': ('吉', '土', '善良包容、财运、正桃花', '花钱没顾忌、容易被骗；影响心脑血管'),
    '生气': ('吉', '木', '乐观、有贵人和机缘，利学习（文昌）', '懒散粗心，久了伤肠胃'),
    '伏位': ('平', '木', '延续前面的气场', '持续消耗，焦虑、没安全感'),
    '六煞': ('凶', '水', '观察细、心思细腻、会沟通', '情绪低落、自卑、抑郁、烂桃花；手脚凉、拉肚子'),
    '祸害': ('凶', '土', '—', '钻牛角尖、爱面子、耳根软、招小人；喉咙胸腔、身上长"土包"'),
    '五鬼': ('凶', '火', '有才华、点子多', '失眠多梦、火气大、易突发病；小孩夜哭'),
    '绝命': ('凶', '金', '敢想敢做、敢拼', '脾气冲、破财、破婚、伤身体'),
}
STAR_FIX = {'五鬼': '生气（用乐观化火气）', '绝命': '天乙（用善良化暴脾气）', '六煞': '延年（用责任和担当化过度敏感）', '祸害': '天乙、生气（用善良和乐观化嘴犟）'}
GONG = {1: '坎1（正北）', 2: '坤2（西南）', 3: '震3（正东）', 4: '巽4（东南）', 5: '中5', 6: '乾6（西北）', 7: '兑7（正西）', 8: '艮8（东北）', 9: '离9（正南）'}


def star_of(x, y):
    x, y = int(x), int(y)
    if x == y:
        return '伏位'
    k = f'{min(x, y)}{max(x, y)}'
    for s, ps in STAR_PAIRS.items():
        if k in ps:
            return s
    return None


def norm5(d, sex):
    if d != '5':
        return d
    if sex in ('男', 'm', 'M'):
        return '2'
    if sex in ('女', 'f', 'F'):
        return '8'
    return None


def cmd_star(a):
    s = star_of(a.x, a.y)
    if not s:
        sys.exit('有 0 或 5 的组合书里另有说法：0 跳过，5 男当 2、女当 8。')
    lvl, wx, good, bad = STAR_INFO[s]
    print(f'【{BRAND}】{a.x} 和 {a.y} 组成 **{s}**（{lvl}，{wx}）\n- 好的一面：{good}\n- 太重了：{bad}')
    if s in STAR_FIX:
        print(f'- 化法：用{STAR_FIX[s]}压')
    print(f'出处：{SRC}第 490、487–489、890、892 章；长文《八颗星》')


def analyse_digits(raw, sex):
    digits = [c for c in raw if c.isdigit()]
    notes = []
    seq = []
    for c in digits:
        if c == '0':
            continue
        n = norm5(c, sex)
        if n is None:
            notes.append('号码里有 5，没给性别：5 男当 2、女当 8（书里另一种说法是 5 代表加强），先按跳过算。')
            continue
        seq.append(n)
    pairs = []
    prev = None
    for i in range(len(seq) - 1):
        x, y = seq[i], seq[i + 1]
        if x == y:
            s = prev or '伏位'  # 伏位延续前一个气场
            pairs.append((x + y, '伏位→' + s if prev else '伏位', s))
        else:
            s = star_of(x, y)
            pairs.append((x + y, s, s))
            prev = s
    return seq, pairs, notes


def print_star_report(raw, sex):
    seq, pairs, notes = analyse_digits(raw, sex)
    print(f'处理后的数字：{"".join(seq)}（0 跳过；5 男当 2、女当 8）')
    from collections import Counter
    cnt = Counter(p[2] for p in pairs if p[2])
    for k, label, eff in pairs:
        lvl = STAR_INFO[eff][0] if eff in STAR_INFO else ''
        print(f'  {k}：{label}（{lvl}）')
    print('统计：' + '，'.join(f'{k} {v}' for k, v in cnt.most_common()))
    tail = pairs[-2:]
    print('后三位（影响大）：' + '、'.join(f'{k} {lab}' for k, lab, _ in tail))
    bad = [k for k in ('绝命', '五鬼', '六煞', '祸害') if cnt.get(k)]
    if bad:
        print('要留意：' + '；'.join(f'{k}（{STAR_INFO[k][3]}），可用{STAR_FIX[k]}' for k in bad))
    if cnt.get('天乙', 0) >= 5:
        print('天乙很多：书里说一个号码 7 个天乙反而容易花钱没顾忌、轻信被骗。')
    for n in notes:
        print('注意：' + n)
    print('作者建议：先改头像、微信号、锁屏密码这些容易改的，别急着换手机号、车牌；吉星不是越多越好。')
    return pairs


def cmd_number(a):
    print(f'【{BRAND}】号码 {a.number} 的八颗星')
    print_star_report(a.number, a.sex)
    print(f'出处：{SRC}第 359、627、655、832 章；长文《手机号、微信号和车牌》《八颗星》')


HETU = {1: '水', 6: '水', 2: '火', 7: '火', 3: '木', 8: '木', 4: '金', 9: '金', 5: '土', 0: '土'}
WAI = {1: '水', 2: '水', 3: '土', 4: '木', 5: '木', 6: '火', 7: '火', 8: '土', 9: '土', 10: '金', 11: '金', 12: '水'}
BAJUE = {(1, 8), (1, 9), (7, 11), (7, 12), (4, 10), (3, 5), (3, 6), (2, 6)}


def cmd_plate(a):
    raw = a.plate.upper()
    letters_as_num = ''.join(str(ord(c) - 64) if c.isalpha() and c.isascii() else (c if c.isdigit() else '') for c in raw)
    only_digits = ''.join(c for c in raw if c.isdigit())
    print(f'【{BRAND}】车牌 {a.plate}')
    print('一、八星（只看数字）：')
    print_star_report(only_digits, a.sex)
    if any(c.isalpha() and c.isascii() for c in raw):
        print('\n   另一种看法，把字母换成数字（A=1、B=2…Z=26）：' + letters_as_num)
        print_star_report(letters_as_num, a.sex)
    ds = [int(c) for c in only_digits]
    print('\n二、河图五行（1、6 水，2、7 火，3、8 木，4、9 金，5、10 土）：' + ''.join(HETU[d] for d in ds))
    wai = [WAI.get(d) for d in ds if d]
    print('三、外五行（数字 1～12 对应子到亥；2 算水、3 算土、5 算木、9 算土、11 算金）：' + ''.join(w for w in wai if w))
    warn = []
    for i in range(len(ds) - 1):
        x, y = ds[i], ds[i + 1]
        if x and y and abs(x - y) == 6:
            warn.append(f'{x}-{y} 相冲')
        if (min(x, y), max(x, y)) in BAJUE:
            warn.append(f'{x}-{y} 八绝')
    print('四、相冲/八绝：' + ('；'.join(warn) if warn else '相邻数字里没有'))
    print('挑的原则：数字之间不要相克，五行尽量是自己的喜用神；避开相冲和八绝。作者提醒：避开重要的冲克就挺好，术是小术。')
    print(f'出处：{SRC}第 915 章；长文《手机号、微信号和车牌》')


DIR_GONG = {'北': 1, '正北': 1, '坎': 1, '西南': 2, '坤': 2, '东': 3, '正东': 3, '震': 3, '东南': 4, '巽': 4,
            '西北': 6, '乾': 6, '西': 7, '正西': 7, '兑': 7, '东北': 8, '艮': 8, '南': 9, '正南': 9, '离': 9}


def to_gong(x):
    x = str(x).strip()
    if x.isdigit() and int(x) in GONG and int(x) != 5:
        return int(x)
    if x in DIR_GONG:
        return DIR_GONG[x]
    sys.exit(f'看不懂方位"{x}"：写 北/东北/东/东南/南/西南/西/西北，或 1–9（不含 5）。')


def cmd_room(a):
    door = to_gong(a.door)
    print(f'【{BRAND}】卧室门在 {GONG[door]}' + (f'，床头朝 {GONG[to_gong(a.bed)]}' if a.bed else ''))
    me = None
    if a.birth and a.sex:
        me, steps = minggong(a.birth, norm_sex(a.sex))
        print(f'你的命宫：{GONG[me]}（{group(me)}；{steps}）')
    if a.bed:
        bed = to_gong(a.bed)
        s = star_of(door, bed)
        print(f'门和床头：{door}{bed} → **{s}**（{STAR_INFO[s][0]}）；{STAR_INFO[s][3] if STAR_INFO[s][0] == "凶" else STAR_INFO[s][2]}')
        if me:
            s2 = star_of(me, bed)
            s3 = star_of(me, door)
            print(f'命宫和床头：{me}{bed} → {s2}（{STAR_INFO[s2][0]}）；命宫和门：{me}{door} → {s3}（{STAR_INFO[s3][0]}）')
        print('三组里以门和床最重要。')
    print('\n床头朝各个方向（以门为准' + ('，另列和命宫的关系' if me else '') + '）：')
    for g in (1, 2, 3, 4, 6, 7, 8, 9):
        s = star_of(door, g)
        line = f'  朝{GONG[g]}：和门成 {s}（{STAR_INFO[s][0]}）'
        if me:
            s2 = star_of(me, g)
            line += f'；和命宫成 {s2}（{STAR_INFO[s2][0]}）'
        print(line)
    sq = [g for g in (1, 2, 3, 4, 6, 7, 8, 9) if star_of(door, g) == '生气']
    print(f'学习位（按开门位置找"生气"）：{GONG[sq[0]]}，书桌或床可以放这一格。' if sq else '')
    print('先用指南针贴墙校准方向、按比例画好九宫再看；方向错了，吉位就成了凶位。一次只动一处，动完观察几天。')
    print(f'出处：{SRC}第 485、488、544、545、756 章；长文《八颗星》《卧室和床》')


# ════════════════ 命宫、流年 ════════════════
def digit_root(n):
    s = sum(int(c) for c in str(n))
    while s > 9:
        s -= 9
    return s


def minggong(year, sex):
    s = digit_root(year)
    if sex == '男':
        g = 11 - s
    else:
        g = 4 + s
    while g > 9:
        g -= 9
    steps = f'{"+".join(str(year))}={sum(int(c) for c in str(year))}→{s}；' + (f'男 11−{s}' if sex == '男' else f'女 4+{s}') + f'→{g}'
    if g == 5:
        g = 2 if sex == '男' else 8
        steps += f'，得 5 {"男改 2" if sex == "男" else "女改 8"}'
    return g, steps


def group(g):
    return '东四命' if g in (1, 3, 4, 9) else '西四命'


def norm_sex(s):
    if s in ('男', 'm', 'M', 'male'):
        return '男'
    if s in ('女', 'f', 'F', 'female'):
        return '女'
    sys.exit('性别写 男 或 女。')


def cmd_minggong(a):
    sex = norm_sex(a.sex)
    g, steps = minggong(a.year, sex)
    print(f'【{BRAND}】{a.year} 年出生的{sex}性：命宫 **{GONG[g]}**，属于{group(g)}')
    print(f'算法：{steps}')
    print('东四命 1、3、4、9；西四命 2、6、7、8。命宫、房门、床的方向最好在同一组。')
    if a.other:
        osex, oy = a.other.split(':') if ':' in a.other else ('女' if sex == '男' else '男', a.other)
        og, osteps = minggong(int(oy), norm_sex(osex))
        st = star_of(g, og)
        print(f'对方 {oy} 年{osex}性：命宫 {GONG[og]}（{group(og)}；{osteps}）')
        print(f'两人命宫组成：{st}（{STAR_INFO[st][0]}）；{"同一组，更合拍" if group(g) == group(og) else "不同组"}')
        print('书里的顺序：先用属相去掉相冲相害的，再看命宫是不是同一组。婚配像"英语"这一科，重要但不是全部。')
    print(f'出处：{SRC}第 264–266 章；长文《命宫婚配》《八颗星》')


def cmd_liunian(a):
    sex = norm_sex(a.sex)
    yg, ysteps = minggong(a.year, sex)
    mg, _ = minggong(a.birth, sex)
    st = star_of(yg, mg)
    gz = cal.JIAZI[(a.year - 1984) % 60]
    print(f'【{BRAND}】{a.year}（{gz}）年的流年，{a.birth} 年出生的{sex}性')
    print(f'办法一：年运命宫 {GONG[yg]}（{ysteps}），你的命宫 {GONG[mg]}，组成 **{st}**（{STAR_INFO[st][0]}）')
    if st == '绝命':
        print('  书里说走到绝命年会有"一百个理由"想辞职、离婚，或碰上暴富的好生意——那是磁场在干扰情绪，要冷静。')
    zwx = cal.ZHI_WX[gz[1]]
    print(f'办法二：当年地支 {gz[1]} 属{zwx}。', end='')
    if a.xiyong:
        xs = [x.strip() for x in re.split('[,，、]', a.xiyong) if x.strip()]
        print('是你的喜用神，一般较顺。' if zwx in xs else '不是你给的喜用神；如果是忌神，一般不顺。')
    else:
        print('先用 bazi 查出喜用神再对照：是喜用就顺，是忌神就不顺。')
    print('办法三：能克你月令五行的年份一般比较顺（用 bazi 看月令）。')
    print('作者的话：运势低时韬光养晦；拿自己经历过的年份对照验证，别自己吓自己。')
    print(f'出处：{SRC}第 369、688、903 章；长文《流年：哪年顺哪年不顺》')


# ════════════════ 八字 ════════════════
RIGAN = {
    '甲': ('阳木', '直直向上的大树', '耿直、要强、不占便宜也不求人、硬气、容易得罪人'),
    '乙': ('阴木', '盘旋向上的藤蔓', '外柔内固执、能随机应变、善用人脉、心软'),
    '丙': ('阳火', '太阳', '热情慷慨、乐观；性急、没心机、缺耐心'),
    '丁': ('阴火', '星星、蜡烛', '外柔内热、有上进心；敏感多疑、慢热；灵性强'),
    '戊': ('阳土', '山石、容器', '包容厚重、重诚信、靠谱；不善变通'),
    '己': ('阴土', '田土、管道', '大度、外柔内固执、心里多疑'),
    '庚': ('阳金', '刀剑', '刚硬倔强、好面子、讲义气、闲不住'),
    '辛': ('阴金', '首饰', '儒雅细腻、有韧性、自尊心强、经不起打击'),
    '壬': ('阳水', '江河', '有冲劲、爱自由、变通强、野心大'),
    '癸': ('阴水', '雨露、杯中水', '温柔、能屈能伸、心思细'),
}
KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}       # 我克
KE_BY = {v: k for k, v in KE.items()}                                     # 克我
CAIKU = {'水': '辰', '木': '未', '火': '戌', '金': '丑'}
BED = {'火': '朝南或东', '水': '朝北或西', '木': '朝东或北', '金': '朝西'}
SEASON = {'木': '金年、秋天', '火': '水年、冬天', '金': '火年、夏天', '水': '土年、季末', '土': '木年、春天'}


def parse_dt(d, t):
    y, m, dd = [int(x) for x in re.split('[-/.]', d)]
    hh, mm = (12, 0)
    if t:
        hh, mm = [int(x) for x in t.split(':')]
    return dt.datetime(y, m, dd, hh, mm, tzinfo=cal.BJ), bool(t)


def cmd_bazi(a):
    t, has_time = parse_dt(a.date, a.time)
    p = cal.four_pillars(t)
    dg = p['day'][0]
    yin, xiang, xing = RIGAN[dg]
    mz = p['month'][1]
    mwx = cal.ZHI_WX[mz]
    xi = KE_BY[mwx]
    print(f'【{BRAND}】{t:%Y-%m-%d %H:%M}（北京时间）出生')
    print(f"四柱：{p['year']}年 {p['month']}月 {p['day']}日 " + (f"{p['hour']}时" if has_time else '（没给时辰，时柱不排）'))
    nb = cal.near_boundary(t, 3)
    if nb:
        print(f'注意：出生时刻离 {nb[0]}（{nb[1]:%m-%d %H:%M}）不到 3 小时，月柱可能差一个月；书里也说节气交接前后有的网站会算错，建议再用"问真八字"核对。')
    print(f'\n1) 日干 {dg}（{yin}，像{xiang}）：{xing}')
    print('   阳干的人主动、直接、急；阴干的人沉得住气、想得多、容易生闷气。这只是本性，不是贴标签。')
    print(f'2) 月令 {mz}，{mwx}旺：{SEASON[mwx]}一般比较顺（"损有余"的简便看法，特殊格局不适用，要拿自己最顺和最不顺的年份验证）。')
    print(f'3) 喜用神（简便法：克月令的五行）：**{xi}**；忌神（和月令同类）：{mwx}')
    print(f'   用法：物品材质、衣服颜色、行业、城市方向选{xi}；床头{BED.get(xi, "书里没写这一项")}。不用追求极致。')
    cai = KE[cal.GAN_WX[dg]]
    ku = CAIKU.get(cai)
    chars = ''.join(p.values()) if has_time else p['year'] + p['month'] + p['day']
    if ku:
        has = ku in chars
        print(f'4) 财星：日干{cal.GAN_WX[dg]}克{cai}，财星是{cai}；{cai}库是"{ku}"，八字里{"有" if has else "没有"}，{"有" if has else "没有"}财库。')
    else:
        print(f'4) 财星：日干{cal.GAN_WX[dg]}克{cai}，财星是{cai}；书里没写{cai}的库是哪个字。')
    print('\n作者的态度：八字像人生地图、像"起手牌"，能看到哪里有弯有坑，不能断定一定掉进去。')
    print('排法说明：年以立春换、月以节换、日按 0 点换日、时柱按五鼠遁；子时（23 点后）各家有分歧，这里仍算当天。')
    print(f'出处：{SRC}第 417、418、545、685–689 章；长文《八字入门：从一个字开始》')


# ════════════════ 称骨 ════════════════
CG_YEAR = {
    '壬申': 7, '甲申': 5, '丙申': 5, '戊申': 14, '庚申': 8, '乙亥': 9, '丁亥': 16, '己亥': 9, '辛亥': 17, '癸亥': 6,
    '己巳': 5, '辛巳': 6, '癸巳': 7, '乙巳': 7, '丁巳': 6, '甲子': 12, '丙子': 16, '戊子': 15, '庚子': 7, '壬子': 5,
    '丁卯': 7, '己卯': 19, '辛卯': 12, '癸卯': 12, '乙卯': 8, '庚午': 9, '壬午': 8, '甲午': 15, '丙午': 13, '戊午': 19,
    '癸酉': 8, '乙酉': 15, '丁酉': 14, '己酉': 5, '辛酉': 16, '乙丑': 9, '丁丑': 8, '己丑': 7, '辛丑': 7, '癸丑': 7,
    '戊辰': 12, '庚辰': 12, '壬辰': 10, '甲辰': 8, '丙辰': 8, '辛未': 8, '癸未': 7, '乙未': 6, '丁未': 5, '己未': 6,
    '甲戌': 15, '丙戌': 6, '戊戌': 14, '庚戌': 9, '壬戌': 10, '丙寅': 6, '戊寅': 8, '庚寅': 9, '壬寅': 9, '甲寅': 12,
}
CG_MONTH = [6, 7, 18, 9, 5, 16, 9, 15, 18, 8, 9, 5]
CG_DAY = [5, 10, 8, 15, 16, 15, 8, 16, 8, 16, 9, 17, 8, 17, 10, 8, 9, 18, 5, 15, 10, 9, 8, 9, 15, 18, 7, 8, 16, 6]
CG_HOUR = dict(zip(cal.ZHI, [16, 6, 7, 10, 9, 16, 10, 8, 8, 9, 6, 6]))


def liang(q):
    """重量（钱）→ 书里的写法：四两八钱、三两、九钱。"""
    cn = '零一二三四五六七八九'
    a, b = divmod(q, 10)
    return (f'{cn[a]}两' if a else '') + (f'{cn[b]}钱' if b else '')


def cmd_chenggu(a):
    if a.lunar:
        ly, lm, ld = [int(x) for x in re.split('[-/.]', a.lunar)]
        hz = a.hour
        if not hz:
            sys.exit('用 --lunar 时还要给 --hour 时辰（子丑寅卯…）。')
        leap = a.leap
        lgz = cal.JIAZI[(ly - 1984) % 60]
        src = f'农历 {ly} 年{cal.month_cn(lm, leap)}{cal.day_cn(ld)} {hz}时'
    else:
        t, has_time = parse_dt(a.date, a.time)
        if not has_time:
            sys.exit('称骨要用出生时辰，请给出时间，比如 14:30。')
        L = cal.lunar(t.date())
        ly, lm, ld, leap, lgz = L['year'], L['month'], L['day'], L['leap'], L['ganzhi_year']
        hz = cal.hour_zhi(t.hour, t.minute)
        src = f'公历 {t:%Y-%m-%d %H:%M} = 农历 {L["text"]} {hz}时'
        nm = cal.near_new_moon(t.date())
        if nm:
            src += f'（注意：这个月的合朔在 {nm:%m-%d %H:%M}，离午夜很近，农历日期可能差一天，建议用万年历核对）'
    y = CG_YEAR[lgz]
    m = CG_MONTH[lm - 1]
    d = CG_DAY[ld - 1]
    h = CG_HOUR[hz]
    total = y + m + d + h
    print(f'【{BRAND}】称骨：{src}')
    print(f'年 {lgz} {liang(y)} + 月 {cal.month_cn(lm)} {liang(m)} + 日 {cal.day_cn(ld)} {liang(d)} + 时 {hz} {liang(h)} = **{liang(total)}**')
    if leap:
        print('出生在闰月：书里的表没写闰月怎么算，这里按同名月份算。')
    root = find_root(quiet=True)
    if root:
        p = root / 'docs' / '05-算时间' / '20-称骨算命歌诀.md'
        if p.exists():
            for line in p.read_text(encoding='utf-8').splitlines():
                cells = [c.strip() for c in line.strip('|').split('|')]
                if len(cells) == 3 and cells[0] == liang(total):
                    print(f'一句话：{cells[1]}\n歌诀：{cells[2].replace("<br>", "")}')
    print('作者的提醒：重量大说的是生活安稳、福气大；成大事的人磨难多，很多伟人只有三两多。骨轻不等于命不好。')
    print(f'出处：{SRC}第 155、804 章（称骨表见第 155 章插图）；长文《称骨算命歌诀》')


# ════════════════ 择日 ════════════════
STAR9 = ['妖星', '惑星', '禾刀星', '煞贡星', '直星', '卜木星', '角己星', '人专星', '立早星']
GOOD9 = ('煞贡星', '直星', '人专星')
JINSHEN = {'甲': '午未', '己': '午未', '乙': '辰巳', '庚': '辰巳', '丙': '子丑寅卯', '辛': '子丑寅卯', '丁': '戌亥', '壬': '戌亥', '戊': '申酉', '癸': '申酉'}
GRP = {'寅': 0, '巳': 0, '申': 0, '亥': 0, '卯': 1, '午': 1, '酉': 1, '子': 1}
HONG = {0: '酉', 1: '巳', 2: '丑'}
TOUXIU = {'壬子', '癸丑', '丙辰', '丁巳', '戊午', '己未', '庚申', '辛酉'}


def judge(d):
    t = dt.datetime(d.year, d.month, d.day, 12, tzinfo=cal.BJ)
    yg = cal.year_gz(t)
    _, _, mz = cal.month_info(t)
    dd = cal.day_gz(d)
    g = GRP.get(mz, 2)
    star = STAR9[(g + cal.JIAZI.index(dd)) % 9]
    js = dd[1] in JINSHEN[yg[0]]
    hong = dd[1] == HONG[g]
    jq = any(x.date() == d for x, n, z in cal.jie_list(d.year))
    return dict(date=d, y=yg, mz=mz, dd=dd, star=star, good=star in GOOD9 and not js and not hong, tx=dd in TOUXIU, js=js, hong=hong, jq=jq)


def cmd_zeri(a):
    import calendar
    print(f'【{BRAND}】{a.year} 年 {a.month} 月九星吉日（金符经九星择日法；年以立春、月以节气为界）')
    n = 0
    for day in range(1, calendar.monthrange(a.year, a.month)[1] + 1):
        r = judge(dt.date(a.year, a.month, day))
        if a.good and not r['good']:
            continue
        flags = [x for x, k in (('吉日', 'good'), ('偷修日', 'tx'), ('金神七煞', 'js'), ('红煞', 'hong'), ('交节当天，上午下午月份可能不同，重要的事避开或再核对', 'jq')) if r[k]]
        n += r['good']
        print(f"{r['date']}  {r['y']}年 {r['mz']}月 {r['dd']}日  {r['star']:<4} {' '.join(flags)}")
    print(f'共 {n} 个吉日。要动"煞位"（比如凶方动土）最好再赶上偷修日；凑不齐就退而求其次。')
    print('作者的话：日子本身没有吉凶，要看什么人干什么事；嫌麻烦至少避开红煞日。')
    print(f'出处：{SRC}第 375–381、851、905 章；长文《择日：九星吉日怎么算》')


# ════════════════ 其他 ════════════════
AGE_GONG = [(8, '艮8（东北）'), (3, '震3（正东）'), (4, '巽4（东南）'), (9, '离9（正南）'), (2, '坤2（西南）'), (7, '兑7（正西）'), (6, '乾6（西北）'), (1, '坎1（正北）')]


def cmd_age(a):
    i = ((a.age - 1) // 9) % 8 if a.age > 0 else 0
    g = AGE_GONG[i]
    lo = (a.age - 1) // 9 * 9 + 1 if a.age > 0 else 0
    print(f'【{BRAND}】{a.age} 岁走在 **{g[1]}** 这一段（{lo}–{lo + 8} 岁）')
    print('书里说九宫从东北艮宫开始，每格 9 岁，顺时针转一圈。自己走到哪个年龄段，房子对应的方位尽量不要缺。')
    print('第 814 章的图里第一段写的是"0–9"，书里没说是虚岁还是周岁，边界附近两格都看一下。')
    print(f'出处：{SRC}第 315、814、889 章；长文《房子和人的年龄》')


def cmd_lunar(a):
    if a.to_solar:
        y, m, d = [int(x) for x in re.split('[-/.]', a.to_solar)]
        s = cal.lunar_to_solar(y, m, d, a.leap)
        print(f'农历 {y} 年{cal.month_cn(m, a.leap)}{cal.day_cn(d)} = 公历 {s}（{cal.day_gz(s)}日）')
    else:
        y, m, d = [int(x) for x in re.split('[-/.]', a.date)]
        x = dt.date(y, m, d)
        L = cal.lunar(x)
        print(f'公历 {x} = 农历 {L["text"]}（{cal.day_gz(x)}日）')
        nm = cal.near_new_moon(x)
        if nm:
            print(f'注意：这个月的合朔在 {nm:%m-%d %H:%M}，离午夜很近，农历日期可能差一天。')


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser(prog='xxlg.py', description=BRAND + '：查书与计算', formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sp = ap.add_subparsers(dest='cmd', required=True)
    sp.add_parser('where').set_defaults(f=cmd_where)
    sp.add_parser('fetch').set_defaults(f=cmd_fetch)
    p = sp.add_parser('search'); p.add_argument('words', nargs='+'); p.add_argument('--in', dest='within', default='all', choices=['all', 'book', 'docs', 'chapters']); p.add_argument('--limit', type=int, default=8); p.set_defaults(f=cmd_search)
    p = sp.add_parser('entry'); p.add_argument('section', type=int, nargs='?'); p.add_argument('item', type=int, nargs='?'); p.add_argument('--title'); p.set_defaults(f=cmd_entry)
    p = sp.add_parser('doc'); p.add_argument('title'); p.add_argument('--section'); p.set_defaults(f=cmd_doc)
    p = sp.add_parser('chapter'); p.add_argument('no'); p.set_defaults(f=cmd_chapter)
    sp.add_parser('sections').set_defaults(f=cmd_sections)
    p = sp.add_parser('minggong'); p.add_argument('year', type=int); p.add_argument('sex'); p.add_argument('--other', help='对方，如 女:1992'); p.set_defaults(f=cmd_minggong)
    p = sp.add_parser('star'); p.add_argument('x'); p.add_argument('y'); p.set_defaults(f=cmd_star)
    p = sp.add_parser('room'); p.add_argument('--door', required=True); p.add_argument('--bed'); p.add_argument('--birth', type=int); p.add_argument('--sex'); p.set_defaults(f=cmd_room)
    p = sp.add_parser('number'); p.add_argument('number'); p.add_argument('--sex'); p.set_defaults(f=cmd_number)
    p = sp.add_parser('plate'); p.add_argument('plate'); p.add_argument('--sex'); p.set_defaults(f=cmd_plate)
    p = sp.add_parser('bazi'); p.add_argument('date'); p.add_argument('time', nargs='?'); p.add_argument('--sex'); p.set_defaults(f=cmd_bazi)
    p = sp.add_parser('liunian'); p.add_argument('year', type=int); p.add_argument('--birth', type=int, required=True); p.add_argument('--sex', required=True); p.add_argument('--xiyong'); p.set_defaults(f=cmd_liunian)
    p = sp.add_parser('chenggu'); p.add_argument('date', nargs='?'); p.add_argument('time', nargs='?'); p.add_argument('--lunar'); p.add_argument('--hour'); p.add_argument('--leap', action='store_true'); p.set_defaults(f=cmd_chenggu)
    p = sp.add_parser('zeri'); p.add_argument('year', type=int); p.add_argument('month', type=int); p.add_argument('--good', action='store_true'); p.set_defaults(f=cmd_zeri)
    p = sp.add_parser('age'); p.add_argument('age', type=int); p.set_defaults(f=cmd_age)
    p = sp.add_parser('lunar'); p.add_argument('date', nargs='?'); p.add_argument('--to-solar'); p.add_argument('--leap', action='store_true'); p.set_defaults(f=cmd_lunar)
    a = ap.parse_args(argv)
    if a.cmd == 'entry' and not a.title and (a.section is None or a.item is None):
        ap.error('entry 要给 节号 条号，或者 --title')
    a.f(a)


if __name__ == '__main__':
    try:
        main()
    except BrokenPipeError:
        pass
