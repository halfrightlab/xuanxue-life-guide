"""历法核心：节气、干支、农历。只用 Python 标准库。

玄学生活指南 · 半对实验室 halfrightlab

- 太阳黄经：Meeus《天文算法》第 25 章的低精度公式，节气时刻误差约十几分钟。
- 朔（新月）：Meeus 第 49 章，误差约几分钟。
- 所有日期按北京时间（UTC+8）。交节、合朔落在午夜前后几分钟的，结果可能差一天，脚本会提示。
"""
import datetime as _dt
import math

GAN = '甲乙丙丁戊己庚辛壬癸'
ZHI = '子丑寅卯辰巳午未申酉戌亥'
JIAZI = [GAN[i % 10] + ZHI[i % 12] for i in range(60)]
SHENGXIAO = '鼠牛虎兔龙蛇马羊猴鸡狗猪'
GAN_WX = dict(zip(GAN, '木木火火土土金金水水'))
ZHI_WX = dict(zip(ZHI, '水土木木土火火土金金土水'))
BJ = _dt.timezone(_dt.timedelta(hours=8))
UTC = _dt.timezone.utc

# ───────── 天文 ─────────
def jd_from_dt(t):
    """带时区的 datetime → 儒略日（按 UT 近似，忽略 ΔT 一分钟级差别）"""
    return t.astimezone(UTC).timestamp() / 86400 + 2440587.5


def dt_from_jd(j):
    return _dt.datetime.fromtimestamp((j - 2440587.5) * 86400, UTC)


def sun_lon(j):
    T = (j - 2451545.0) / 36525
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
    M = math.radians(357.52911 + 35999.05029 * T - 0.0001537 * T * T)
    C = ((1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M)
         + (0.019993 - 0.000101 * T) * math.sin(2 * M) + 0.000289 * math.sin(3 * M))
    om = math.radians(125.04 - 1934.136 * T)
    return (L0 + C - 0.00569 - 0.00478 * math.sin(om)) % 360


def term_jd(year, lon):
    """year 年里太阳到达黄经 lon 的时刻（儒略日）。从 year 年 1 月 1 日往后找第一次。"""
    j = jd_from_dt(_dt.datetime(year, 1, 1, tzinfo=UTC))
    j += ((lon - sun_lon(j)) % 360) * 365.2422 / 360
    for _ in range(60):
        d = (lon - sun_lon(j) + 540) % 360 - 180
        if abs(d) < 1e-7:
            break
        j += d * 365.2422 / 360
    return j


TERM_NAMES = ['小寒', '大寒', '立春', '雨水', '惊蛰', '春分', '清明', '谷雨', '立夏', '小满', '芒种', '夏至',
              '小暑', '大暑', '立秋', '处暑', '白露', '秋分', '寒露', '霜降', '立冬', '小雪', '大雪', '冬至']
TERM_LON = [285 + 15 * i for i in range(24)]
TERM_LON = [x % 360 for x in TERM_LON]


def terms_of_year(year):
    """year 年的 24 节气 [(名, 北京时间 datetime)]，按时间排序。"""
    out = [(n, dt_from_jd(term_jd(year, lon)).astimezone(BJ)) for n, lon in zip(TERM_NAMES, TERM_LON)]
    return sorted(out, key=lambda x: x[1])


# 12 个"节"（定月份用）：立春寅月 … 小寒丑月
JIE = [('立春', '寅'), ('惊蛰', '卯'), ('清明', '辰'), ('立夏', '巳'), ('芒种', '午'), ('小暑', '未'),
       ('立秋', '申'), ('白露', '酉'), ('寒露', '戌'), ('立冬', '亥'), ('大雪', '子'), ('小寒', '丑')]
_JIE_ZHI = dict(JIE)
_cache = {}


def jie_list(year):
    """year 前后三年里所有"节"的 (北京时间, 名, 月支)。"""
    if year not in _cache:
        out = []
        for y in (year - 1, year, year + 1):
            for n, t in terms_of_year(y):
                if n in _JIE_ZHI:
                    out.append((t, n, _JIE_ZHI[n]))
        _cache[year] = sorted(out)
    return _cache[year]


