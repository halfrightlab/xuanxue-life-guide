"""九星吉日计算（玄学生活指南 · tools/jiri.py）

按《改命记实录》第377–381、851章写的金符经九星择日规则，算某个月哪几天是吉日。
节气用天文公式自算（北京时间，精度约几分钟，支持 1901–2100 年）；交节当天按交节后的月份算。

用法：
    python3 jiri.py 2026 11        # 列出 2026 年 11 月每天的干支、九星和是否吉日
    python3 jiri.py 2026 11 --good # 只列吉日

只用 Python 标准库，不用装任何东西。结果仅供民俗参考。
"""
import math, datetime
GAN='甲乙丙丁戊己庚辛壬癸'; ZHI='子丑寅卯辰巳午未申酉戌亥'
JZ=[GAN[i%10]+ZHI[i%12] for i in range(60)]
STAR=['妖星','惑星','禾刀星','煞贡星','直星','卜木星','角己星','人专星','立早星']
def jd(dt):  # UT datetime -> JD
    return dt.timestamp()/86400 + 2440587.5
def sun_lon(j):
    T=(j-2451545.0)/36525
    L0=280.46646+36000.76983*T+0.0003032*T*T
    M=math.radians(357.52911+35999.05029*T-0.0001537*T*T)
    C=(1.914602-0.004817*T-0.000014*T*T)*math.sin(M)+(0.019993-0.000101*T)*math.sin(2*M)+0.000289*math.sin(3*M)
    om=math.radians(125.04-1934.136*T)
    return (L0+C-0.00569-0.00478*math.sin(om))%360
def term_time(year, lon):
    # search near expected date
    guess=datetime.datetime(year,3,20,tzinfo=datetime.timezone.utc)+datetime.timedelta(days=(lon-0)%360*365.2422/360)
    t=guess
    for _ in range(50):
        d=(lon-sun_lon(jd(t))+540)%360-180
        if abs(d)<1e-6: break
        t+=datetime.timedelta(days=d*365.2422/360)
    return t+datetime.timedelta(hours=8)  # Beijing
JIE=[(315,'立春','寅'),(345,'惊蛰','卯'),(15,'清明','辰'),(45,'立夏','巳'),(75,'芒种','午'),(105,'小暑','未'),(135,'立秋','申'),(165,'白露','酉'),(195,'寒露','戌'),(225,'立冬','亥'),(255,'大雪','子'),(285,'小寒','丑')]
def jie_list(y0,y1):
    out=[]
    for y in range(y0,y1+1):
        for lon,name,z in JIE:
            t=term_time(y if lon<300 else y-1 if lon>=315 and False else y, lon)
            out.append((t,name,z))
    # fix year for 立春(315)/小寒(285): term_time(year,lon) searches from Mar 20 of 'year' forward up to a year, so 315 -> Feb of year+1
    return sorted(set(out))
TERMS=jie_list(1900,2100)
def month_of(d):
    # 交节当天算新月
    cur=None
    for t,name,z in TERMS:
        if t.date()<=d: cur=(t,name,z)
    return cur
def year_gz(d):
    lc=[t for t,n,z in TERMS if n=='立春' and t.date()<=d][-1]
    y=lc.year
    return JZ[(y-1984)%60]
ANCHOR=datetime.date(2025,1,5)  # 甲戌（书中例）
def day_gz(d): return JZ[(10+(d-ANCHOR).days)%60]
JS={'甲':'午未','己':'午未','乙':'辰巳','庚':'辰巳','丙':'子丑寅卯','辛':'子丑寅卯','丁':'戌亥','壬':'戌亥','戊':'申酉','癸':'申酉'}
GRP={'寅':0,'巳':0,'申':0,'亥':0,'卯':1,'午':1,'酉':1,'子':1}
HS={0:'酉',1:'巳',2:'丑'}
TX={'壬子','癸丑','丙辰','丁巳','戊午','己未','庚申','辛酉'}
def judge(d):
    y=year_gz(d); t,name,mz=month_of(d); dd=day_gz(d); g=GRP.get(mz,2)
    s=STAR[(g+JZ.index(dd))%9]
    good = s in ('煞贡星','直星','人专星') and dd[1] not in JS[y[0]] and dd[1]!=HS[g]
    return dict(date=d,y=y,mz=mz,dd=dd,star=s,good=good,tx=dd in TX,hong=dd[1]==HS[g],js=dd[1] in JS[y[0]])
if __name__=='__main__':
    import sys, calendar
    if len(sys.argv) < 3:
        print(__doc__); raise SystemExit(1)
    y, mo = int(sys.argv[1]), int(sys.argv[2]); only = '--good' in sys.argv
    print(f'{y} 年 {mo} 月（年、月干支以立春和节气为界）')
    for day in range(1, calendar.monthrange(y, mo)[1] + 1):
        r = judge(datetime.date(y, mo, day))
        if only and not r['good']: continue
        flags = []
        if r['good']: flags.append('吉日')
        if r['tx']: flags.append('偷修日')
        if r['js']: flags.append('金神七煞')
        if r['hong']: flags.append('红煞')
        print(f"{y}-{mo:02d}-{day:02d}  {r['y']}年 {r['mz']}月 {r['dd']}日  {r['star']:<4}  {' '.join(flags)}")
