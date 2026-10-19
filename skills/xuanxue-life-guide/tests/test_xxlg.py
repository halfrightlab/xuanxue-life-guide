"""玄学生活指南 skill 自测 · 半对实验室 halfrightlab
运行：python3 -m unittest discover -s tests   （在 skill 目录下）
用例都取自书里给的例子，或公认的农历日期。"""
import datetime as dt
import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / 'scripts'))
import cal  # noqa: E402
import xxlg  # noqa: E402


def run(*args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        xxlg.main(list(args))
    return buf.getvalue()


class Minggong(unittest.TestCase):
    def test_book_examples(self):  # 第 264 章
        self.assertEqual(xxlg.minggong(1995, '男')[0], 2)
        self.assertEqual(xxlg.minggong(2018, '女')[0], 6)
        self.assertEqual(xxlg.minggong(1990, '男')[0], 1)
        self.assertEqual(xxlg.minggong(1990, '女')[0], 8)

    def test_liunian_2024(self):  # 第 369 章：2024 男女都是震3，和兑7 成绝命
        self.assertEqual(xxlg.minggong(2024, '男')[0], 3)
        self.assertEqual(xxlg.minggong(2024, '女')[0], 3)
        self.assertEqual(xxlg.star_of(3, 7), '绝命')


class Stars(unittest.TestCase):
    def test_table(self):
        self.assertEqual(xxlg.star_of(1, 9), '延年')
        self.assertEqual(xxlg.star_of(4, 9), '天乙')
        self.assertEqual(xxlg.star_of(8, 2), '生气')
        self.assertEqual(xxlg.star_of(6, 1), '六煞')
        self.assertEqual(xxlg.star_of(8, 1), '五鬼')
        self.assertEqual(xxlg.star_of(3, 3), '伏位')

    def test_zero_and_repeat(self):  # 106 等于 16；166 等于两个 16
        _, pairs, _ = xxlg.analyse_digits('106', '男')
        self.assertEqual([p[2] for p in pairs], ['六煞'])
        _, pairs, _ = xxlg.analyse_digits('166', '男')
        self.assertEqual([p[2] for p in pairs], ['六煞', '六煞'])

    def test_five(self):  # 5 男当 2、女当 8
        self.assertEqual(xxlg.analyse_digits('15', '男')[0], ['1', '2'])
        self.assertEqual(xxlg.analyse_digits('15', '女')[0], ['1', '8'])

    def test_plate_141(self):  # 第 915 章：141 外五行水木水，河图水金水，八星两个生气
        out = run('plate', '141', '--sex', '男')
        self.assertIn('水金水', out)
        self.assertIn('水木水', out)
        self.assertIn('生气 2', out)


class Room(unittest.TestCase):
    def test_book_544(self):  # 第 544 章：艮8 开门、床头朝北，1 和 8 成五鬼
        out = run('room', '--door', '东北', '--bed', '北')
        self.assertIn('五鬼', out)
        self.assertIn('学习位', out)


class Calendar(unittest.TestCase):
    def test_new_year(self):
        cny = {1985: (2, 20), 1990: (1, 27), 2000: (2, 5), 2001: (1, 24), 2010: (2, 14), 2015: (2, 19),
               2019: (2, 5), 2020: (1, 25), 2021: (2, 12), 2022: (2, 1), 2023: (1, 22), 2024: (2, 10),
               2025: (1, 29), 2026: (2, 17)}
        for y, (m, d) in cny.items():
            self.assertEqual(cal.lunar_to_solar(y, 1, 1), dt.date(y, m, d), y)

    def test_leap_months(self):
        self.assertEqual(cal.lunar(dt.date(2023, 3, 22))['leap'], True)
        self.assertEqual(cal.lunar(dt.date(2025, 7, 25))['month'], 6)
        self.assertEqual(cal.lunar(dt.date(2020, 5, 23))['leap'], True)

    def test_day_ganzhi(self):  # 第 377 章：2025-01-05 甲戌
        self.assertEqual(cal.day_gz(dt.date(2025, 1, 5)), '甲戌')
        self.assertEqual(cal.day_gz(dt.date(2025, 1, 29)), '戊戌')

    def test_year_by_lichun(self):
        self.assertEqual(cal.year_gz(dt.datetime(2026, 2, 3, 12, tzinfo=cal.BJ)), '乙巳')
        self.assertEqual(cal.year_gz(dt.datetime(2026, 2, 5, 12, tzinfo=cal.BJ)), '丙午')


class Chenggu(unittest.TestCase):
    def test_sum_and_verse(self):
        out = run('chenggu', '--lunar', '1984-1-1', '--hour', '子')
        self.assertIn('三两九钱', out)  # 甲子 1.2 + 正月 0.6 + 初一 0.5 + 子 1.6


class Zeri(unittest.TestCase):
    def test_2026_11(self):
        good = [d.day for d in (dt.date(2026, 11, i) for i in range(1, 31)) if xxlg.judge(d)['good']]
        self.assertEqual(good, [5, 6, 8, 16, 17, 20, 26, 29])


class Age(unittest.TestCase):
    def test_age(self):
        self.assertIn('坤2', run('age', '45'))
        self.assertIn('艮8', run('age', '5'))
        self.assertIn('坎1', run('age', '70'))


@unittest.skipUnless(xxlg.find_root(quiet=True), '没有正文，跳过查书测试')
class Search(unittest.TestCase):
    def test_synonyms(self):
        out = run('search', '睡不着')
        self.assertIn('失眠', out)
        self.assertIn('第 1 节', out)

    def test_entry(self):
        self.assertIn('烤大蒜', run('entry', '--title', '烤大蒜'))

    def test_doc_footnotes(self):
        out = run('doc', '八颗星')
        self.assertNotIn('[^', out)
        self.assertIn('第490章', out)


if __name__ == '__main__':
    unittest.main()