def new_moon_jd(k):
    """Meeus 第 49 章：第 k 个朔（k=0 约为 2000-01-06）。"""
    T = k / 1236.85
    jde = (2451550.09766 + 29.530588861 * k + 0.00015437 * T ** 2 - 0.00000015 * T ** 3 + 0.00000000073 * T ** 4)
    E = 1 - 0.002516 * T - 0.0000074 * T ** 2
    r = math.radians
    M = r((2.5534 + 29.10535670 * k - 0.0000014 * T ** 2) % 360)
    Mp = r((201.5643 + 385.81693528 * k + 0.0107582 * T ** 2) % 360)
    F = r((160.7108 + 390.67050284 * k - 0.0016118 * T ** 2) % 360)
    Om = r((124.7746 - 1.56375588 * k + 0.0020672 * T ** 2) % 360)
    corr = (-0.40720 * math.sin(Mp) + 0.17241 * E * math.sin(M) + 0.01608 * math.sin(2 * Mp)
            + 0.01039 * math.sin(2 * F) + 0.00739 * E * math.sin(Mp - M) - 0.00514 * E * math.sin(Mp + M)
            + 0.00208 * E * E * math.sin(2 * M) - 0.00111 * math.sin(Mp - 2 * F) - 0.00057 * math.sin(Mp + 2 * F)
            + 0.00056 * E * math.sin(2 * Mp + M) - 0.00042 * math.sin(3 * Mp) + 0.00042 * E * math.sin(M + 2 * F)
            + 0.00038 * E * math.sin(M - 2 * F) - 0.00024 * E * math.sin(2 * Mp - M) - 0.00017 * math.sin(Om)
            - 0.00007 * math.sin(Mp + 2 * M) + 0.00004 * math.sin(2 * Mp - 2 * F) + 0.00004 * math.sin(3 * M)
            + 0.00003 * math.sin(Mp + M - 2 * F) + 0.00003 * math.sin(2 * Mp + 2 * F) - 0.00003 * math.sin(Mp + M + 2 * F)
            + 0.00003 * math.sin(Mp - M + 2 * F) - 0.00002 * math.sin(Mp - M - 2 * F) - 0.00002 * math.sin(3 * Mp + M)
            + 0.00002 * math.sin(4 * Mp))
    # JDE(TT) → UT：近现代 ΔT 约 1 分钟
    return jde + corr - 69 / 86400


def bj_date(j):
    return dt_from_jd(j).astimezone(BJ).date()


# ───────── 农历 ─────────
_lunar_cache = {}


def _months_between_winters(y):
    """农历：从 y-1 年冬至所在月（十一月）开始，到 y 年冬至所在月之前的各月 [(起始日期, 月号, 是否闰月)]。"""
    if y in _lunar_cache:
        return _lunar_cache[y]
    ws0 = bj_date(term_jd(y - 1, 270))
    ws1 = bj_date(term_jd(y, 270))
    k = math.floor((term_jd(y - 1, 270) - 2451550.09766) / 29.530588861) - 1
    starts = []
    while True:
        d = bj_date(new_moon_jd(k))
        if d > ws1:
            break
        starts.append(d)
        k += 1
    # 冬至所在月：起始日 <= 冬至 的最后一个
    i0 = max(i for i, d in enumerate(starts) if d <= ws0)
    i1 = max(i for i, d in enumerate(starts) if d <= ws1)
    months = starts[i0:i1 + 1]  # 含两头的十一月
    zq = []  # 中气日期（冬至之后的 12 个）
    for yy in (y - 1, y):
        for lon in range(0, 360, 30):
            zq.append(bj_date(term_jd(yy, lon)))
    zq = sorted(set(zq))
    n = len(months) - 1  # 两个十一月之间的月数：12 或 13
    leap_idx = None
    if n == 13:
        for i in range(1, n):
            a, b = months[i], months[i + 1]
            if not any(a <= z < b for z in zq):
                leap_idx = i
                break
    out = []
    num = 11
    for i in range(n):
        if i == leap_idx:
            out.append((months[i], out[-1][1], True))
            continue
        out.append((months[i], num, False))
        num = num % 12 + 1
    _lunar_cache[y] = (out, months[-1])
    return _lunar_cache[y]


NUM_CN = '一二三四五六七八九十'


def month_cn(m, leap=False):
    name = {1: '正', 11: '十一', 12: '腊'}.get(m, NUM_CN[m - 1])
    return ('闰' if leap else '') + name + '月'


def day_cn(d):
    if d <= 10:
        return '初' + NUM_CN[d - 1]
    if d < 20:
        return '十' + NUM_CN[d - 11]
    if d == 20:
        return '二十'
    if d < 30:
        return '廿' + NUM_CN[d - 21]
    return '三十'


