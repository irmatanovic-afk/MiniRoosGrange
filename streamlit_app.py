"""
Soccer Match Tracker — USC Lion U6 (2026 season)
Ready to deploy on Streamlit Community Cloud.

Persistence
-----------
Community Cloud wipes the local filesystem on every reboot, so results are
stored in a Google Sheet (via st-gsheets-connection) when one is configured.
If no Google Sheet is set up, the app falls back to a local CSV so it still
runs on your own machine. See README.md for the one-time Google setup.
"""

import os
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Soccer Match Tracker", page_icon="⚽", layout="wide")

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Nunito:wght@400;600;700;800&display=swap');

:root {
  --pitch: #2faa5a;
  --pitch-dark: #1e7a40;
  --sun: #ffd23f;
  --sky: #5cc6ff;
  --coral: #ff6b4a;
  --ink: #143a26;
}

.stApp, [data-testid="stAppViewContainer"], html, body { font-family: 'Nunito', sans-serif; }

.stApp {
  background:
    radial-gradient(circle at 12% 16%, rgba(92,198,255,.12), transparent 40%),
    radial-gradient(circle at 88% 8%, rgba(255,210,63,.16), transparent 38%),
    #f3faf4;
}
[data-testid="stHeader"] { background: transparent; }

h1, h2, h3 { font-family: 'Fredoka', sans-serif; color: var(--ink); letter-spacing: .2px; }

