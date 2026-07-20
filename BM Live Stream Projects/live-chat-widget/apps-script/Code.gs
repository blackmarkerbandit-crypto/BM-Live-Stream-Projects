/**
 * BM Live Chat — Google Apps Script backend
 * -------------------------------------------------
 * Stores chat messages in a Google Sheet and serves them as JSON.
 *   - Website widget WRITES via POST and READS via JSONP (?callback=).
 *   - vMix READS clean JSON via ?vmix=1  (newest message first).
 *
 * Sheet columns (row 1 = header): id | time | name | message | hidden
 *   hidden = type TRUE in that cell to hide a message from the site + vMix.
 *
 * See SETUP.md for deployment steps.
 */

const SHEET_NAME    = 'Messages';
const MAX_MESSAGES  = 100;   // how many recent messages to return
const MAX_NAME_LEN  = 40;
const MAX_MSG_LEN   = 300;

/** Run this ONCE from the editor to create the sheet + header row. */
function setupSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) sheet = ss.insertSheet(SHEET_NAME);
  sheet.clear();
  sheet.getRange(1, 1, 1, 5).setValues([['id', 'time', 'name', 'message', 'hidden']]);
  sheet.setFrozenRows(1);
}

/** READ: returns recent messages as JSON (or JSONP if ?callback= is present). */
function doGet(e) {
  const p = (e && e.parameter) || {};
  const messages = getMessages();
  // Website widget wants oldest->newest (chat scrolls down).
  // vMix wants newest first so the latest post is record #1.
  const out = p.vmix === '1' ? messages.slice().reverse() : messages;
  const jsonStr = JSON.stringify(out);

  if (p.callback) {
    return ContentService
      .createTextOutput(p.callback + '(' + jsonStr + ')')
      .setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
  return ContentService
    .createTextOutput(jsonStr)
    .setMimeType(ContentService.MimeType.JSON);
}

/** WRITE: appends a message. Called from the widget with mode:'no-cors'. */
function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    let name = clean(String(body.name || 'Guest'), MAX_NAME_LEN) || 'Guest';
    let message = clean(String(body.message || ''), MAX_MSG_LEN);
    if (!message) return json({ ok: false, error: 'empty' });

    const sheet = getSheet();
    const id = Utilities.getUuid().slice(0, 8);
    sheet.appendRow([id, new Date(), name, message, false]);
    return json({ ok: true, id: id });
  } catch (err) {
    return json({ ok: false, error: String(err) });
  }
}

/* ---------- helpers ---------- */

function getSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) { setupSheet(); sheet = ss.getSheetByName(SHEET_NAME); }
  return sheet;
}

function getMessages() {
  const sheet = getSheet();
  const values = sheet.getDataRange().getValues();
  const rows = values.slice(1); // drop header
  const list = [];
  for (let i = 0; i < rows.length; i++) {
    const r = rows[i];
    if (!r[0]) continue;                                   // no id -> skip
    if (String(r[4]).toUpperCase() === 'TRUE') continue;   // hidden
    list.push({
      id: r[0],
      time: (r[1] instanceof Date) ? r[1].toISOString() : String(r[1]),
      name: r[2],
      message: r[3]
    });
  }
  return list.slice(-MAX_MESSAGES);
}

/** Trim, cap length, strip angle brackets so nothing breaks the site or vMix titles. */
function clean(s, max) {
  return s.replace(/[<>]/g, '').replace(/\s+/g, ' ').trim().slice(0, max);
}

function json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
