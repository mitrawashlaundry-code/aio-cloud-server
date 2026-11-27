import os
import json
import subprocess
import shutil
import urllib.request
import uuid
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from http.cookies import SimpleCookie

PORT = 80
OPENBOT_DIR = "/opt/app-data/openbot"
CONFIG_FILE = "/opt/app-data/openbot/config.json"
AUTH_FILE = "/opt/app-data/auth.json"

if not os.path.exists(OPENBOT_DIR):
    os.makedirs(OPENBOT_DIR, exist_ok=True)

if not os.path.exists(AUTH_FILE):
    default_auth = {"username": "admin", "password": "admin123"}
    with open(AUTH_FILE, "w") as f:
        json.dump(default_auth, f, indent=2)

if not os.path.exists(CONFIG_FILE):
    default_config = {
        "gemini_api_key": "",
        "gemini_model": "gemini-flash-lite-latest",
        "system_instruction": "Kamu adalah OpenBot, asisten AI pribadi dan teman ngobrol yang ramah, hangat, santai, cerdas, dan bersahabat. Gunakan bahasa Indonesia sehari-hari yang luwes, alami, dan sopan. Kamu siap diajak ngobrol santai seputar percakapan ringan, cerita keseharian, humor, tips praktis, hingga menjawab pertanyaan dengan ringkas, jelas, dan menyenangkan."
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(default_config, f, indent=2)

SESSIONS = {}

def is_authenticated(headers):
    cookie_header = headers.get("Cookie")
    if not cookie_header:
        return False
    cookie = SimpleCookie()
    try:
        cookie.load(cookie_header)
        if "aio_session" in cookie:
            token = cookie["aio_session"].value
            if token in SESSIONS:
                if time.time() - SESSIONS[token] < 86400 * 7: # 7 hari
                    return True
                else:
                    del SESSIONS[token]
    except:
        pass
    return False

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        return res.stdout.strip()
    except Exception as e:
        return str(e)

def get_containers_status():
    cmd = "docker ps -a --format '{{.Names}}|{{.Status}}|{{.State}}'"
    out = run_cmd(cmd)
    res = {}
    if out:
        for line in out.splitlines():
            parts = line.split("|")
            if len(parts) >= 3:
                res[parts[0]] = {
                    "status": parts[1],
                    "state": parts[2]
                }
    return res

def get_service_status(service_name):
    out = run_cmd(f"systemctl is-active {service_name}")
    return "running" if out == "active" else "stopped"

def get_system_metrics():
    cpu_idle = run_cmd("top -bn1 | grep 'Cpu(s)' | awk '{print $8}'")
    cpu_usage = "N/A"
    try:
        cpu_usage = f"{100.0 - float(cpu_idle):.1f}%"
    except:
        pass
    
    ram_out = run_cmd("free -m | awk 'NR==2{printf \"%s/%sMB (%.1f%%)\", $3,$2,$3*100/$2 }'")
    disk_out = run_cmd("df -h / | awk 'NR==2{printf \"%s/%s (%s)\", $3,$2,$5}'")
    uptime = run_cmd("uptime -p")
    
    return {
        "cpu": cpu_usage,
        "ram": ram_out,
        "disk": disk_out,
        "uptime": uptime
    }

LOGIN_HTML = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Login - AIO Control Center</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: #090d16;
      background-image: radial-gradient(at 50% 50%, rgba(59, 130, 246, 0.15) 0px, transparent 60%);
      color: #f3f4f6;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      padding: 20px;
    }
    .login-card {
      background: rgba(18, 24, 38, 0.85);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 20px;
      padding: 36px 32px;
      width: 100%;
      max-width: 400px;
      backdrop-filter: blur(16px);
      box-shadow: 0 20px 40px rgba(0,0,0,0.6);
      text-align: center;
    }
    .icon {
      width: 54px;
      height: 54px;
      background: linear-gradient(135deg, #3b82f6, #8b5cf6);
      border-radius: 16px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 26px;
      margin-bottom: 16px;
      box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
    }
    h2 { font-size: 20px; font-weight: 800; margin-bottom: 6px; }
    p { font-size: 13px; color: #9ca3af; margin-bottom: 24px; }
    .form-group { text-align: left; margin-bottom: 16px; }
    label { display: block; font-size: 12px; font-weight: 600; color: #cbd5e1; margin-bottom: 6px; }
    input {
      width: 100%;
      background: rgba(15, 23, 42, 0.9);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 10px;
      padding: 12px 14px;
      color: white;
      font-size: 14px;
      outline: none;
      transition: all 0.2s;
    }
    input:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25); }
    .btn {
      width: 100%;
      background: #3b82f6;
      color: white;
      border: none;
      border-radius: 10px;
      padding: 12px;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      margin-top: 8px;
      transition: background 0.2s;
    }
    .btn:hover { background: #2563eb; }
    .err-msg {
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid rgba(239, 68, 68, 0.3);
      color: #f87171;
      padding: 8px 12px;
      border-radius: 8px;
      font-size: 12px;
      margin-bottom: 16px;
      display: none;
    }
  </style>
</head>
<body>
  <div class="login-card">
    <div class="icon">⚡</div>
    <h2>AIO Server Control</h2>
    <p>Silakan masuk untuk mengelola cloud server</p>
    
    <div id="err" class="err-msg">Username atau Password salah!</div>

    <form onsubmit="handleLogin(event)">
      <div class="form-group">
        <label>Username</label>
        <input type="text" id="uname" value="admin" required autofocus>
      </div>
      <div class="form-group">
        <label>Password</label>
        <input type="password" id="pword" value="admin123" required>
      </div>
      <button type="submit" class="btn">Masuk ke Dashboard</button>
    </form>
  </div>

  <script>
    async function handleLogin(e) {
      e.preventDefault();
      const u = document.getElementById('uname').value.trim();
      const p = document.getElementById('pword').value.trim();
      const err = document.getElementById('err');
      err.style.display = 'none';

      try {
        const res = await fetch('/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: u, password: p })
        });
        const d = await res.json();
        if (d.success) {
          window.location.href = '/';
        } else {
          err.innerText = d.message || 'Login gagal';
          err.style.display = 'block';
        }
      } catch (e) {
        err.innerText = 'Gagal menghubungi server';
        err.style.display = 'block';
      }
    }
  </script>
</body>
</html>
"""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AIO Cloud Server Control Center</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #090d16;
      --card-bg: rgba(18, 24, 38, 0.7);
      --card-border: rgba(255, 255, 255, 0.08);
      --accent: #3b82f6;
      --accent-glow: rgba(59, 130, 246, 0.35);
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --text: #f3f4f6;
      --text-muted: #9ca3af;
      --radius: 16px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: var(--bg);
      background-image: 
        radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.12) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(139, 92, 246, 0.12) 0px, transparent 50%);
      color: var(--text);
      min-height: 100vh;
      padding: 24px;
    }
    .container { max-width: 1200px; margin: 0 auto; }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--card-border);
      flex-wrap: wrap;
      gap: 16px;
    }
    .logo-area { display: flex; align-items: center; gap: 14px; }
    .logo-icon {
      width: 48px;
      height: 48px;
      background: linear-gradient(135deg, #3b82f6, #8b5cf6);
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      box-shadow: 0 8px 20px var(--accent-glow);
    }
    h1 { font-size: 24px; font-weight: 800; letter-spacing: -0.5px; }
    .subtitle { font-size: 13px; color: var(--text-muted); }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 600;
    }
    .badge-online { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-offline { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .stat-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--radius);
      padding: 16px 20px;
      backdrop-filter: blur(12px);
    }
    .stat-label { font-size: 12px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
    .stat-val { font-size: 20px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }

    .power-banner {
      background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.9));
      border: 1px solid var(--card-border);
      border-radius: var(--radius);
      padding: 20px 24px;
      margin-bottom: 32px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }
    .power-title { font-size: 16px; font-weight: 700; }
    .power-desc { font-size: 13px; color: var(--text-muted); margin-top: 4px; }
    .btn-group { display: flex; gap: 10px; flex-wrap: wrap; }
    .btn {
      padding: 9px 16px;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 600;
      border: none;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s;
      text-decoration: none;
    }
    .btn-primary { background: var(--accent); color: white; }
    .btn-primary:hover { background: #2563eb; transform: translateY(-1px); }
    .btn-danger { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .btn-danger:hover { background: #ef4444; color: white; }
    .btn-warning { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .btn-warning:hover { background: #f59e0b; color: white; }
    .btn-secondary { background: rgba(255, 255, 255, 0.08); color: var(--text); border: 1px solid var(--card-border); }
    .btn-secondary:hover { background: rgba(255, 255, 255, 0.15); }

    .section-title {
      font-size: 18px;
      font-weight: 700;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .apps-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
      gap: 20px;
      margin-bottom: 36px;
    }
    .app-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--radius);
      padding: 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      overflow: hidden;
    }
    .app-card:hover {
      border-color: rgba(59, 130, 246, 0.4);
      transform: translateY(-3px);
      box-shadow: 0 12px 30px -10px rgba(0, 0, 0, 0.5);
    }
    .app-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
    .app-meta { display: flex; align-items: center; gap: 12px; }
    .app-avatar {
      width: 44px;
      height: 44px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--card-border);
    }
    .app-name { font-size: 16px; font-weight: 700; }
    .app-port { font-size: 12px; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; }
    .app-desc { font-size: 13px; color: #94a3b8; line-height: 1.5; margin-bottom: 18px; }
    .app-actions {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      padding-top: 14px;
    }

    .openbot-box {
      background: var(--card-bg);
      border: 1px solid rgba(139, 92, 246, 0.3);
      border-radius: var(--radius);
      padding: 24px;
      margin-bottom: 36px;
      box-shadow: 0 10px 30px -10px rgba(139, 92, 246, 0.2);
    }
    .form-group { margin-bottom: 16px; }
    .form-label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; color: #cbd5e1; }
    .form-input, .form-textarea, .form-select {
      width: 100%;
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 10px 14px;
      color: white;
      font-family: inherit;
      font-size: 13px;
      outline: none;
      transition: border-color 0.2s;
    }
    .form-input:focus, .form-textarea:focus, .form-select:focus {
      border-color: var(--accent);
    }
    .chat-window {
      background: rgba(10, 15, 28, 0.9);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 16px;
      height: 240px;
      overflow-y: auto;
      margin-bottom: 14px;
      font-size: 13px;
      line-height: 1.6;
    }
    .chat-msg { margin-bottom: 10px; padding: 8px 12px; border-radius: 8px; }
    .chat-user { background: rgba(59, 130, 246, 0.15); border-left: 3px solid var(--accent); }
    .chat-ai { background: rgba(139, 92, 246, 0.15); border-left: 3px solid #8b5cf6; }
    .chat-system { background: rgba(255, 255, 255, 0.05); color: var(--text-muted); font-style: italic; }

    #toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: #1e293b;
      color: white;
      padding: 12px 20px;
      border-radius: 10px;
      border-left: 4px solid var(--accent);
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
      transform: translateY(100px);
      opacity: 0;
      transition: all 0.3s;
      z-index: 999;
      font-size: 13px;
      font-weight: 500;
    }
    #toast.show { transform: translateY(0); opacity: 1; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="logo-area">
        <div class="logo-icon">⚡</div>
        <div>
          <h1>AIO Cloud Server Control</h1>
          <div class="subtitle">Google Cloud Platform &bull; asia-southeast1-b (Singapura) &bull; 34.1.202.11</div>
        </div>
      </div>
      <div style="display: flex; gap: 10px; align-items: center;">
        <span class="badge badge-online"><span class="dot"></span> Server Online</span>
        <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 12px;" onclick="changePasswordPrompt()">🔑 Ganti Password</button>
        <button class="btn btn-danger" style="padding: 6px 12px; font-size: 12px;" onclick="logout()">Keluar</button>
      </div>
    </header>

    <!-- System Metrics -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">CPU Usage</div>
        <div class="stat-val" id="val-cpu">Loading...</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">RAM Memory</div>
        <div class="stat-val" id="val-ram">Loading...</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Storage Disk (/)</div>
        <div class="stat-val" id="val-disk">Loading...</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">System Uptime</div>
        <div class="stat-val" id="val-uptime" style="font-size: 16px;">Loading...</div>
      </div>
    </div>

    <!-- Power Management Banner -->
    <div class="power-banner">
      <div>
        <div class="power-title">Kontrol Daya & Mesin Virtual (GCP VM)</div>
        <div class="power-desc">Nyalakan, reboot, atau matikan instance VM Singapura saat tidak digunakan untuk berhemat biaya.</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-warning" onclick="rebootVM()">🔄 Reboot Server</button>
        <button class="btn btn-danger" onclick="stopVM()">🛑 Matikan VM (Shutdown)</button>
        <button class="btn btn-secondary" onclick="backupData()">📦 Download Backup (.tar.gz)</button>
      </div>
    </div>

    <!-- Apps Grid -->
    <div class="section-title">🚀 Aplikasi & Layanan Terpasang</div>
    <div class="apps-grid" id="apps-container"></div>

    <!-- OpenBot Multi-Agent AI Studio -->
    <div class="section-title">🤖 OpenBot AI Engine (Gemini Integration)</div>
    <div class="openbot-box">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 12px;">
        <div>
          <h3 style="font-size: 16px; font-weight: 700;">Konfigurasi Agen Gemini</h3>
          <p style="font-size: 13px; color: var(--text-muted); margin-top: 2px;">Terintegrasi dengan Gemini AI Engine untuk riset, otomatisasi task, dan eksekusi instruksi.</p>
        </div>
        <div style="display: flex; gap: 8px;">
          <a href="http://" + window.location.hostname + ":7681" id="link-web-console" target="_blank" class="btn btn-primary" style="padding: 6px 12px; font-size: 12px;">💻 Buka Console Terminal (Tablet/Laptop) ↗</a>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; margin-bottom: 16px;">
        <div class="form-group">
          <label class="form-label">Gemini API Key</label>
          <input type="password" id="gemini-key" class="form-input" placeholder="Masukkan Google AI Studio API Key (AIzaSy...)">
        </div>
        <div class="form-group">
          <label class="form-label">Model Gemini</label>
          <select id="gemini-model" class="form-select">
            <option value="gemini-flash-lite-latest" selected>Gemini Flash Lite (Stabil, Cepat & Aktif)</option>
            <option value="gemini-flash-latest">Gemini Flash Latest</option>
            <option value="gemini-3.8-flash">Gemini 3.8 Flash</option>
          </select>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">System Instruction / Persona Agen</label>
        <textarea id="gemini-instruction" class="form-textarea" rows="2" placeholder="Instruksi dasar untuk OpenBot..."></textarea>
      </div>

      <div style="margin-bottom: 20px; display: flex; gap: 10px;">
        <button class="btn btn-primary" onclick="saveOpenBotConfig()">💾 Simpan Konfigurasi</button>
      </div>

      <h4 style="font-size: 14px; font-weight: 600; margin-bottom: 10px;">💬 Chat Langsung dengan OpenBot</h4>
      <div class="chat-window" id="chat-box">
        <div class="chat-msg chat-system">OpenBot Gemini Engine siap menerima instruksi Anda. Ketik pertanyaan atau tugas di bawah:</div>
      </div>
      <div style="display: flex; gap: 10px;">
        <input type="text" id="chat-input" class="form-input" placeholder="Ketik perintah atau tugas untuk OpenBot..." onkeypress="if(event.key === 'Enter') sendChatMessage()">
        <button class="btn btn-primary" onclick="sendChatMessage()">Kirim</button>
      </div>
    </div>
  </div>

  <div id="toast">Notifikasi</div>

  <script>
    const host = window.location.hostname;
    document.getElementById('link-web-console').href = 'http://' + host + ':7681';

    const APPS_DEF = [
      {
        id: 'openbot-console',
        name: 'OpenBot Web Console',
        icon: '💻',
        port: '7681',
        url: 'http://' + host + ':7681',
        desc: 'Web Terminal interaktif untuk mengontrol agen OpenBot langsung dari Browser Laptop & Tablet (Login: admin / admin123).',
        type: 'service'
      },
      {
        id: 'xrdp',
        name: 'Remote Desktop (XFCE GUI)',
        icon: '🖥️',
        port: '3389',
        url: null,
        desc: 'Desktop GUI Linux lengkap via Remote Desktop Connection (RDP). Connect ke 34.1.202.11:3389 dengan user eardisis / admin123.',
        type: 'service'
      },
      {
        id: 'portainer',
        name: 'Portainer CE',
        icon: '🐳',
        port: '9000',
        url: 'http://' + host + ':9000',
        desc: 'Manajemen visual container Docker, inspect log, network, dan statistik pemakaian resource server.',
        type: 'docker'
      },
      {
        id: 'adguardhome',
        name: 'AdGuard Home',
        icon: '🛡️',
        port: '3000',
        url: 'http://' + host + ':3000',
        desc: 'DNS level ad-blocker & tracking blocker terpusat untuk mengamankan jaringan koneksi.',
        type: 'docker'
      },
      {
        id: 'metube',
        name: 'MeTube Downloader',
        icon: '📥',
        port: '8081',
        url: 'http://' + host + ':8081',
        desc: 'Cloud video downloader berbasis yt-dlp dengan kecepatan server Google 1 Gbps (YouTube, TikTok, dll).',
        type: 'docker'
      },
      {
        id: 'filebrowser',
        name: 'FileBrowser',
        icon: '📂',
        port: '8080',
        url: 'http://' + host + ':8080',
        desc: 'Web file manager pribadi (Google Drive mandiri) untuk mengelola & memutar video download.',
        type: 'docker'
      },
      {
        id: 'anythingllm',
        name: 'AnythingLLM',
        icon: '🧠',
        port: '3001',
        url: 'http://' + host + ':3001',
        desc: 'Platform Tanya Jawab AI Dokumen (RAG) untuk SOP, catatan riset laundry, dan file PDF/Docx.',
        type: 'docker'
      },
      {
        id: 'rustdesk-hbbs',
        name: 'RustDesk Relay Server',
        icon: '⚡',
        port: '21115-21119',
        url: null,
        desc: 'Server relay & rendezvous pribadi untuk aplikasi remote desktop RustDesk (G9t+eH0b...).',
        type: 'docker'
      },
      {
        id: 'singbox',
        name: 'sing-box (VLESS Reality)',
        icon: '🚀',
        port: '443',
        url: null,
        desc: 'Proxy VLESS + XTLS Vision + Reality terkamuflase gateway.icloud.com dengan kernel BBR.',
        type: 'service'
      }
    ];

    function showToast(msg) {
      const t = document.getElementById('toast');
      t.innerText = msg;
      t.className = 'show';
      setTimeout(() => { t.className = ''; }, 3500);
    }

    async function loadData() {
      try {
        const res = await fetch('/api/status');
        if (res.status === 401) {
          window.location.reload();
          return;
        }
        const data = await res.json();
        
        document.getElementById('val-cpu').innerText = data.metrics.cpu;
        document.getElementById('val-ram').innerText = data.metrics.ram;
        document.getElementById('val-disk').innerText = data.metrics.disk;
        document.getElementById('val-uptime').innerText = data.metrics.uptime;

        const container = document.getElementById('apps-container');
        container.innerHTML = '';

        APPS_DEF.forEach(app => {
          let isRunning = false;
          let statusText = 'Unknown';

          if (app.type === 'docker') {
            const c = data.containers[app.id];
            if (c) {
              isRunning = c.state === 'running';
              statusText = c.status;
            }
          } else if (app.type === 'service') {
            if (app.id === 'singbox') {
              isRunning = data.singbox === 'running';
            } else if (app.id === 'xrdp') {
              isRunning = data.xrdp === 'running';
            } else if (app.id === 'openbot-console') {
              isRunning = data.openbot_console === 'running';
            }
            statusText = isRunning ? 'active (running)' : 'inactive';
          }

          const badgeClass = isRunning ? 'badge-online' : 'badge-offline';
          const badgeText = isRunning ? 'Running' : 'Stopped';

          const card = document.createElement('div');
          card.className = 'app-card';
          card.innerHTML = `
            <div>
              <div class="app-header">
                <div class="app-meta">
                  <div class="app-avatar">${app.icon}</div>
                  <div>
                    <div class="app-name">${app.name}</div>
                    <div class="app-port">Port: ${app.port}</div>
                  </div>
                </div>
                <span class="badge ${badgeClass}"><span class="dot"></span> ${badgeText}</span>
              </div>
              <p class="app-desc">${app.desc}</p>
            </div>
            <div class="app-actions">
              <div class="btn-group">
                ${isRunning ? 
                  `<button class="btn btn-warning" style="padding: 6px 12px; font-size: 12px;" onclick="toggleApp('${app.id}', '${app.type}', 'restart')">Restart</button>
                   <button class="btn btn-danger" style="padding: 6px 12px; font-size: 12px;" onclick="toggleApp('${app.id}', '${app.type}', 'stop')">Stop</button>` :
                  `<button class="btn btn-primary" style="padding: 6px 12px; font-size: 12px;" onclick="toggleApp('${app.id}', '${app.type}', 'start')">Start</button>`
                }
              </div>
              ${app.url ? `<a href="${app.url}" target="_blank" class="btn btn-secondary" style="padding: 6px 12px; font-size: 12px;">Buka Web ↗</a>` : ''}
            </div>
          `;
          container.appendChild(card);
        });

      } catch (e) {
        console.error(e);
      }
    }

    async function toggleApp(id, type, action) {
      showToast(`Mengirim perintah ${action} ke ${id}...`);
      try {
        const res = await fetch('/api/app/action', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id, type, action })
        });
        const out = await res.json();
        showToast(out.message || 'Selesai');
        setTimeout(loadData, 1200);
      } catch (e) {
        showToast('Gagal mengubah state aplikasi');
      }
    }

    async function rebootVM() {
      if (!confirm('Apakah Anda yakin ingin me-reboot VM server? Server akan offline selama ~30 detik.')) return;
      showToast('Memerintahkan reboot server...');
      await fetch('/api/vm/reboot', { method: 'POST' });
    }

    async function stopVM() {
      if (!confirm('PERINGATAN: Mematikan VM akan menghentikan seluruh layanan. Anda dapat menyalakannya kembali lewat Google Cloud Console atau Antigravity.')) return;
      showToast('Memerintahkan shutdown VM...');
      await fetch('/api/vm/stop', { method: 'POST' });
    }

    function backupData() {
      showToast('Menyiapkan file backup, unduhan akan segera dimulai...');
      window.location.href = '/api/backup';
    }

    async function logout() {
      await fetch('/api/logout', { method: 'POST' });
      window.location.href = '/';
    }

    async function changePasswordPrompt() {
      const newPass = prompt('Masukkan password baru untuk Dashboard AIO:');
      if (!newPass || newPass.trim().length < 4) {
        alert('Password minimal 4 karakter');
        return;
      }
      try {
        const res = await fetch('/api/auth/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ password: newPass.trim() })
        });
        const d = await res.json();
        alert(d.message || 'Password berhasil diperbarui');
      } catch (e) {
        alert('Gagal memperbarui password');
      }
    }

    async function loadOpenBotConfig() {
      try {
        const res = await fetch('/api/openbot/config');
        const cfg = await res.json();
        if (cfg.gemini_api_key) document.getElementById('gemini-key').value = cfg.gemini_api_key;
        if (cfg.gemini_model) document.getElementById('gemini-model').value = cfg.gemini_model;
        if (cfg.system_instruction) document.getElementById('gemini-instruction').value = cfg.system_instruction;
      } catch (e) {}
    }

    async function saveOpenBotConfig() {
      const apiKey = document.getElementById('gemini-key').value.trim();
      const model = document.getElementById('gemini-model').value;
      const instruction = document.getElementById('gemini-instruction').value.trim();

      showToast('Menyimpan konfigurasi OpenBot...');
      try {
        const res = await fetch('/api/openbot/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            gemini_api_key: apiKey,
            gemini_model: model,
            system_instruction: instruction
          })
        });
        const d = await res.json();
        showToast(d.message || 'Konfigurasi tersimpan');
      } catch (e) {
        showToast('Gagal menyimpan konfigurasi');
      }
    }

    async function sendChatMessage() {
      const input = document.getElementById('chat-input');
      const text = input.value.trim();
      if (!text) return;

      const box = document.getElementById('chat-box');
      box.innerHTML += `<div class="chat-msg chat-user"><strong>Anda:</strong> ${text}</div>`;
      input.value = '';
      box.scrollTop = box.scrollHeight;

      const loadingMsg = document.createElement('div');
      loadingMsg.className = 'chat-msg chat-ai';
      loadingMsg.innerHTML = '<em>OpenBot sedang berpikir...</em>';
      box.appendChild(loadingMsg);
      box.scrollTop = box.scrollHeight;

      try {
        const res = await fetch('/api/openbot/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: text })
        });
        const d = await res.json();
        loadingMsg.innerHTML = `<strong>OpenBot (${d.model}):</strong><br>${d.reply.replace(/\\n/g, '<br>')}`;
      } catch (e) {
        loadingMsg.innerHTML = `<span style="color: var(--danger)">Gagal terhubung: ${e.message}</span>`;
      }
      box.scrollTop = box.scrollHeight;
    }

    loadData();
    loadOpenBotConfig();
    setInterval(loadData, 5000);
  </script>
</body>
</html>
"""

class RequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        authed = is_authenticated(self.headers)

        if not authed:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(LOGIN_HTML.encode("utf-8"))
            return

        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode("utf-8"))
        elif self.path == "/api/status":
            containers = get_containers_status()
            singbox = get_service_status("sing-box")
            xrdp = get_service_status("xrdp")
            openbot_console = get_service_status("openbot-console")
            metrics = get_system_metrics()
            self._send_json({
                "containers": containers,
                "singbox": singbox,
                "xrdp": xrdp,
                "openbot_console": openbot_console,
                "metrics": metrics
            })
        elif self.path == "/api/openbot/config":
            try:
                with open(CONFIG_FILE, "r") as f:
                    cfg = json.load(f)
                self._send_json(cfg)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif self.path == "/api/backup":
            tar_file = "/tmp/backup_aio_server.tar.gz"
            run_cmd(f"tar -czf {tar_file} -C /opt app-data")
            if os.path.exists(tar_file):
                self.send_response(200)
                self.send_header("Content-Type", "application/gzip")
                self.send_header("Content-Disposition", 'attachment; filename="backup-app-data.tar.gz"')
                self.end_headers()
                with open(tar_file, "rb") as f:
                    shutil.copyfileobj(f, self.wfile)
            else:
                self._send_json({"error": "Failed to generate backup archive"}, 500)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            req_data = json.loads(body)
        except:
            req_data = {}

        if self.path == "/api/login":
            u = req_data.get("username", "")
            p = req_data.get("password", "")
            try:
                with open(AUTH_FILE, "r") as f:
                    auth_data = json.load(f)
            except:
                auth_data = {"username": "admin", "password": "admin123"}

            if u == auth_data.get("username", "admin") and p == auth_data.get("password", "admin123"):
                session_token = str(uuid.uuid4())
                SESSIONS[session_token] = time.time()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Set-Cookie", f"aio_session={session_token}; Path=/; Max-Age=604800; SameSite=Lax")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
            else:
                self._send_json({"success": False, "message": "Username atau Password salah!"}, 401)
            return

        if self.path == "/api/logout":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Set-Cookie", "aio_session=; Path=/; Max-Age=0")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
            return

        if not is_authenticated(self.headers):
            self._send_json({"error": "Unauthorized"}, 401)
            return

        if self.path == "/api/auth/update":
            new_pass = req_data.get("password")
            if new_pass:
                with open(AUTH_FILE, "w") as f:
                    json.dump({"username": "admin", "password": new_pass}, f, indent=2)
                self._send_json({"success": True, "message": "Password berhasil diperbarui"})
            else:
                self._send_json({"error": "Password tidak valid"}, 400)

        elif self.path == "/api/app/action":
            app_id = req_data.get("id")
            app_type = req_data.get("type")
            action = req_data.get("action")

            if app_type == "docker":
                if action == "restart":
                    run_cmd(f"docker restart {app_id}")
                elif action == "stop":
                    run_cmd(f"docker stop {app_id}")
                elif action == "start":
                    run_cmd(f"docker start {app_id}")
                self._send_json({"success": True, "message": f"{app_id} {action} sukses"})
            elif app_type == "service":
                svc_map = {
                    "singbox": "sing-box",
                    "xrdp": "xrdp",
                    "openbot-console": "openbot-console"
                }
                actual_svc = svc_map.get(app_id, app_id)
                if action in ["start", "stop", "restart"]:
                    run_cmd(f"systemctl {action} {actual_svc}")
                self._send_json({"success": True, "message": f"{actual_svc} {action} sukses"})
            else:
                self._send_json({"error": "Unknown app type"}, 400)

        elif self.path == "/api/vm/reboot":
            self._send_json({"success": True, "message": "Server sedang di-reboot"})
            def delayed_reboot():
                import time
                time.sleep(1)
                run_cmd("shutdown -r now")
            import threading
            threading.Thread(target=delayed_reboot).start()

        elif self.path == "/api/vm/stop":
            self._send_json({"success": True, "message": "Server sedang di-shutdown"})
            def delayed_shutdown():
                import time
                time.sleep(1)
                run_cmd("shutdown -h now")
            import threading
            threading.Thread(target=delayed_shutdown).start()

        elif self.path == "/api/openbot/config":
            try:
                with open(CONFIG_FILE, "w") as f:
                    json.dump(req_data, f, indent=2)
                self._send_json({"success": True, "message": "Konfigurasi OpenBot berhasil disimpan"})
            except Exception as e:
                self._send_json({"error": str(e)}, 500)

        elif self.path == "/api/openbot/chat":
            prompt = req_data.get("prompt", "")
            try:
                with open(CONFIG_FILE, "r") as f:
                    cfg = json.load(f)
            except:
                cfg = {}

            api_key = cfg.get("gemini_api_key", "").strip()
            model = cfg.get("gemini_model", "gemini-flash-lite-latest")
            instruction = cfg.get("system_instruction", "")

            if not api_key:
                self._send_json({
                    "model": model,
                    "reply": "⚠️ Gemini API Key belum dikonfigurasi. Silakan masukkan API Key Anda di form konfigurasi di atas dan klik 'Simpan Konfigurasi'."
                })
                return

            active_model = model
            if "gemini-2." in model or not active_model:
                active_model = "gemini-flash-lite-latest"

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{active_model}:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {
                        "parts": [{"text": prompt}]
                    }
                ]
            }
            if instruction:
                payload["systemInstruction"] = {
                    "parts": [{"text": instruction}]
                }

            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    text_parts = []
                    candidates = resp_data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        for p in parts:
                            if "text" in p:
                                text_parts.append(p["text"])
                    reply = "".join(text_parts) if text_parts else "Tidak ada respons dari model."
                    self._send_json({"model": active_model, "reply": reply})
            except Exception as e:
                self._send_json({"model": active_model, "reply": f"Error API Gemini: {str(e)}"}, 500)
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), RequestHandler)
    print(f"AIO Server Control running with Web Form Login on port {PORT}...")
    server.serve_forever()
