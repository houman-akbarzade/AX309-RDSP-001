# AX309-RDSP-001 — Final Pfa acceptance report (S02 v1.2)

**RESULT PASS** for fixed-sample Empirical Bernstein 95% one-sided upper CPI-mean on software Python reference, not physical FPGA performance.

## Authorization and reproducibility
S02 v1.2 approval Git e88731cd70ae80d755bc26124ad71c67e4f1a8ee; source frozen in Git 51b06a5782972d8be3c5094e92124d319b05aa82 BEFORE data generation.
Approved contract SHA256 6e07ab218cd76f8358d56e3de0bbbc57dc62eff82b702222c0bb47f3b9ca1f3e; matrix SHA256 23f07e63950c8bd4f3b04a805c37a46792b0068ae918b25d0713dd65a15c51a0.
Executable SHA256 12c2a1d404ecac650370a7b12b9a64083bb7b1df22814b8c296e2c1c544331ed; model SHA256 2b4e28c6afaebc5d5240cfc1c80d94bbcbca325b48937ed8a8855087bef85c1b. Preflight 16/16 SHA256 1f88318bed156ef22625ceac3fafa9bc05e2a62c1f34eea6eeeb382f324ea27a.
Original S02 v1.0/v1.1 and failed Student-t 7/15 and spatial anisotropy z=43.575 remain byte-preserved. Historical spatial failure remains FAIL, but its normative prerequisite was superseded in v1.2.

## Prespecified method and observations
Exactly 20000 independent full 33x128 complex Gaussian CPI using fixed master Seed 411091703, fresh PCG64 SeedSequence([411091703,i,191]) for i=0..19999, full MF/MTI/FFT/power/40-training 2D CA-CFAR with frozen alpha 7.476912055027923. Each CPI has 2782 valid CUT. No optional stopping or changing alpha/Delta.
U_EB=min(1, Xbar+sqrt(2*S2*ln(40)/20000)+7*ln(40)/(3*19999)), Xi=Fi/2782, S2 unbiased sample CPI variance.

| Metric | Recorded value |
|---|---:|
| Valid CPI | 20000/20000 |
| Total alarms | 55919 |
| Mean alarms per CPI | 2.79595 |
| Unbiased sample alarm-count variance | 3.9605116230811537 |
| Mean alarm rate | 0.0010050143781452192 |
| Sample variance CPI alarm fractions | 5.117254786058101e-07 |
| EB upper 95% | 0.0014491445035750084 |
| Acceptance limit | 0.0015 |
| Margin limit minus U | 5.085549642499165e-05 |
| Elapsed wall monotonic seconds | 9.503801190003287 |
| Independent NumPy and Welford difference | 4.336808689942018e-19 |

Final PASS under approved source-defined software noise-only CPI generator and its procedural independence. The finite-sample theorem treats whole CPI as the independent unit and permits arbitrary within-CPI CUT correlations. No FPGA board, bittrue, synthesis or timing tests. Pd is still NOT_RUN, Gate-S03 OPEN, progress stays S03 75%, overall 22.9167% pending engineer decision.

Full count vector evidence SHA256 6dab2a8a6669b698a53e74f88105b61169c02f819ac72d3674a94d34aca9cc7f; typed int32 count vector SHA256 75c5977e5288b004cdb3f1682e3ef82ae4f28512a946df6c0c302d080541afb6; single-run claim SHA256 c5a1509709102b8df920efaf8fafb1ea8226913937c12a02b23ad5efcdf5d384.
