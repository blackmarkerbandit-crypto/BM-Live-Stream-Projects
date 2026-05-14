const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = 3000;

// ─── JSON Database ────────────────────────────────────────────────────────────
const dbDir = path.join(__dirname, 'db');
const dbFile = path.join(dbDir, 'submissions.json');
const backupDir = path.join(dbDir, 'backups');

if (!fs.existsSync(dbDir)) fs.mkdirSync(dbDir, { recursive: true });
if (!fs.existsSync(backupDir)) fs.mkdirSync(backupDir, { recursive: true });
if (!fs.existsSync(dbFile)) fs.writeFileSync(dbFile, '[]', 'utf8');

function readDB() {
  try { return JSON.parse(fs.readFileSync(dbFile, 'utf8')); }
  catch (e) { return []; }
}

function writeDB(data) {
  fs.writeFileSync(dbFile, JSON.stringify(data, null, 2), 'utf8');
}

function nextId(rows) {
  return rows.length === 0 ? 1 : Math.max(...rows.map(r => r.id)) + 1;
}

// ─── Middleware ───────────────────────────────────────────────────────────────
app.use(express.json({ limit: '5mb' }));
app.use(express.urlencoded({ extended: true }));

// Serve website static files
app.use(express.static(path.join(__dirname, 'website')));

// ─── Localhost Guard ──────────────────────────────────────────────────────────
function localhostOnly(req, res, next) {
  const ip = req.ip || req.connection.remoteAddress;
  const isLocal = ip === '127.0.0.1' || ip === '::1' || ip === '::ffff:127.0.0.1';
  if (!isLocal) return res.status(403).json({ error: 'Access restricted to local machine.' });
  next();
}

// ─── API: Save Page (Inline Editor) ──────────────────────────────────────────
app.post('/api/save-page', localhostOnly, (req, res) => {
  const { filename, html } = req.body;

  if (!filename || !html) {
    return res.status(400).json({ error: 'filename and html are required.' });
  }

  const safeName = path.basename(filename);
  if (!safeName.endsWith('.html')) {
    return res.status(400).json({ error: 'Only .html files can be saved.' });
  }

  const filePath = path.join(__dirname, 'website', safeName);

  // Backup before overwrite
  if (fs.existsSync(filePath)) {
    const ts = new Date().toISOString().replace(/[:.]/g, '-');
    fs.copyFileSync(filePath, path.join(backupDir, `${safeName}.${ts}.bak`));
  }

  fs.writeFileSync(filePath, html, 'utf8');
  console.log(`[SAVE] ${safeName} saved at ${new Date().toLocaleTimeString()}`);
  res.json({ success: true, file: safeName });
});

// ─── API: Form Submission ─────────────────────────────────────────────────────
app.post('/api/submit-form', (req, res) => {
  const { form_type, name, email, phone, company, message, ...rest } = req.body;

  if (!form_type || !email) {
    return res.status(400).json({ error: 'form_type and email are required.' });
  }

  const emailRx = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRx.test(email)) {
    return res.status(400).json({ error: 'Invalid email address.' });
  }

  const rows = readDB();
  const record = {
    id: nextId(rows),
    form_type,
    name: name || null,
    email,
    phone: phone || null,
    company: company || null,
    message: message || null,
    data: Object.keys(rest).length ? rest : null,
    ip: req.ip || req.connection.remoteAddress,
    created_at: new Date().toISOString()
  };

  rows.push(record);
  writeDB(rows);

  console.log(`[FORM] New ${form_type} submission from ${email} (id: ${record.id})`);
  res.json({ success: true, id: record.id });
});

// ─── Admin Dashboard ──────────────────────────────────────────────────────────
app.get('/admin', localhostOnly, (req, res) => {
  res.sendFile(path.join(__dirname, 'admin', 'index.html'));
});

// Admin API: get submissions
app.get('/api/admin/submissions', localhostOnly, (req, res) => {
  const { form_type, limit = 100, offset = 0 } = req.query;
  let rows = readDB();

  if (form_type) rows = rows.filter(r => r.form_type === form_type);

  // Newest first
  rows = rows.slice().reverse();
  const total = rows.length;
  const page = rows.slice(Number(offset), Number(offset) + Number(limit));

  res.json({ submissions: page, total });
});

// Admin API: export CSV
app.get('/api/admin/export', localhostOnly, (req, res) => {
  const rows = readDB().slice().reverse();
  const headers = ['id', 'form_type', 'name', 'email', 'phone', 'company', 'message', 'created_at'];

  const csv = [
    headers.join(','),
    ...rows.map(r =>
      headers.map(h => {
        const val = r[h] == null ? '' : String(r[h]);
        return `"${val.replace(/"/g, '""')}"`;
      }).join(',')
    )
  ].join('\r\n');

  res.setHeader('Content-Type', 'text/csv');
  res.setHeader('Content-Disposition', 'attachment; filename="bmb-submissions.csv"');
  res.send(csv);
});

// Admin API: delete a submission
app.delete('/api/admin/submissions/:id', localhostOnly, (req, res) => {
  const id = Number(req.params.id);
  const rows = readDB().filter(r => r.id !== id);
  writeDB(rows);
  res.json({ success: true });
});

// ─── 404 Fallback ─────────────────────────────────────────────────────────────
app.use((req, res) => {
  res.status(404).send('<h2 style="font-family:sans-serif;padding:2rem">404 — Page not found</h2>');
});

// ─── Start ────────────────────────────────────────────────────────────────────
app.listen(PORT, '127.0.0.1', async () => {
  console.log('');
  console.log('  ██████╗ ███╗   ███╗██████╗');
  console.log('  ██╔══██╗████╗ ████║██╔══██╗');
  console.log('  ██████╔╝██╔████╔██║██████╔╝');
  console.log('  ██╔══██╗██║╚██╔╝██║██╔══██╗');
  console.log('  ██████╔╝██║ ╚═╝ ██║██████╔╝');
  console.log('  ╚═════╝ ╚═╝     ╚═╝╚═════╝');
  console.log('');
  console.log(`  BlackMarkerMedia local server running`);
  console.log(`  Site   → http://localhost:${PORT}`);
  console.log(`  Admin  → http://localhost:${PORT}/admin`);
  console.log('');

  try {
    const open = (await import('open')).default;
    await open(`http://localhost:${PORT}`);
  } catch (e) {
    // open is optional
  }
});
