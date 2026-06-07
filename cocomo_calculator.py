"""
Автоматизированный расчёт технико-экономического обоснования
программного проекта по модели COCOMO II

Контейнер безопасности с AES-256-GCM шифрованием
Вариант №56 — Рощина А.В., группа КП-23-17
РГУ нефти и газа (НИУ) имени И.М. Губкина, 2026
"""

import math
import os
from datetime import datetime

PROJECT = {
    "name": "Контейнер безопасности AES-256-GCM",
    "variant": 56,
    "author": "Рощина А.В.",
    "group": "КП-23-17",
    "year": 2026,
}

NOP_RAW = 174
REUSE_PERCENT = 35
PROD = 13
AVC = 20
A = 3.0
B = 1.12

COEFF = {
    "PERS": 1.00,
    "RCPX": 1.33,
    "RUSE": 1.15,
    "PDIF": 1.00,
    "PREX": 1.00,
    "FCIL": 0.87,
    "SCED": 1.00,
}

ASLOC_FRACTION = 0.15
AA = 2; SU = 20; DM = 25; CM = 30; IM = 30

SALARY_AVG = 300_000
TAX_RATE = 1.30
OVERHEAD_RATE = 1.50

COST_COEFFS = {
    "RELY": 1.39,
    "TIME": 1.00,
    "STOR": 1.00,
    "TOOL": 0.86,
    "EXP":  1.00,
}

PRODUCTIVITY_PUTNAM = 3249
B_PUTNAM = 0.28

PHASES = [
    ("Планирование и анализ требований", 10),
    ("Проектирование архитектуры", 20),
    ("Детальное проектирование", 25),
    ("Кодирование и модульное тестирование", 30),
    ("Интеграционное и системное тестирование", 10),
    ("Внедрение и сопровождение", 5),
]

SIGMA = 4
HOURS_PER_MONTH = 160

# Три параметра Боэма
HW_COST = 2_046_720
TRAVEL_COST = 236_400


def calc_level1():
    nop_adj = NOP_RAW * (1 - REUSE_PERCENT / 100)
    pm = nop_adj / PROD
    return {
        "nop_raw": NOP_RAW, "reuse": REUSE_PERCENT,
        "nop_adj": round(nop_adj, 1), "prod": PROD,
        "pm": round(pm, 2), "prod_lines": PROD * AVC,
    }

def calc_M():
    M = 1.0
    for v in COEFF.values():
        M *= v
    return round(M, 3)

def calc_level2(nop_adj):
    sloc = nop_adj * AVC
    kdsi = sloc / 1000
    M = calc_M()
    pm = A * (kdsi ** B) * M
    return {
        "sloc": round(sloc, 1), "kdsi": round(kdsi, 3),
        "M": M, "kdsi_pow": round(kdsi ** B, 3), "pm": round(pm, 2),
    }

def calc_level3(kdsi_base):
    sloc_base = kdsi_base * 1000
    asloc = ASLOC_FRACTION * sloc_base
    asloc_kdsi = asloc / 1000
    esloc = asloc_kdsi * (AA + SU + 0.4*DM + 0.3*CM + 0.3*IM) / 100
    kdsi_post = kdsi_base + esloc
    M = calc_M()
    pm = A * (kdsi_post ** B) * M
    return {
        "asloc": round(asloc, 1), "asloc_kdsi": round(asloc_kdsi, 3),
        "esloc": round(esloc, 3), "kdsi_post": round(kdsi_post, 3),
        "M": M, "pm": round(pm, 2),
    }

def calc_tdev(pm):
    exp = 0.33 + 0.2 * (B - 1.01)
    tdev = 3 * (pm ** exp)
    return round(tdev, 2), round(exp, 3)

def calc_cost(pm):
    cpm = SALARY_AVG * TAX_RATE * OVERHEAD_RATE
    mult = 1.0
    for v in COST_COEFFS.values():
        mult *= v
    pm_eff = pm * mult
    sc = pm_eff * cpm
    return {
        "cpm": round(cpm, 0), "mult": round(mult, 3),
        "pm_eff": round(pm_eff, 3), "sc": round(sc, 0),
    }

def calc_rayleigh(pm, months):
    K = pm * HOURS_PER_MONTH
    sigma2 = SIGMA ** 2
    raw = []
    for t in range(1, months + 1):
        ft = (t / sigma2) * math.exp(-t**2 / (2 * sigma2))
        raw.append((t, round(ft, 4), round(K * ft, 1)))
    total_raw = sum(r[2] for r in raw)
    k_norm = K / total_raw
    result = []
    cumulative = 0
    for t, ft, et in raw:
        et_norm = round(et * k_norm, 1)
        cumulative += et_norm
        result.append((t, ft, et_norm, round(cumulative, 1)))
    return result, round(K, 1)

