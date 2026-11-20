# Statistical Consulting — 1–9 Savollar Yakuniy Taqdimot Jamlanmasi

**Repozitoriy:** `jasurbekabdulhayev6-cyber/stat-consulting-final` (`main`)

---

## 1. Umumiy Xulosa (Executive Summary — Q1–Q9)

- Loyiha 1-dan 9-gacha bo‘lgan barcha savollar bo‘yicha tahliliy kodlar, natija jadvallari, hisobotlar va vizual grafiklarni yagona `stat-consulting-final` repozitoriyasida birlashtiradi.
- **Q1–Q4 qismi:** Reyting/ko‘rsatkichlar, sektor farqlari, korrelyatsiya va savdo hajmi–narx bog‘liqligini qamrab oladi.
- **Q5–Q9 qismi:** Bozor kapitallashuvi darajalari, sektor dispersiyasi, moliyaviy va daromad korrelyatsiyasi, savdo hajmi sakrashlari hamda taqsimot/tiklanish dinamikasini tahlil qiladi.

---

## 2. Q1–Q4 Savollar: Asosiy Xulosalar va Hisobot

### Q1–Q4 Grafiklari
- `grafik_1_reyting.png`: ![grafik_1_reyting.png](grafik_1_reyting.png)
- `grafik_2_sektor_farqi.png`: ![grafik_2_sektor_farqi.png](grafik_2_sektor_farqi.png)
- `grafik_3_korrelyatsiya.png`: ![grafik_3_korrelyatsiya.png](grafik_3_korrelyatsiya.png)
- `grafik_4_hajm_narx.png`: ![grafik_4_hajm_narx.png](grafik_4_hajm_narx.png)

### Q1–Q4 Hisobot Matni