def _year_months(y):
    """[(起始日期, 农历年, 月, 闰)]：y-1 年十一月到 y 年十月（含闰月）。"""
    months, end = _months_between_winters(y)
    ny = next(st for st, m, lp in months if m == 1 and not lp)  # y 年正月初一
    return [(st, (y if st >= ny else y - 1), m, lp) for st, m, lp in months], end


def lunar(date):
    """公历日期 → dict(year=农历年(正月初一换年), month, day, leap, ganzhi_year, text)。"""
    for y in (date.year, date.year + 1):
        months, end = _year_months(y)
        if months[0][0] <= date < end:
            st, ly, m, leap = [x for x in months if x[0] <= date][-1]
            d = (date - st).days + 1
            gz = JIAZI[(ly - 1984) % 60]
            return dict(year=ly, month=m, day=d, leap=leap, ganzhi_year=gz,
                        text=f'{gz}年（{ly}）{month_cn(m, leap)}{day_cn(d)}')
    raise ValueError('超出范围')


def lunar_to_solar(year, month, day, leap=False):
    """农历 → 公历。"""
    for y in (year, year + 1):
        months, end = _year_months(y)
        for i, (st, ly, m, lp) in enumerate(months):
            if ly == year and m == month and lp == leap:
                nxt = months[i + 1][0] if i + 1 < len(months) else end
                if day > (nxt - st).days:
                    raise ValueError(f'{month_cn(m, lp)}只有 {(nxt - st).days} 天')
                return st + _dt.timedelta(days=day - 1)
    raise ValueError('找不到这个农历日期（闰月要加 --leap）')


def near_new_moon(date, hours=1):
    """这个日期附近的合朔是否离午夜很近（农历日期可能差一天）。返回合朔北京时间或 None。"""
    k0 = round((jd_from_dt(_dt.datetime(date.year, date.month, date.day, tzinfo=BJ)) - 2451550.09766) / 29.530588861)
    for k in (k0 - 1, k0, k0 + 1):
        t = dt_from_jd(new_moon_jd(k)).astimezone(BJ)
        if abs((t.date() - date).days) <= 30:
            mid = t.replace(hour=0, minute=0, second=0, microsecond=0)
            gap = min(abs((t - mid).total_seconds()), abs((mid + _dt.timedelta(days=1) - t).total_seconds()))
            if gap < hours * 3600 and abs((t.date() - date).days) <= 30:
                return t
    return None


# ───────── 干支 ─────────
_ANCHOR = _dt.date(2025, 1, 5)  # 甲戌日（书中第 377 章的例子）


def day_gz(d):
    return JIAZI[(10 + (d - _ANCHOR).days) % 60]


def year_gz(t):
    """以立春换年。t 为北京时间 datetime。"""
    lc = [x for x, n, z in jie_list(t.year) if n == '立春' and x <= t][-1]
    return JIAZI[(lc.year - 1984) % 60]


def month_info(t):
    """t 所在的节令月：(节名, 交节时刻, 月支)。"""
    cur = None
    for x, n, z in jie_list(t.year):
        if x <= t:
            cur = (n, x, z)
    return cur


def month_gz(t):
    yg = year_gz(t)[0]
    _, _, mz = month_info(t)
    # 五虎遁：甲己之年丙作首……
    start = {'甲': '丙', '己': '丙', '乙': '戊', '庚': '戊', '丙': '庚', '辛': '庚', '丁': '壬', '壬': '壬', '戊': '甲', '癸': '甲'}[yg]
    off = (ZHI.index(mz) - 2) % 12
    return GAN[(GAN.index(start) + off) % 10] + mz


def hour_zhi(h, m=0):
    return ZHI[((h + 1) // 2) % 12]


def hour_gz(dg, h, m=0):
    hz = hour_zhi(h, m)
    start = {'甲': '甲', '己': '甲', '乙': '丙', '庚': '丙', '丙': '戊', '辛': '戊', '丁': '庚', '壬': '庚', '戊': '壬', '癸': '壬'}[dg]
    return GAN[(GAN.index(start) + ZHI.index(hz)) % 10] + hz


def near_boundary(t, hours=2):
    """t 是否离交节时刻很近（排盘可能差一个月）。"""
    for x, n, z in jie_list(t.year):
        if abs((x - t).total_seconds()) < hours * 3600:
            return n, x
    return None


def four_pillars(t):
    """北京时间 datetime → 年月日时四柱。日柱按 0 点换日（23 点后仍算当天，子时按当天日干起）。"""
    d = t.date()
    dg = day_gz(d)
    return dict(year=year_gz(t), month=month_gz(t), day=dg, hour=hour_gz(dg[0], t.hour, t.minute))