def calc_putnam(kdsi_post, tdev):
    size = kdsi_post * 1000
    time_years = tdev / 12
    effort_years = ((size / (PRODUCTIVITY_PUTNAM * (time_years ** (4/3)))) ** 3) * B_PUTNAM
    return {
        "size": round(size, 0), "time_years": round(time_years, 3),
        "effort_years": round(effort_years, 4), "pm": round(effort_years * 12, 2),
    }

def calc_phases(pm):
    return [(name, pct, round(pm * pct / 100, 2)) for name, pct in PHASES]

def calc_putnam_monthly(pm, months):
    putnam_pct = [8.8, 15.5, 19.0, 19.0, 16.5, 12.6, 8.7]
    result = []
    cumulative = 0
    for i in range(min(months, len(putnam_pct))):
        val = round(pm * putnam_pct[i] / 100, 2)
        cumulative += val
        result.append((i + 1, putnam_pct[i], val, round(cumulative, 2)))
    return result


def print_sep(title=""):
    if title:
        print(f"\n{'='*60}\n  {title}\n{'='*60}")
    else:
        print("-" * 60)

def run_calculations():
    print_sep("COCOMO II — ТЕХНИКО-ЭКОНОМИЧЕСКОЕ ОБОСНОВАНИЕ")
    print(f"  Проект: {PROJECT['name']}")
    print(f"  Автор:  {PROJECT['author']}, группа {PROJECT['group']}, {PROJECT['year']} г.")

    print_sep("УРОВЕНЬ 1: ПРЕДВАРИТЕЛЬНОЕ ПРОТОТИПИРОВАНИЕ")
    l1 = calc_level1()
    print(f"  NOP = {l1['nop_raw']}, повторное использование = {l1['reuse']}%")
    print(f"  NOP скорр. = {l1['nop_adj']}, PROD = {l1['prod']}")
    print(f"  PM = {l1['nop_adj']} / {l1['prod']} = {l1['pm']} чел.-мес.")
    print(f"  Производительность = {l1['prod_lines']} строк/чел.-мес.")

    print_sep("УРОВЕНЬ 2: ПРЕДВАРИТЕЛЬНОЕ ПРОЕКТИРОВАНИЕ")
    l2 = calc_level2(l1['nop_adj'])
    M = calc_M()
    print(f"  SLOC = {l2['sloc']}, KDSI = {l2['kdsi']}, M = {M}")
    print(f"  PM = {A} × {l2['kdsi_pow']} × {M} = {l2['pm']} чел.-мес.")

    print_sep("УРОВЕНЬ 3: ПОСТАРХИТЕКТУРНЫЙ")
    l3 = calc_level3(l2['kdsi'])
    print(f"  ESLOC = {l3['esloc']} KDSI, KDSI_пост = {l3['kdsi_post']}")
    print(f"  PM = {A} × {l3['kdsi_post']}^{B} × {M} = {l3['pm']} чел.-мес.")

    print_sep("СВОДНАЯ ТАБЛИЦА ТРЁХ УРОВНЕЙ")
    print(f"  Уровень 1: {l1['pm']} чел.-мес.")
    print(f"  Уровень 2: {l2['pm']} чел.-мес.")
    print(f"  Уровень 3: {l3['pm']} чел.-мес. (итоговый)")

    # PM для TDEV, Рэлея, Путмана и SC — уровень предварительного проектирования
    pm_base = l2['pm']  # 9.96 чел.-мес.

    tdev, tdev_exp = calc_tdev(pm_base)
    print_sep("ДЛИТЕЛЬНОСТЬ ПРОЕКТА (TDEV)")
    print(f"  Базовая PM = {pm_base} чел.-мес. (уровень предварительного проектирования)")
    print(f"  Показатель степени = {tdev_exp}")
    print(f"  TDEV = 3 × {pm_base}^{tdev_exp} = {tdev} месяца")

    print_sep("СТОИМОСТЬ ПЕРСОНАЛА (SC)")
    cost = calc_cost(pm_base)
    print(f"  CPM = {int(cost['cpm']):,} руб./чел.-мес.")
    print(f"  Коэффициенты = {cost['mult']}, PM_эфф = {cost['pm_eff']}")
    print(f"  SC = {int(cost['sc']):,} руб. ≈ {cost['sc']/1_000_000:.2f} млн руб.")

    print_sep("ТРИ ПАРАМЕТРА БОЭМА")
    total = HW_COST + TRAVEL_COST + int(cost['sc'])
    print(f"  1. Аппаратные средства и ПО: {HW_COST:,} руб.")
    print(f"  2. Командировки и обучение:   {TRAVEL_COST:,} руб.")
    print(f"  3. Персонал:                  {int(cost['sc']):,} руб.")
    print(f"  Итого:                        {total:,} руб.")

    months = 7
    rayleigh, K = calc_rayleigh(pm_base, months)
    print_sep("МОДЕЛЬ РЭЛЕЯ")
    print(f"  K = {K} чел.-ч., σ = {SIGMA}")
    for t, ft, et, cum in rayleigh:
        print(f"  Месяц {t}: f(t)={ft:.4f}, E(t)={et:.1f}, итог={cum:.1f}")

    putnam = calc_putnam(l3['kdsi_post'], tdev)
    print_sep("МОДЕЛЬ ПУТМАНА")
    print(f"  PM_Путман = {putnam['pm']} чел.-мес. (COCOMO II уровень 2: {pm_base})")

    phases = calc_phases(pm_base)
    putnam_monthly = calc_putnam_monthly(pm_base, months)

    print_sep()
    print("  Генерация HTML-отчёта...")

    return l1, l2, l3, tdev, cost, rayleigh, K, putnam, phases, putnam_monthly, months, l2['pm']