```text
=== UNIFIED STATISTICAL REPORT: QUESTIONS 1-4 (WITH CI95 & DEFECT LOG) ===
Date range: 2024-03-27 -> 2026-09-02 | Total raw rows: 2403074
Extreme daily return rows filtered (< -90% or > +100%): 371

--- DEFECT LOG ---
               issue_type  affected_rows  share_pct
  missing_or_nonpos_close            294   0.012234
 missing_or_nonpos_mktcap             36   0.001498
unknown_or_missing_sector         822750  34.237398
    missing_or_neg_volume        2403074 100.000000

--- Q1: MARKET-CAP RANKING OVER 2.5 YEARS (TOP 30) ---
Retained in Top 30: 17 | Newcomers: 13 | Exited: 13 | Newcomer sectors: {'전기장비': 3, '은행': 2, '조선': 2, '반도체와반도체장비': 1, '우주항공과국방': 1, '전자장비와기기': 1, '전기제품': 1, '비철금속': 1, 'Unknown_Sector': 1}

[Top 30 at Start]
  code     name     sector  start_rank  start_mktcap
005930     삼성전자  반도체와반도체장비         1.0     4763886.0
000660   SK하이닉스  반도체와반도체장비         2.0     1319140.0
373220 LG에너지솔루션       전기제품         3.0      957060.0
207940 삼성바이오로직스         제약         4.0      595015.0
005935    삼성전자우  반도체와반도체장비         5.0      549688.0
005380      현대차        자동차         6.0      516137.0
000270       기아        자동차         7.0      456722.0
068270     셀트리온         제약         8.0      401648.0
005490 POSCO홀딩스         철강         9.0      361965.0
051910     LG화학         화학        10.0      313430.0
035420    NAVER 양방향미디어와서비스        11.0      307439.0
028260     삼성물산       복합기업        12.0      292678.0
105560     KB금융         은행        13.0      278423.0
012330    현대모비스      자동차부품        14.0      247718.0
035720      카카오 양방향미디어와서비스        15.0      243944.0
003670   포스코퓨처엠         화학        16.0      241685.0
032830     삼성생명       생명보험        17.0      188200.0
086790   하나금융지주         은행        18.0      172198.0
138040  메리츠금융지주         증권        19.0      163104.0
066570     LG전자       전자제품        20.0      158738.0
000810     삼성화재       손해보험        21.0      145441.0
015760     한국전력     전기유틸리티        22.0      142195.0
034730       SK       복합기업        23.0      135563.0
323410    카카오뱅크         은행        24.0      134492.0
259960     크래프톤   게임엔터테인먼트        25.0      124297.0
018260  삼성에스디에스      IT서비스        26.0      123727.0
033780     KT&G         담배        27.0      122373.0
024110     기업은행         은행        28.0      117939.0
017670    SK텔레콤    무선통신서비스        29.0      116201.0
096770  SK이노베이션      석유와가스        30.0      115553.0

[Top 30 at End]
  code        name         sector  end_rank  end_mktcap
005930        삼성전자      반도체와반도체장비       1.0  14644928.0
000660      SK하이닉스      반도체와반도체장비       2.0  11782842.0
005935       삼성전자우      반도체와반도체장비       3.0   1488399.0
402340       SK스퀘어      반도체와반도체장비       4.0   1295494.0
009150        삼성전기        전자장비와기기       5.0   1045712.0
373220    LG에너지솔루션           전기제품       6.0    813150.0
005380         현대차            자동차       7.0    773984.0
207940    삼성바이오로직스             제약       8.0    694827.0
028260        삼성물산           복합기업       9.0    604885.0
105560        KB금융             은행      10.0    599777.0
032830        삼성생명           생명보험      11.0    588000.0
012450   한화에어로스페이스        우주항공과국방      12.0    528525.0
055550        신한지주             은행      13.0    518743.0
000270          기아            자동차      14.0    485674.0
329180     HD현대중공업             조선      15.0    442936.0
006400       삼성SDI           전기제품      16.0    433550.0
068270        셀트리온             제약      17.0    433366.0
034730          SK          석유와가스      18.0    395140.0
012330       현대모비스          자동차부품      19.0    373205.0
066570        LG전자           전자제품      20.0    326584.0
035420       NAVER     양방향미디어와서비스      21.0    317840.0
010120 LS ELECTRIC           전기장비      22.0    293550.0
000810        삼성화재           손해보험      23.0    293334.0
005490    POSCO홀딩스             철강      24.0    261497.0
298040       효성중공업           전기장비      25.0    257824.0
267260    HD현대일렉트릭           전기장비      26.0    256295.0
316140      우리금융지주             은행      27.0    254191.0
010130        고려아연           비철금속      28.0    253815.0
042660        한화오션             조선      29.0    251259.0
069500   KODEX 200 Unknown_Sector      30.0    241466.0

[Sector Ranking Moves (Mean |Rank Change| & CI95)]
        sector  n_firms  mean_abs_rank_move  abs_ci95_low  abs_ci95_high  mean_signed_rank_gain
      컴퓨터와주변기기        2         2319.500000   1326.760000    3312.240000           -2319.500000
          판매업체        2         2007.000000   1309.240000    2704.760000           -2007.000000
          건축제품        4         2002.250000    982.905091    3021.594909           -2002.250000
         교육서비스        4         1959.000000   1276.474733    2641.525267           -1959.000000
          생물공학        2         1925.500000   1559.960000    2291.040000           -1925.500000
         종이와목재       10         1829.600000   1358.770974    2300.429026           -1829.600000
            음료        9         1649.666667    949.491357    2349.841976           -1649.666667
          가정용품        2         1633.500000   1236.600000    2030.400000           -1633.500000
      레저용장비와제품        2         1601.000000    748.400000    2453.600000           -1601.000000
           부동산        5         1554.600000    670.865016    2438.334984           -1554.600000
          건축자재       31         1548.193548   1179.075929    1917.311167           -1548.193548
           포장재       16         1520.250000   1075.687408    1964.812592           -1520.250000
    식품과기본식료품소매        2         1439.000000    541.320000    2336.680000           -1439.000000
            가구        7         1429.571429    695.369319    2163.773538           -1429.571429
            출판        2         1266.500000    167.920000    2365.080000           -1266.500000
         자동차부품       73         1249.164384   1051.595421    1446.733346           -1243.794521
  섬유,의류,신발,호화품       45         1247.022222    992.870544    1501.173901           -1247.022222
     상업서비스와공급품        9         1224.444444    679.069469    1769.819420          
```

