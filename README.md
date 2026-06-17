# Soccer Match Tracker ⚽

A small Streamlit app to track the USC Lion U6 season. All 18 fixtures are
pre-loaded — you just enter the scores. It's styled for kids (pitch banner,
sticker cards) and works well on a phone, with a Quick-entry panel for tapping
in results at the sideline.

---

## What's in the repo
- `streamlit_app.py` — the app
- `requirements.txt` — the Python packages it needs
- `.streamlit/config.toml` — the colour theme (keeps it on the light "pitch"
  look instead of following a phone's dark mode)

## Three places to keep straight
It helps to know these are three separate things:
- **github.com** → your code (`streamlit_app.py`, `config.toml`, `requirements.txt`)
- **share.streamlit.io** → the dashboard where you deploy, reboot, and store
  secret credentials (Settings → Secrets)
- **miniroosgrange.streamlit.app** → the live app you and the parents use

---

## Part 1 — Get it online (≈5 minutes)

1. **Create a GitHub repo.** On github.com click **New**, give it a name, make
   it Public or Private (both work), and create it.
2. **Add the files.** Click **Add file → Upload files**, drag in
   `streamlit_app.py` and `requirements.txt`, then **Commit changes**.
3. **Add the theme file.** Click **Add file → Create new file**. In the filename
   box type exactly `.streamlit/config.toml` — typing the `/` makes the
   `.streamlit` folder — paste in the theme contents, and Commit. Check the repo
   root now shows a `.streamlit` folder *next to* `streamlit_app.py`.
   (Without this file the app follows the phone's dark mode and looks broken.)
4. **Deploy.** Go to **share.streamlit.io**, sign in with GitHub, click
   **Create app**, choose your repo, branch `main`, main file
   `streamlit_app.py`, then **Deploy**.

It builds in a couple of minutes and gives you a link like
`https://your-name.streamlit.app`. It works straight away.

⚠️ **At this stage results save to a temporary file that resets whenever the app
reboots.** To keep results permanently, do Part 2.

---

## Part 2 — Make results stick (Google Sheets)

Streamlit Community Cloud wipes the app's files on every reboot, so we store
results in a Google Sheet instead. This is a one-time setup. A laptop is much
easier than a phone for this part.

### Step 0 — Back up any data you already have
Connecting a fresh sheet starts the app blank, so first open the live app,
scroll to the bottom, and click **Download CSV backup**. Keep that file.

### A. Create the sheet
1. Make a new Google Sheet at **sheets.google.com**.
2. Rename the bottom tab from `Sheet1` to **`matches`**.
3. Copy the sheet's URL — you'll need it later.

### B. Create a Google Cloud project
1. Go to **console.cloud.google.com** and sign in.
2. At the top, next to the **Google Cloud** logo, click the **project dropdown**.
3. Click **New Project** (top-right), name it e.g. `miniroos-soccer`, leave
   organisation as the default ("No organisation" is fine), click **Create**.
4. When it finishes, click the dropdown again and **select your new project** so
   it's the active one. (No billing/credit card is needed.)

### C. Enable the two APIs
1. **☰ menu → APIs & Services → Library**.
2. Search **Google Sheets API**, open it, click **Enable**.
3. Go back to Library, search **Google Drive API**, open it, click **Enable**.
   (Make sure your project name shows at the top before enabling.)

### D. Create the service account + key (the app's "login")
1. **☰ menu → APIs & Services → Credentials**.
2. **+ Create credentials → Service account**. Name it e.g. `miniroos-app`,
   click **Create and continue**, **skip the optional role** (Continue), then
   **Done**.
3. Back on Credentials, click your new `miniroos-app@…` account.
4. Open the **Keys** tab → **Add key → Create new key → JSON → Create**.
   A `.json` file downloads. This is the password file — keep it safe and never
   put it on GitHub.

### E. Share the sheet with the service account
1. Open the JSON file and find the **`client_email`** value (looks like
   `miniroos-app@yourproject.iam.gserviceaccount.com`). Copy it.
2. In your Google Sheet click **Share**, paste that email, set it to **Editor**,
   and share. (A warning about sharing with a non-Google address is expected.)

### F. Make sure the library is installed
Open `requirements.txt` in your repo and confirm it has these three lines:
```
streamlit
pandas
st-gsheets-connection
```
If `st-gsheets-connection` is missing, the app silently falls back to CSV — this
is the most common reason it "won't connect". Add it and commit.

### G. Paste the secret credentials
In **share.streamlit.io** → your app → **⋮ menu → Settings → Secrets**, paste the
block below into the box and click **Save**. The key names match the JSON file,
so it's mostly copy-and-paste:

```toml
[connections.gsheets]
spreadsheet = "PASTE_YOUR_GOOGLE_SHEET_URL"
worksheet = "matches"
type = "service_account"
project_id = "from JSON: project_id"
private_key_id = "from JSON: private_key_id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "from JSON: client_email"
client_id = "from JSON: client_id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "from JSON: client_x509_cert_url"
```

- `spreadsheet` and `worksheet` are NOT in the JSON — use your sheet URL and
  `matches`.
- The last three URL lines are the same for everyone — leave them as written.
- **`private_key`:** copy the whole value from the JSON including every `\n`.
  Leave the `\n`s as the two characters `\` and `n` — do not turn them into real
  line breaks.
- Don't paste the raw JSON in; fill this template instead. Ignore any extra JSON
  keys like `universe_domain`.
- Never commit the JSON or these secrets to GitHub.

### Restore your data
After you Save, use **⋮ → Reboot app**, then refresh. The sidebar should read
**"Saving to Google Sheets ✓"** and the sheet auto-fills with the 18 blank
fixtures. Then either re-enter the handful of scores with Quick entry, or import
your backup CSV into the `matches` tab (**File → Import**). If you import, set
the Date column format to **plain text** so the `YYYY-MM-DD` dates stay intact.

---

## Running it on your own computer (optional)
```
pip install -r requirements.txt
streamlit run streamlit_app.py
```
Locally it saves to `soccer_matches.csv` in the same folder.

---

## Troubleshooting

**Sidebar says "Saving to a local CSV…"** — the app couldn't reach Google, so it
fell back to CSV (and keeps working, which hides the problem). In order:
1. Check `requirements.txt` contains `st-gsheets-connection` (most common cause).
2. Check Settings → Secrets starts with `[connections.gsheets]` and you Saved.
3. Confirm the sheet is shared with the service account's `client_email` as
   Editor, and the tab is named `matches`.
4. **⋮ → Reboot app** — a plain refresh isn't always enough for secrets or
   package changes to take effect.

**The app looks dark / the Save button is red** — the `.streamlit/config.toml`
theme file isn't being read. Confirm it's at the repo root inside a `.streamlit`
folder, then Reboot.

---

## Note on the fixtures
Dates, times, grounds and home/away come straight from the season photo and
should be accurate. A few opponent names — especially the colour suffixes
(Blue/Yellow/Black/etc.) and Round 15 — were hard to read in the rotated image,
so give them a quick check and edit any directly in the app's table.
