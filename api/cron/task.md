# Phase 3A — Prediction Finalization Engine

## Step 1: Database Migration
- [/] Create `phase3a_migration.sql`

## Step 2: finalize_closed_week_predictions()
- [ ] get_last_data_week() — epi-time anchor (R1)
- [ ] get_pending_forecasts() — fetch all forecast_week <= last_data_week
- [ ] Closed-week guard in loop
- [ ] Fetch actual_s from ast_weekly_aggregated
- [ ] Direction correctness (prior week comparison)
- [ ] Revision detection (G2)
- [ ] Insert new validation row
- [ ] Commit + log summary

## Step 3: Wire into Stage E
- [ ] Call finalize_closed_week_predictions after Stage B, before Phase 3B

## Step 4: Verification
- [ ] Run Stage E twice — no duplicate rows
- [ ] Manual actual_s change → revision_flag = TRUE
- [ ] Open-week forecasts not validated
- [ ] prediction_error sign correct