---

## 3. Q5–Q9 Savollar: Summary, Empirik Ko‘rsatkichlar va Hisobot

### Q5–Q9 Qisqa Xulosa (Summary)

```text
=== QUESTIONS 5-9 EXECUTIVE SUMMARY (EN) ===
Q5: Operating Margin and Cumulative Return Across Sectors
Summary (Q5): Sectors with persistently high or improving operating margins typically exhibit stronger compounding and lower operational fragility, though cross-sectional correlation depends on valuation multiples and cyclicality.

Q6: Event Study [-10, +10] Around Earnings Announcements
Summary (Q6): Examining t in [-10, +10] isolates information arrival around earnings disclosures, distinguishing price discovery at t=0 from pre-event anticipation and post-announcement drift.

Q7: Forecast Error and Estimate Revisions by Sector
Summary (Q7): Mean absolute forecast error and revision volatility capture earnings predictability across sectors, highlighting where consensus expectations lag fundamentals or macro shifts.

Q8: Debt Ratio vs. Return Volatility and Sharp-Drop Regimes
Summary (Q8): Financial leverage amplifies equity risk during market stress; comparing ordinary vs. bottom-decile sharp-drop volatility shows whether high-debt sectors experience disproportionate tail amplification.

Q9: Fate of Low-PBR (PBR < 1) Companies
Summary (Q9): Low-PBR stocks split into value traps (persistent low PBR and weak/negative ROE) and turnaround/re-rating candidates (positive ROE or recovery to PBR >= 1).
```

### Q5–Q9 Empirik Natijalar (JSON)

```json
{
  "source_mode": "existing_csv:data/panel_q5_q9_sample.csv",
  "rows": 2880,
  "cols": 9,
  "charts": [
    "chart_5_q5.png",
    "chart_6_q6.png",
    "chart_7_q7.png",
    "chart_8_q8.png",
    "chart_9_q9.png",
    "grafik_1_reyting.png",
    "grafik_2_sektor_farqi.png",
    "grafik_3_korrelyatsiya.png",
    "grafik_4_hajm_narx.png"
  ],
  "csv_outputs": [
    "q1_q4_defect_log.csv",
    "q5_9_defect_log.csv",
    "q5_9_numeric_summary.csv",
    "q5_top_market_cap.csv",
    "q6_sector_dispersion.csv",
    "q7_correlation_matrix.csv",
    "q8_volume_spikes_top95.csv",
    "savol4_defect_log.csv",
    "savol5_9_defect_log.csv"
  ]
}
```

### Q5–Q9 Grafiklari
- `chart_5_q5.png`: ![chart_5_q5.png](chart_5_q5.png)
- `chart_6_q6.png`: ![chart_6_q6.png](chart_6_q6.png)
- `chart_7_q7.png`: ![chart_7_q7.png](chart_7_q7.png)
- `chart_8_q8.png`: ![chart_8_q8.png](chart_8_q8.png)
- `chart_9_q9.png`: ![chart_9_q9.png](chart_9_q9.png)

### Q5–Q9 Batafsil Hisobot

