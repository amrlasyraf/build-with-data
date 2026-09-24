# Optional forecasting experiment

This exercise asks: **Can an interpretable model forecast next month's gross
sales by product category and sales channel better than a simple baseline?**
It starts from `silver.sales_enriched`, not Gold, so the modeling dataset can
be defined independently of the reporting table.

Run Bronze and Silver first. Gold is not required for this exercise. Install
the optional model package and run the experiment from the repository root:

```powershell
.\_local\.venv\Scripts\python.exe -m pip install -r step_05_optional\forecasting\requirements.txt
.\_local\.venv\Scripts\python.exe -m step_05_optional.forecasting.run_forecast
```

The program groups Silver sales into monthly category/channel totals. Months
with no rows for an observed category/channel are treated as zero sales. It
excludes the final source month if the source ends before that month's last
calendar day. For the bundled data, February 2021 is partial and excluded.

The final 12 complete months are held out. The model trains only on earlier
months. Each holdout prediction is one month ahead and may use actual sales
from prior holdout months, just as a monthly rerun would. No model fitting uses
holdout targets. This is not a single 12-month-ahead forecast.

Two methods are compared:

- **Seasonal naive:** use sales from the same category/channel 12 months ago.
- **Ridge regression:** use sales from 1 and 12 months ago, the preceding
  3-month average, calendar month, category, and channel. Negative predictions
  are clipped to zero.

The script reports mean absolute error (MAE) and weighted absolute percentage
error (WAPE). It selects the model only if its holdout MAE is lower than the
baseline's; otherwise it keeps the baseline. It then refits the model on all
complete months and produces one forecast for the next month. The selected
method and its forecast are in `_local/forecasts/next_month_forecast.csv`.

With the bundled dataset, the February 2020 through January 2021 holdout gives
the seasonal baseline an MAE of $59,573.22 and WAPE of 147.80%. Ridge improves
MAE to $54,301.74, but its WAPE is still 134.72%. The model wins this limited
comparison, yet both methods have large errors. The February 2021 output is a
historical exercise, **not a decision-ready forecast**.

Inspect these local files:

| File | What to inspect |
|---|---|
| `holdout_predictions.csv` | Actual sales versus both predictions for each test month and segment |
| `metrics.json` | Date split, both error scores, and selected method |
| `next_month_forecast.csv` | Both next-month estimates and the selected value |

The data is a fictional historical sample with a large shift in 2020. A low
error here would not prove that the method works for a present-day retailer.
The derived gross-sales measure uses standard product prices, not actual
receipts after discounts, returns, or tax.
