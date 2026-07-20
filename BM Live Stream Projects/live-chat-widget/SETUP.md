# BM Live Chat — Setup Guide

A lightweight chat you own, that replaces cbox and feeds **individual posts into vMix**
the same way your social feeds do. Three pieces:

1. **Google Sheet** — stores every message.
2. **Apps Script** (`apps-script/Code.gs`) — receives messages + serves them as JSON.
3. **Widget** (`chat-widget.html`) — the chat box you embed on the website.

Total cost: **$0**. No server to run.

---

## Part 1 — Create the Sheet + backend (~10 min, one time)

1. Go to **[sheets.new](https://sheets.new)** to create a blank Google Sheet. Name it `BM Live Chat`.
2. In that sheet: **Extensions → Apps Script**. A code editor opens.
3. Delete whatever is in `Code.gs`, then paste the entire contents of
   [`apps-script/Code.gs`](apps-script/Code.gs) from this folder. Click the **save** (💾) icon.
4. In the function dropdown at the top, select **`setupSheet`** and click **Run**.
   - First run asks for permission → **Review permissions → pick your Google account → Advanced →
     Go to (project) → Allow.** (This is normal for your own script.)
   - Switch back to the Sheet; you'll see a `Messages` tab with headers. ✅
5. Now deploy it as a web app: **Deploy → New deployment**.
   - Click the gear ⚙ next to "Select type" → **Web app**.
   - **Description:** BM Live Chat
   - **Execute as:** **Me**
   - **Who has access:** **Anyone**  ← important, this lets the website reach it
   - Click **Deploy** → authorize if asked → **copy the Web app URL**.
     It ends in `/exec` and looks like:
     `https://script.google.com/macros/s/AKfy……/exec`

> Keep that URL. It's used by both the widget and vMix.

---

## Part 2 — Configure + embed the widget

1. Open [`chat-widget.html`](chat-widget.html). Near the top of the `<script>` block, find:
   ```js
   const CHAT_API = 'PASTE_YOUR_WEB_APP_URL_HERE';
   ```
   Replace the placeholder with the `/exec` URL you copied. Save.
2. **Test it locally first:** double-click `chat-widget.html` to open it in a browser,
   type a message, hit Send. Within a few seconds it should appear, and a new row should
   show up in the Google Sheet. 🎉
3. **Put it on the website.** Easiest way = upload `chat-widget.html` to the site and drop
   this iframe where cbox used to be:
   ```html
   <iframe
     src="/chat-widget.html"
     title="Live Chat"
     style="width:100%;max-width:420px;height:600px;border:0;border-radius:14px;"
     loading="lazy"></iframe>
   ```
   Adjust `max-width` / `height` to fit your layout. (Prefer it inline instead of an iframe?
   Copy the `<div class="chat">…</div>` markup, the `<style>`, and the `<script>` straight into
   your page.)
4. Match your branding: in the widget's CSS, change `--accent` (the red) and the background
   variables at the very top of the `<style>` block.

---

## Part 3 — Wire it into vMix

vMix can't talk to cbox, but it reads this chat as a **Data Source**:

1. In vMix: **Settings → Data Sources → Add**.
2. Type: **JSON**.
3. URL: your Web App URL **with `?vmix=1` on the end**, e.g.
   `https://script.google.com/macros/s/AKfy……/exec?vmix=1`
   (The `?vmix=1` returns newest message first, so record #1 is always the latest post.)
4. Set **Refresh** to a few seconds (e.g. 3–5s). Click **OK**.
5. Build/choose a Title (lower-third) with text fields for the name and the message.
   Open the Title's **Data Source** settings and map:
   - a text field → **`name`**
   - a text field → **`message`**
   - (optional) a field → **`time`**
6. On that Title input you now get **record navigation** (next / previous / index) and
   optional auto-cycle — that's your "put one post on screen at a time" control, exactly
   like the social feed workflow.

### Moderation
To hide a junk message from both the website and vMix: open the Google Sheet, find the
row, and type `TRUE` in the **hidden** column. It disappears on the next refresh. To delete
permanently, just delete the row.

---

## Updating later
If you edit `Code.gs`, you must **Deploy → Manage deployments → Edit (✏) → Version: New version → Deploy**
for changes to go live. Editing `chat-widget.html` just needs a re-upload — no redeploy.

## Notes / limits
- Refreshes every ~4s on the site and every few seconds in vMix (polling, not instant — fine for a shoutbox).
- Handles typical live-broadcast chat volume comfortably on Google's free quotas.
- Messages are capped at 300 chars, names at 40, and `< >` are stripped for safety.