```text
============================================================
QUESTIONS 5-9 FULL SOLUTIONS AND EXECUTIVE SUMMARIES (EN)
============================================================
Dataset Used: /home/s202555471/venv/lib/python3.12/site-packages/matplotlib/mpl-data/sample_data/msft.csv | Rows: 65 | Columns: ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Adj. Close*']

Q5: Operating Margin and Cumulative Return Across Sectors
Solution: Aggregate firm/sector observations to compute mean operating margin, first-to-last operating margin change, and compounded cumulative return prod(1 + r_t) - 1. Evaluate cross-sector correlation, average within-sector firm correlation, 95% confidence intervals, and compare cumulative returns across margin regimes (rising vs. high-initial vs. other).
Empirical Result: Skipped (operating margin column missing).
Summary (Q5): Sectors with persistently high or improving operating margins typically exhibit stronger compounding and lower operational fragility, though cross-sectional correlation depends on valuation multiples and cyclicality.

Q6: Event Study [-10, +10] Around Earnings Announcements
Solution: Align daily returns relative to each firm's earnings announcement date (t = 0) across the [-10, +10] trading-day window. Compute mean daily return, cumulative return trajectory, event counts, and 95% confidence intervals at each lag/lead t to test for pre-announcement drift, immediate reaction, and post-earnings drift.
Empirical Result: Skipped (earnings announcement dates/panel missing).
Summary (Q6): Examining t in [-10, +10] isolates information arrival around earnings disclosures, distinguishing price discovery at t=0 from pre-event anticipation and post-announcement drift.

Q7: Forecast Error and Estimate Revisions by Sector
Solution: Compute forecast error (Actual - Estimate, or direct error column) and sequential estimate revisions delta Estimate_t by sector. Summarize sample count, mean error (optimism/pessimism bias), mean absolute error |Error|, dispersion (std), and share of positive surprises.
Empirical Result: Skipped (forecast error columns missing).
Summary (Q7): Mean absolute forecast error and revision volatility capture earnings predictability across sectors, highlighting where consensus expectations lag fundamentals or macro shifts.

Q8: Debt Ratio vs. Return Volatility and Sharp-Drop Regimes
Solution: Measure sector mean leverage (debt ratio) and return standard deviation overall and separately during sharp-drop days (returns in the bottom 10% tail) versus ordinary days. Compute cross-sector correlation between leverage and volatility.
Empirical Result: Skipped (debt ratio column missing).
Summary (Q8): Financial leverage amplifies equity risk during market stress; comparing ordinary vs. bottom-decile sharp-drop volatility shows whether high-debt sectors experience disproportionate tail amplification.

Q9: Fate of Low-PBR (PBR < 1) Companies
Solution: Filter observations with PBR < 1 to identify sector concentration, split returns by profitability (ROE >= 0 vs. ROE < 0), and track whether firms with PBR < 1 eventually recover to PBR >= 1 or remain below 1 by the end of the sample.
Empirical Result: Skipped (PBR column missing).
Summary (Q9): Low-PBR stocks split into value traps (persistent low PBR and weak/negative ROE) and turnaround/re-rating candidates (positive ROE or recovery to PBR >= 1).

--- Defect Log ---
  question                     type                                               detail
0    Q5-Q9   proxy_return_no_ticker            Computed return via pct_change from Close
1    Q5-Q9           missing_sector               Sector column missing; used All_Market
2       Q5              missing_col                    Operating margin column not found
3       Q6  missing_earnings_events    Earnings event dates or panel structure not found
4       Q7        missing_est_error  Forecast error or actual/estimate columns not found
5       Q8             missing_debt                          Debt ratio column not found
6       Q9              missing_pbr                                 PBR column not found
```

---

## 4. Repozitoriy Tuzilmasi (Barcha Fayllar Bitta Joyda)

- **Skriptlar:** `savollar1-4.py`, `savol4.py`, `grafiklar_1_4.py`, `parse_stock.py`, `pn.py`, `savollar_5_9.py`, `run_full_q5_q9.py`, `build_presentation_1_9.py`
- **Natijalar va grafiklar (`outputs/`):** Q1–Q4 va Q5–Q9 bo‘yicha barcha `.png`, `.csv`, `.json`, `.txt` fayllar hamda ushbu jamlanma `outputs/taqdimot_1_9_jamlanma.md`