def generate_html(l1, l2, l3, tdev, cost, rayleigh, K, putnam, phases, putnam_monthly, months, pm_base):
    M = calc_M()
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    total_boehm = HW_COST + TRAVEL_COST + int(cost['sc'])

    rayleigh_labels = str([str(r[0]) for r in rayleigh]).replace("'", '"')
    rayleigh_data   = str([r[2] for r in rayleigh])
    phase_labels    = str([p[0] for p in phases]).replace("'", '"')
    phase_data      = str([p[2] for p in phases])
    pm_monthly_labels = str([str(r[0]) for r in putnam_monthly]).replace("'", '"')
    pm_monthly_data   = str([r[2] for r in putnam_monthly])

    coeff_rows = "\n".join(
        f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in COEFF.items()
    )
    coeff_rows += f"\n<tr class='hl'><td><b>M (итого)</b></td><td><b>{M}</b></td></tr>"

    rayleigh_rows = "\n".join(
        f"<tr><td>{t}</td><td>{ft:.4f}</td><td>{et:.1f}</td><td>{cum:.1f}</td></tr>"
        for t, ft, et, cum in rayleigh
    )
    phase_rows = "\n".join(
        f"<tr><td>{name}</td><td>{pct}%</td><td>{val:.2f}</td></tr>"
        for name, pct, val in phases
    )
    phase_rows += f"\n<tr class='hl'><td><b>Итого</b></td><td><b>100%</b></td><td><b>{pm_base:.2f}</b></td></tr>"

    pm_monthly_rows = "\n".join(
        f"<tr><td>{t}</td><td>{pct}%</td><td>{val:.2f}</td><td>{cum:.2f}</td></tr>"
        for t, pct, val, cum in putnam_monthly
    )
    pm_monthly_rows += f"\n<tr class='hl'><td><b>Итого</b></td><td><b>100%</b></td><td><b>{pm_base:.2f}</b></td><td><b>{pm_base:.2f}</b></td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>COCOMO II — ТЭО контейнера безопасности</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f9; color: #222; }}