/* ---------- Scoreboard banner (signature element) ---------- */
.scoreboard {
  position: relative;
  border-radius: 26px;
  padding: 28px 26px;
  margin: 2px 0 16px;
  background: repeating-linear-gradient(90deg, #2faa5a 0 64px, #2ea455 64px 128px);
  box-shadow: 0 10px 26px rgba(30,122,64,.28);
  border: 4px solid #ffffff;
  overflow: hidden;
}
.scoreboard::before {
  content: ""; position: absolute; top: 0; bottom: 0; left: 50%;
  width: 3px; background: rgba(255,255,255,.55); transform: translateX(-50%);
}
.scoreboard::after {
  content: ""; position: absolute; top: 50%; left: 50%;
  width: 120px; height: 120px; border: 3px solid rgba(255,255,255,.5);
  border-radius: 50%; transform: translate(-50%, -50%);
}
.scoreboard .title {
  position: relative; z-index: 1; font-family: 'Fredoka', sans-serif; font-weight: 700;
  font-size: clamp(26px, 4.5vw, 40px); color: #fff; margin: 0; line-height: 1.1;
  text-shadow: 0 2px 0 rgba(0,0,0,.18);
}
.scoreboard .sub {
  position: relative; z-index: 1; color: #eafff0; font-weight: 700;
  margin-top: 6px; font-size: 15px;
}
.scoreboard .ball { display: inline-block; animation: bob 1.6s ease-in-out infinite; }
@keyframes bob { 0%,100% { transform: translateY(0) rotate(-8deg); } 50% { transform: translateY(-7px) rotate(8deg); } }

/* ---------- Metric cards ---------- */
[data-testid="stMetric"] {
  background: #fff; border-radius: 18px; padding: 14px 16px;
  box-shadow: 0 6px 16px rgba(20,58,38,.08); border-top: 5px solid var(--pitch);
}
[data-testid="stMetricValue"] { font-family: 'Fredoka', sans-serif; color: var(--pitch-dark); }
[data-testid="stMetricLabel"] p { font-weight: 800; color: var(--ink); }

/* ---------- Buttons ---------- */
.stButton > button, .stDownloadButton > button {
  font-family: 'Fredoka', sans-serif; font-weight: 600;
  background: var(--pitch); color: #fff; border: none; border-radius: 999px;
  padding: .5rem 1.3rem; box-shadow: 0 5px 0 var(--pitch-dark);
  transition: transform .08s ease, box-shadow .08s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  background: var(--pitch-dark); color: #fff; transform: translateY(1px); box-shadow: 0 4px 0 #155c30;
}
.stButton > button:active, .stDownloadButton > button:active { transform: translateY(4px); box-shadow: 0 1px 0 #155c30; }
.stButton > button[kind="primary"] { background: var(--sun); color: #5a3d00; box-shadow: 0 5px 0 #d9a400; }
.stButton > button[kind="primary"]:hover { background: #ffce26; color: #5a3d00; box-shadow: 0 4px 0 #d9a400; }

/* ---------- Next-match card ---------- */
.nextcard {
  display: flex; flex-wrap: wrap; align-items: center; gap: 12px;
  background: #fff; border: 3px dashed var(--sky); border-radius: 20px;
  padding: 14px 18px; margin: 4px 0 8px; box-shadow: 0 6px 16px rgba(20,58,38,.07);
}
.nextcard .pill {
  background: var(--sky); color: #063b56; font-family: 'Fredoka', sans-serif; font-weight: 700;
  padding: 6px 12px; border-radius: 999px; white-space: nowrap;
}
.nextcard .vs { font-family: 'Fredoka', sans-serif; font-size: 19px; color: var(--ink); }
.nextcard .meta { color: #4d6a59; font-weight: 700; font-size: 14px; }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] { background: #ffffff; border-right: 3px solid #e4f3e8; }
[data-testid="stSidebar"] h2 { color: var(--pitch-dark); }

@media (prefers-reduced-motion: reduce) { .scoreboard .ball { animation: none; } }
"""
st.markdown(f"<style>{CUSTOM_CSS}</style>", unsafe_allow_html=True)

DATA_FILE = "soccer_matches.csv"
WORKSHEET = "matches"  # the tab name inside your Google Sheet

COLUMNS = [
    "Round", "Date", "Time", "Ground", "Home/Away", "Opponent",
    "Goals For", "Goals Against", "Snacks",
]

# Fixtures read from the Football SA schedule photo.
# [Round, Date, Time, Ground, Home/Away, Opponent]
# NOTE: dates/times/grounds are high-confidence; please double-check opponent
# names and colours against the original sheet — they're editable in the app.
FIXTURES = [
    [1,  "2026-04-19", "9:30",  "Grange Recreation Reserve", "Home", "Adelaide Titans"],
    [2,  "2026-04-26", "8:30",  "Jack Smith Park", "Away", "WT Birkalla (Black)"],
    [3,  "2026-05-03", "9:30",  "Grange Recreation Reserve", "Home", "Mount Barker United"],
    [4,  "2026-05-10", "9:30",  "Grange Recreation Reserve", "Home", "WT Birkalla (Yellow)"],
    [5,  "2026-05-17", "9:00",  "Plympton Oval", "Away", "Plympton FC"],
    [6,  "2026-05-24", "10:30", "O'Sullivan Beach Sports & Community Club", "Away", "South Adelaide"],
    [7,  "2026-05-31", "9:30",  "Grange Recreation Reserve", "Home", "Sturt Lions (Blue)"],
    [8,  "2026-06-14", "8:30",  "SAWSA Park", "Away", "Adelaide Thunder"],
    [9,  "2026-06-21", "9:30",  "Grange Recreation Reserve", "Home", "Fulham United (White)"],
    [10, "2026-06-28", "8:35",  "Pro Paint & Panel - Weigall Oval", "Away", "Adelaide Cobras (Green)"],
    [11, "2026-07-12", "9:30",  "Grange Recreation Reserve", "Home", "Sturt Lions (Orange)"],
    [12, "2026-07-19", "10:00", "Matheson Reserve", "Away", "Adelaide Titans"],
    [13, "2026-07-26", "9:30",  "Grange Recreation Reserve", "Home", "WT Birkalla (Black)"],
    [14, "2026-08-02", "9:15",  "Summit Sport & Recreation Park", "Away", "Mount Barker United"],
    [15, "2026-08-09", "9:30",  "Grange Recreation Reserve", "Home", "Plympton FC"],
    [16, "2026-08-16", "8:30",  "Jack Smith Park", "Away", "WT Birkalla (Yellow)"],
    [17, "2026-08-23", "9:30",  "Grange Recreation Reserve", "Home", "South Adelaide"],
    [18, "2026-08-30", "9:00",  "Hewett Sports Ground", "Away", "Sturt Lions (Blue)"],
]


def seed_frame():
    rows = []
    for r in FIXTURES:
        rows.append({
            "Round": r[0], "Date": r[1], "Time": r[2], "Ground": r[3],
            "Home/Away": r[4], "Opponent": r[5],
            "Goals For": None, "Goals Against": None, "Snacks": "",
        })
    return pd.DataFrame(rows, columns=COLUMNS)


# ---------------------------------------------------------------------------
# Storage backend: Google Sheets if configured, else local CSV
# ---------------------------------------------------------------------------
USE_GSHEETS = False
conn = None
try:
    from streamlit_gsheets import GSheetsConnection
    try:
        configured = "gsheets" in st.secrets.get("connections", {})
    except Exception:
        configured = False
    if configured:
        conn = st.connection("gsheets", type=GSheetsConnection)
        USE_GSHEETS = True
except Exception:
    USE_GSHEETS = False


def normalize(df):
    if df is None:
        return seed_frame()
    df = df.copy().dropna(how="all")
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[COLUMNS]
    if df.empty:
        return seed_frame()
    df["Round"] = pd.to_numeric(df["Round"], errors="coerce")
    for col in ["Goals For", "Goals Against"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Snacks"] = df["Snacks"].fillna("")
    return df


def load_data():
    if USE_GSHEETS:
        try:
            raw = conn.read(worksheet=WORKSHEET, ttl=0)
        except Exception:
            raw = None
        empty = raw is None or (hasattr(raw, "dropna") and raw.dropna(how="all").empty)
        if empty:
            df = seed_frame()
            try:
                conn.update(worksheet=WORKSHEET, data=df)
            except Exception as e:
                st.warning(f"Couldn't initialise the Google Sheet tab '{WORKSHEET}': {e}")
            return df
        return normalize(raw)

    # Local CSV fallback
    if os.path.exists(DATA_FILE):
        try:
            raw = pd.read_csv(DATA_FILE)
        except pd.errors.EmptyDataError:
            raw = None
    else:
        raw = None
    if raw is None or raw.dropna(how="all").empty:
        df = seed_frame()
        df.to_csv(DATA_FILE, index=False)
        return df
    return normalize(raw)


def save_data(df):
    out = df.copy()
    for col in COLUMNS:
        if col not in out.columns:
            out[col] = None
    out = out[COLUMNS].copy()
    out["Date"] = pd.to_datetime(out["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    out["Date"] = out["Date"].where(out["Date"].notna(), "")
    if USE_GSHEETS:
        conn.update(worksheet=WORKSHEET, data=out)
    else:
        out.to_csv(DATA_FILE, index=False)


def has_result(row):
    return pd.notna(row["Goals For"]) and pd.notna(row["Goals Against"])


def result_label(row):
    if not has_result(row):
        return ""
    gf, ga = row["Goals For"], row["Goals Against"]
    if gf > ga:
        return "Win"
    if gf < ga:
        return "Loss"
    return "Draw"


def fmt_date(s):
    try:
        return datetime.strptime(str(s), "%Y-%m-%d").strftime("%a %d %b")
    except Exception:
        return str(s)


def current_streak(seq):
    if not seq:
        return "—"
    last = seq[-1]
    n = 0
    for x in reversed(seq):
        if x == last:
            n += 1
        else:
            break
    word = {"Win": "win", "Draw": "draw", "Loss": "loss"}[last]
    return f"{n} {word}{'s' if n > 1 else ''}"


def longest_run(seq, kinds):
    best = cur = 0
    for x in seq:
        if x in kinds:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚽ Team setup")
    team_name = st.text_input("Team name", value="USC Lion U6 Joeys (Blue)")
    st.divider()
    if USE_GSHEETS:
        st.success("Saving to Google Sheets ✓")
    else:
        st.info(
            "Saving to a local CSV. On Streamlit Cloud, connect a Google Sheet "
            "(see README) so results aren't lost when the app reboots."
        )

st.markdown(
    f"""
    <div class="scoreboard">
      <div class="title"><span class="ball">⚽</span> {team_name}</div>
      <div class="sub">2026 season scoreboard — pop in your scores and watch the season grow! 🌱</div>
    </div>
    """,
    unsafe_allow_html=True,
)

df = load_data()

if st.session_state.pop("just_saved", False):
    st.success("Saved! 🎉")
    st.balloons()

results = df.apply(result_label, axis=1)
played_mask = df.apply(has_result, axis=1)

# Summary
played = int(played_mask.sum())
wins = int((results == "Win").sum())
draws = int((results == "Draw").sum())
losses = int((results == "Loss").sum())
gf_total = int(df.loc[played_mask, "Goals For"].sum()) if played else 0
ga_total = int(df.loc[played_mask, "Goals Against"].sum()) if played else 0

cols = st.columns(6)
cols[0].metric("Played", f"{played}/{len(df)}")
cols[1].metric("Wins 🏆", wins)
cols[2].metric("Draws 🤝", draws)
cols[3].metric("Losses", losses)
cols[4].metric("Our goals ⚽", gf_total)
cols[5].metric("Their goals 🥅", ga_total)

# Next match
upcoming = df[~played_mask].sort_values(["Date", "Time"])
if not upcoming.empty:
    nx = upcoming.iloc[0]
    snack = str(nx.get("Snacks", "") or "").strip()
    snack_html = f'<div class="meta">🍊 Snacks: <b>{snack}</b></div>' if snack else ""
    st.markdown(
        f"""
        <div class="nextcard">
          <div class="pill">Next up · Round {int(nx['Round'])}</div>
          <div class="vs">{nx['Home/Away']} vs <b>{nx['Opponent']}</b></div>
          <div class="meta">📅 {fmt_date(nx['Date'])} &nbsp;·&nbsp; ⏰ {nx['Time']} &nbsp;·&nbsp; 📍 {nx['Ground']}</div>
          {snack_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

# Editable fixtures + results
st.subheader("📋 Fixtures & results")
st.caption("For each match, type how many goals each team scored, then press Save. "
           "You can also fix an opponent's name right here.")

edit_view = df.sort_values("Round").reset_index(drop=True).copy()
edit_view["Date"] = pd.to_datetime(edit_view["Date"], errors="coerce")

edited = st.data_editor(
    edit_view,
    use_container_width=True,
    hide_index=True,
    num_rows="dynamic",
    key="editor",
    column_config={
        "Round": st.column_config.NumberColumn("Round", width="small", disabled=True),
        "Date": st.column_config.DateColumn("Date", format="DD MMM YYYY", width="medium"),
        "Time": st.column_config.TextColumn("Time", width="small"),
        "Ground": st.column_config.TextColumn("Ground", width="medium"),
        "Home/Away": st.column_config.SelectboxColumn(
            "Home / Away", options=["Home", "Away", "Neutral"], width="small"
        ),
        "Opponent": st.column_config.TextColumn("Opponent", width="medium"),
        "Goals For": st.column_config.NumberColumn(
            "Our goals ⚽", min_value=0, step=1,
            help="Goals scored by your team in this match",
        ),
        "Goals Against": st.column_config.NumberColumn(
            "Their goals 🥅", min_value=0, step=1,
            help="Goals scored by the other team in this match",
        ),
        "Snacks": st.column_config.TextColumn(
            "🍊 Snacks", width="medium",
            help="Who's bringing the oranges/snacks this week",
        ),
    },
)

if st.button("💾 Save results", type="primary"):
    save_data(edited)
    st.session_state["just_saved"] = True
    st.rerun()

# Results so far + chart
done = df[played_mask].copy()
if not done.empty:
    done["Score"] = done.apply(
        lambda r: f'{int(r["Goals For"])}\u2013{int(r["Goals Against"])}', axis=1
    )
    res_emoji = {"Win": "✅ Win", "Draw": "🤝 Draw", "Loss": "❌ Loss"}
    done["Result"] = [res_emoji.get(x, x) for x in results[played_mask].values]
    done["When"] = done["Date"].map(fmt_date)

    st.subheader("📊 Results so far")
    st.dataframe(
        done[["Round", "When", "Home/Away", "Opponent", "Score", "Result"]],
        hide_index=True,
        use_container_width=True,
        column_config={
            "Round": st.column_config.NumberColumn("Round", width="small"),
            "When": st.column_config.TextColumn("Date", width="medium"),
            "Home/Away": st.column_config.TextColumn("Home / Away", width="small"),
            "Opponent": st.column_config.TextColumn("Opponent", width="medium"),
            "Score": st.column_config.TextColumn("Score (us–them)", width="small"),
            "Result": st.column_config.TextColumn("Result", width="small"),
        },
    )

    st.subheader("🥅 Goals by round")
    st.bar_chart(done.sort_values("Round").set_index("Round")[["Goals For", "Goals Against"]])

# Form, streaks and record by opponent
played_df = df[played_mask].sort_values("Round")
if not played_df.empty:
    seq = [result_label(r) for _, r in played_df.iterrows()]
    square = {"Win": "🟩", "Draw": "🟨", "Loss": "🟥"}

    st.subheader("🔥 Form")
    st.markdown("**Last 5:**  " + "  ".join(square[x] for x in seq[-5:]))
    st.caption("🟩 win · 🟨 draw · 🟥 loss")
    fc = st.columns(4)
    fc[0].metric("Current run", current_streak(seq))
    fc[1].metric("Longest win streak", longest_run(seq, {"Win"}))
    fc[2].metric("Unbeaten streak", longest_run(seq, {"Win", "Draw"}))
    fc[3].metric("Points (3/1/0)", wins * 3 + draws)

    st.subheader("🏆 Record by opponent")
    rows = []
    for opp, g in played_df.groupby("Opponent"):
        res = [result_label(r) for _, r in g.iterrows()]
        rows.append({
            "Opponent": opp,
            "Played": len(g),
            "Won": res.count("Win"),
            "Drawn": res.count("Draw"),
            "Lost": res.count("Loss"),
            "Our goals": int(g["Goals For"].sum()),
            "Their goals": int(g["Goals Against"].sum()),
        })
    h2h = pd.DataFrame(rows).sort_values(["Won", "Our goals"], ascending=False)
    st.dataframe(h2h, hide_index=True, use_container_width=True)

st.download_button(
    "Download CSV backup",
    df[COLUMNS].to_csv(index=False),
    file_name="soccer_matches.csv",
    mime="text/csv",
)
