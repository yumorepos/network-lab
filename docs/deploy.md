# Deploy

The dashboard is a single Streamlit app that reads precomputed Parquet outputs
under `data/parquet/outputs/`. Those outputs are small (a few MB) and are the
only data the deployed app needs - it never downloads BTS/StatCan or rebuilds
the warehouse in the cloud. Deploys to Streamlit Community Cloud for free.

## One-command local check first

```
make setup && make data && make all && make app
```

`make app` should open at http://localhost:8501 with the Route screen, Market
detail, Validation, Backtest, and About views populated. If it does, the
cloud deploy will too.

## What to commit for the deploy

The app needs the computed outputs, which are normally gitignored. For a
Community Cloud deploy, commit the outputs directory explicitly (it is small):

```
git add -f data/parquet/outputs/*.parquet data/parquet/outputs/*.yaml
git add -f data/parquet/outputs/*.csv
git commit -m "Add precomputed outputs for Streamlit Community Cloud"
```

Do NOT commit `data/raw/`, `data/parquet/db1b/`, `data/parquet/t100/`, or
`data/warehouse.duckdb` - they are large and unnecessary for the app.

## GitHub push (needs your account)

```
gh repo create network-lab --public --source=. --remote=origin --push
# or, against an existing empty repo:
git remote add origin https://github.com/<you>/network-lab.git
git push -u origin main
```

## Streamlit Community Cloud (needs your account)

1. Go to https://share.streamlit.io and sign in with GitHub.
2. "New app" -> pick the `network-lab` repo, branch `main`.
3. Main file path: `app/streamlit_app.py`.
4. Advanced settings -> Python version 3.11.
5. Deploy. First build installs `requirements.txt` (verified to resolve on a
   clean venv) and boots the app; subsequent pushes redeploy automatically.

No secrets or API keys are required. If you later want ACS median household
income instead of the BEA fallback, add `CENSUS_API_KEY` in the app's
Secrets and rebuild the data locally before committing new outputs.

## Runtimes (measured on the build machine)

| step | from scratch | cached |
|---|---|---|
| `make setup` | ~1-2 min | - |
| `make data` | ~50 min (downloads ~2 GB of BTS DB1B/T-100) | ~1 s (raw cached) |
| `make models` | ~35 s | ~35 s |
| `make backtest` | ~5 s | ~5 s |
| `make reports` | ~2 s | ~2 s |
| `make test` | ~4 s | ~4 s |

The cloud app itself does none of this; it loads the committed Parquet outputs
and renders.