header {{ background: #1a3a5c; color: #fff; padding: 28px 40px; }}
header h1 {{ font-size: 20px; font-weight: 600; margin-bottom: 6px; }}
header p {{ font-size: 13px; opacity: 0.75; }}
.container {{ max-width: 1100px; margin: 0 auto; padding: 28px 20px; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 14px; margin-bottom: 28px; }}
.card {{ background: #fff; border-radius: 10px; padding: 18px 20px; border-left: 4px solid #1a3a5c; box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
.card .label {{ font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: .5px; margin-bottom: 5px; }}
.card .value {{ font-size: 26px; font-weight: 700; color: #1a3a5c; }}
.card .sub {{ font-size: 11px; color: #999; margin-top: 3px; }}
section {{ background: #fff; border-radius: 10px; padding: 22px 24px; margin-bottom: 22px; box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
section h2 {{ font-size: 15px; font-weight: 600; color: #1a3a5c; margin-bottom: 6px; padding-bottom: 10px; border-bottom: 2px solid #e8edf3; }}
.chart-subtitle {{ font-size: 12px; color: #888; margin-bottom: 12px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th {{ background: #1a3a5c; color: #fff; padding: 9px 12px; text-align: left; font-weight: 500; }}
td {{ padding: 8px 12px; border-bottom: 1px solid #eef0f3; }}
tr:last-child td {{ border-bottom: none; }}
tr:nth-child(even) td {{ background: #f8f9fb; }}
.hl td {{ background: #e8f0fe !important; font-weight: 600; color: #1a3a5c; }}
.chart-wrap {{ position: relative; margin-top: 14px; }}
.h280 {{ height: 280px; }}
.h380 {{ height: 380px; }}
footer {{ text-align: center; font-size: 11px; color: #aaa; padding: 20px; }}
</style>
</head>
<body>
<header>
  <h1>COCOMO II — Технико-экономическое обоснование</h1>
  <p>{PROJECT['name']} &nbsp;|&nbsp; Вариант №{PROJECT['variant']} &nbsp;|&nbsp; {PROJECT['author']}, группа {PROJECT['group']} &nbsp;|&nbsp; {PROJECT['year']} г.</p>
  <p style="margin-top:5px;opacity:.55;">Сгенерировано: {now}</p>
</header>

<div class="container">

<div class="cards">
  <div class="card">
    <div class="label">NOP объектных точек</div>
    <div class="value">{l1['nop_raw']}</div>
    <div class="sub">скорр. {l1['nop_adj']} (−{l1['reuse']}%)</div>
  </div>
  <div class="card">
    <div class="label">PM постархитектурный</div>
    <div class="value">{pm_base}</div>
    <div class="sub">чел.-мес. (уровень 2, базовый)</div>
  </div>
  <div class="card">
    <div class="label">Длительность TDEV</div>
    <div class="value">{tdev}</div>
    <div class="sub">месяца</div>
  </div>
  <div class="card">
    <div class="label">Стоимость персонала</div>
    <div class="value">{cost['sc']/1_000_000:.2f}</div>
    <div class="sub">млн руб.</div>
  </div>
  <div class="card">
    <div class="label">Совокупные затраты</div>
    <div class="value">{total_boehm/1_000_000:.2f}</div>
    <div class="sub">млн руб. (3 параметра Боэма)</div>
  </div>
</div>

<!-- Три уровня COCOMO -->
<section>
  <h2>Сравнение трёх уровней оценки COCOMO II</h2>
  <table>
    <thead><tr><th>Уровень оценки</th><th>Размер</th><th>PM, чел.-мес.</th></tr></thead>
    <tbody>
      <tr><td>Уровень 1 — Предварительное прототипирование</td><td>NOP = {l1['nop_adj']} точек</td><td>{l1['pm']}</td></tr>
      <tr><td>Уровень 2 — Предварительное проектирование</td><td>KDSI = {l2['kdsi']}</td><td>{l2['pm']}</td></tr>
      <tr class="hl"><td>Уровень 3 — Постархитектурный (итоговый)</td><td>KDSI = {l3['kdsi_post']}</td><td>{l3['pm']}</td></tr>
    </tbody>
  </table>
</section>

<!-- Коэффициенты M -->
<section>
  <h2>Поправочные коэффициенты множителя M</h2>
  <table>
    <thead><tr><th>Коэффициент</th><th>Значение</th></tr></thead>
    <tbody>{coeff_rows}</tbody>
  </table>
</section>

<!-- Стоимость персонала -->
<section>
  <h2>Расчёт стоимости персонала (SC)</h2>
  <table>
    <thead><tr><th>Показатель</th><th>Значение</th></tr></thead>
    <tbody>
      <tr><td>Средняя зарплата специалиста</td><td>{SALARY_AVG:,} руб./мес.</td></tr>
      <tr><td>С учётом налогов и взносов (×{TAX_RATE})</td><td>{int(SALARY_AVG*TAX_RATE):,} руб./мес.</td></tr>
      <tr><td>CPM с накладными расходами (×{OVERHEAD_RATE})</td><td>{int(cost['cpm']):,} руб./чел.-мес.</td></tr>
      <tr><td>RELY × TIME × STOR × TOOL × EXP</td><td>{cost['mult']}</td></tr>
      <tr><td>PM_эфф = {pm_base} × {cost['mult']}</td><td>{cost['pm_eff']} чел.-мес.</td></tr>
      <tr class="hl"><td><b>SC = {cost['pm_eff']} × {int(cost['cpm']):,}</b></td><td><b>{int(cost['sc']):,} руб. ≈ {cost['sc']/1_000_000:.2f} млн руб.</b></td></tr>
    </tbody>
  </table>
</section>

<!-- Аппаратные средства -->
<section>
  <h2>Стоимость аппаратных средств и программного обеспечения</h2>
  <table>
    <thead><tr><th>Статья затрат</th><th>Сумма, руб.</th></tr></thead>
    <tbody>
      <tr><td>Рабочие станции (5 мест × 130 000 ₽)</td><td>650 000</td></tr>
      <tr><td>Лицензионное ПО (ОС, среды разработки)</td><td>100 000</td></tr>
      <tr><td>Открытый стек (Python, Django, Docker, Kubernetes, Prometheus, Grafana)</td><td>0</td></tr>
      <tr><td>Единовременные затраты на платформу разработки</td><td>750 000</td></tr>
      <tr><td>Облачная инфраструктура Timeweb Cloud (в год)</td><td>1 184 220</td></tr>
      <tr><td>Обслуживание рабочих станций и ПО (15% в год)</td><td>112 500</td></tr>
      <tr class="hl"><td><b>Итого за первый год</b></td><td><b>{HW_COST:,}</b></td></tr>
    </tbody>
  </table>
</section>

<!-- Командировки и обучение -->
<section>
  <h2>Расходы на командировки и обучение</h2>
  <table>
    <thead><tr><th>Статья</th><th>Сумма, руб.</th></tr></thead>
    <tbody>
      <tr><td>Обучение специалиста по ИБ (курс по разработке и сертификации СКЗИ)</td><td>100 000</td></tr>
      <tr><td>Обучение инженера DevOps (Kubernetes, управление секретами)</td><td>60 000</td></tr>
      <tr><td>Командировки на пилотные внедрения (2 выезда × 38 200 ₽)</td><td>76 400</td></tr>
      <tr class="hl"><td><b>Итого</b></td><td><b>{TRAVEL_COST:,}</b></td></tr>
    </tbody>
  </table>
</section>

<!-- Три параметра Боэма — сводная -->
<section>
  <h2>Сводная таблица затрат по трём параметрам Боэма</h2>
  <table>
    <thead><tr><th>Параметр</th><th>Сумма, руб.</th></tr></thead>
    <tbody>
      <tr><td>1. Аппаратные средства и ПО (включая обслуживание)</td><td>{HW_COST:,}</td></tr>
      <tr><td>2. Командировки и обучение</td><td>{TRAVEL_COST:,}</td></tr>
      <tr><td>3. Расходы на персонал</td><td>{int(cost['sc']):,}</td></tr>
      <tr class="hl"><td><b>Итого совокупные затраты</b></td><td><b>{total_boehm:,}</b></td></tr>
    </tbody>
  </table>
</section>

<!-- Рисунок 1 — Рэлей -->
<section>
  <h2>Рисунок 1 — Распределение трудоёмкости проекта по модели Рэлея</h2>
  <p class="chart-subtitle">По оси X — месяцы (1–7), по оси Y — трудоёмкость в чел.-ч. σ = {SIGMA}, K = {K} чел.-ч.</p>
  <div class="chart-wrap h280">
    <canvas id="rayleighChart" role="img" aria-label="Кривая Рэлея">Кривая Рэлея.</canvas>
  </div>
  <table style="margin-top:16px;">
    <thead><tr><th>Месяц</th><th>f(t)</th><th>Трудоёмкость, чел.-ч.</th><th>Нарастающий итог, чел.-ч.</th></tr></thead>
    <tbody>{rayleigh_rows}</tbody>
  </table>
</section>

<!-- Рисунок 2 — Фазы -->
<section>
  <h2>Рисунок 2 — Распределение трудоёмкости по фазам жизненного цикла</h2>
  <p class="chart-subtitle">По оси X — фазы проекта, по оси Y — трудоёмкость в чел.-мес.</p>
  <div class="chart-wrap h380">
    <canvas id="phasesChart" role="img" aria-label="Трудоёмкость по фазам">Фазы.</canvas>
  </div>
  <table style="margin-top:16px;">
    <thead><tr><th>Фаза</th><th>Доля</th><th>Трудоёмкость, чел.-мес.</th></tr></thead>
    <tbody>{phase_rows}</tbody>
  </table>
</section>

<!-- Рисунок 3 — Путман помесячно -->
<section>
  <h2>Рисунок 3 — Помесячное распределение трудоёмкости по модели Путмана</h2>
  <p class="chart-subtitle">По оси X — месяцы (1–7), по оси Y — трудоёмкость в чел.-мес.</p>
  <div class="chart-wrap h280">
    <canvas id="putnamChart" role="img" aria-label="Помесячное распределение Путмана">Путман.</canvas>
  </div>
  <table style="margin-top:16px;">
    <thead><tr><th>Месяц</th><th>Доля усилий</th><th>Трудоёмкость, чел.-мес.</th><th>Нарастающий итог, чел.-мес.</th></tr></thead>
    <tbody>{pm_monthly_rows}</tbody>
  </table>
</section>

<!-- Путман сводка -->
<section>
  <h2>Модель Путмана — сводные результаты</h2>
  <table>
    <thead><tr><th>Параметр</th><th>Значение</th></tr></thead>
    <tbody>
      <tr><td>Размер (ESLOC)</td><td>{int(putnam['size']):,}</td></tr>
      <tr><td>Длительность (годы)</td><td>{putnam['time_years']}</td></tr>
      <tr><td>Производительность</td><td>{PRODUCTIVITY_PUTNAM:,} ESLOC/(чел.-год)</td></tr>
      <tr><td>Effort (чел.-лет)</td><td>{putnam['effort_years']}</td></tr>
      <tr class="hl"><td><b>PM Путман</b></td><td><b>{putnam['pm']} чел.-мес.</b></td></tr>
      <tr><td>PM COCOMO II (уровень 2)</td><td>{pm_base} чел.-мес.</td></tr>
      <tr><td>Расхождение</td><td>{abs(putnam['pm'] - pm_base):.2f} чел.-мес.</td></tr>
    </tbody>
  </table>
</section>

</div>

<footer>{PROJECT['author']}, группа {PROJECT['group']} &nbsp;|&nbsp; Вариант №{PROJECT['variant']} &nbsp;|&nbsp; {now}</footer>

<script>
new Chart(document.getElementById('rayleighChart').getContext('2d'), {{
  type: 'line',
  data: {{
    labels: {rayleigh_labels},
    datasets: [{{
      data: {rayleigh_data},
      borderColor: '#1a3a5c',
      backgroundColor: 'rgba(26,58,92,0.10)',
      borderWidth: 2.5,
      pointRadius: 5,
      pointBackgroundColor: '#1a3a5c',
      tension: 0.4,
      fill: true
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ title: {{ display: true, text: 'Месяц проекта' }} }},
      y: {{ title: {{ display: true, text: 'чел.-ч.' }}, beginAtZero: true }}
    }}
  }}
}});

new Chart(document.getElementById('phasesChart').getContext('2d'), {{
  type: 'bar',
  data: {{
    labels: {phase_labels},
    datasets: [{{
      data: {phase_data},
      backgroundColor: 'rgba(26,58,92,0.78)',
      borderColor: '#1a3a5c',
      borderWidth: 1
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{
        title: {{ display: true, text: 'Фазы проекта' }},
        ticks: {{ maxRotation: 45, minRotation: 45, font: {{ size: 9 }} }}
      }},
      y: {{ title: {{ display: true, text: 'чел.-мес.' }}, beginAtZero: true }}
    }}
  }}
}});

new Chart(document.getElementById('putnamChart').getContext('2d'), {{
  type: 'line',
  data: {{
    labels: {pm_monthly_labels},
    datasets: [{{
      data: {pm_monthly_data},
      borderColor: '#1a3a5c',
      backgroundColor: 'rgba(26,58,92,0.10)',
      borderWidth: 2.5,
      pointRadius: 5,
      pointBackgroundColor: '#1a3a5c',
      tension: 0.4,
      fill: true
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ title: {{ display: true, text: 'Месяц проекта' }} }},
      y: {{ title: {{ display: true, text: 'чел.-мес.' }}, beginAtZero: true }}
    }}
  }}
}});
</script>
</body>
</html>"""
    return html


if __name__ == "__main__":
    l1, l2, l3, tdev, cost, rayleigh, K, putnam, phases, putnam_monthly, months, pm_base = run_calculations()
    html = generate_html(l1, l2, l3, tdev, cost, rayleigh, K, putnam, phases, putnam_monthly, months, pm_base)
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  HTML-отчёт сохранён: {output_path}")
    print(f"  Откройте report.html в браузере.")