<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VALIANT ZIPPU</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      background: #0a0a0a;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      font-family: 'Courier New', monospace;
      padding: 40px 20px;
    }

    .terminal {
      max-width: 1000px;
      width: 100%;
      background: #0d0d0d;
      border: 1px solid #1a1a1a;
      border-radius: 12px;
      padding: 40px;
      box-shadow: 0 0 60px rgba(255,255,255,0.02), inset 0 0 60px rgba(255,255,255,0.01);
      position: relative;
    }

    /* Glow line */
    .terminal::before {
      content: '';
      position: absolute;
      top: -1px;
      left: 20%;
      right: 20%;
      height: 1px;
      background: linear-gradient(90deg, transparent, #333, transparent);
    }

    /* ASCII LOGO */
    .logo {
      color: #ffffff;
      font-size: 12px;
      line-height: 1.3;
      letter-spacing: 1px;
      text-align: center;
      white-space: pre;
      font-family: 'Courier New', monospace;
      margin-bottom: 10px;
      opacity: 0.9;
    }

    .subtitle {
      text-align: center;
      color: #666;
      font-size: 14px;
      letter-spacing: 6px;
      text-transform: uppercase;
      padding-bottom: 30px;
      border-bottom: 1px solid #141414;
      margin-bottom: 30px;
    }

    .subtitle span {
      color: #888;
    }

    /* GRID CARDS */
    .grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      margin-bottom: 30px;
    }

    .card {
      background: #0f0f0f;
      border: 1px solid #181818;
      border-radius: 8px;
      padding: 24px 20px;
      position: relative;
      transition: all 0.3s ease;
    }

    .card:hover {
      border-color: #2a2a2a;
      background: #111;
    }

    .card::after {
      content: '';
      position: absolute;
      bottom: -1px;
      left: 20%;
      right: 20%;
      height: 1px;
      background: linear-gradient(90deg, transparent, #222, transparent);
    }

    .card-label {
      color: #444;
      font-size: 10px;
      letter-spacing: 4px;
      text-transform: uppercase;
      margin-bottom: 14px;
      font-weight: 400;
    }

    .card-label .bullet {
      color: #666;
      margin-right: 6px;
    }

    .card-content {
      color: #ccc;
      font-size: 13px;
      line-height: 1.9;
      letter-spacing: 2px;
    }

    .card-content .highlight {
      color: #fff;
      font-weight: 400;
    }

    .card-content .dim {
      color: #555;
    }

    /* TOOLKIT */
    .toolkit-wrap {
      margin-bottom: 30px;
    }

    .toolkit-box {
      background: #0f0f0f;
      border: 1px solid #181818;
      border-radius: 8px;
      padding: 20px 24px;
      text-align: center;
    }

    .toolkit-label {
      color: #444;
      font-size: 10px;
      letter-spacing: 4px;
      text-transform: uppercase;
      margin-bottom: 12px;
    }

    .toolkit-items {
      color: #aaa;
      font-size: 13px;
      letter-spacing: 3px;
      word-spacing: 8px;
    }

    .toolkit-items .sep {
      color: #2a2a2a;
    }

    /* STATS */
    .stats-wrap {
      margin-bottom: 30px;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }

    .stats-box {
      background: #0f0f0f;
      border: 1px solid #181818;
      border-radius: 8px;
      padding: 20px;
      text-align: center;
    }

    .stats-box img {
      max-width: 100%;
      height: auto;
      border-radius: 4px;
    }

    .stats-box.full {
      grid-column: 1 / -1;
    }

    .stats-label {
      color: #444;
      font-size: 10px;
      letter-spacing: 4px;
      text-transform: uppercase;
      margin-bottom: 12px;
    }

    /* CONNECT */
    .connect-wrap {
      margin-bottom: 30px;
    }

    .connect-box {
      background: #0f0f0f;
      border: 1px solid #181818;
      border-radius: 8px;
      padding: 20px 24px;
      text-align: center;
    }

    .connect-label {
      color: #444;
      font-size: 10px;
      letter-spacing: 4px;
      text-transform: uppercase;
      margin-bottom: 14px;
    }

    .connect-links {
      display: flex;
      justify-content: center;
      gap: 20px;
      flex-wrap: wrap;
    }

    .connect-links a {
      color: #888;
      text-decoration: none;
      font-size: 12px;
      letter-spacing: 3px;
      text-transform: uppercase;
      padding: 8px 20px;
      border: 1px solid #1a1a1a;
      border-radius: 4px;
      transition: all 0.3s ease;
    }

    .connect-links a:hover {
      color: #fff;
      border-color: #333;
      background: #141414;
    }

    /* FOOTER ASCII */
    .footer-ascii {
      text-align: center;
      color: #1a1a1a;
      font-size: 8px;
      line-height: 1.4;
      letter-spacing: 0.5px;
      white-space: pre;
      font-family: 'Courier New', monospace;
      padding: 20px 0 10px 0;
      border-top: 1px solid #111;
      margin-top: 10px;
    }

    .footer-ascii .highlight {
      color: #222;
    }

    .footer-text {
      text-align: center;
      color: #222;
      font-size: 10px;
      letter-spacing: 4px;
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px solid #0f0f0f;
    }

    /* RESPONSIVE */
    @media (max-width: 768px) {
      .terminal { padding: 20px; }
      .grid { grid-template-columns: 1fr; }
      .stats-grid { grid-template-columns: 1fr; }
      .stats-box.full { grid-column: 1; }
      .logo { font-size: 8px; }
      .connect-links { gap: 10px; }
      .connect-links a { font-size: 10px; padding: 6px 14px; }
    }

    /* SCROLL BAR */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: #0a0a0a; }
    ::-webkit-scrollbar-thumb { background: #1a1a1a; border-radius: 2px; }

    /* SELECTION */
    ::selection { background: #1a1a1a; color: #fff; }

    /* CURSOR BLINK */
    .cursor {
      display: inline-block;
      width: 2px;
      height: 14px;
      background: #333;
      margin-left: 4px;
      animation: blink 1.2s step-end infinite;
      vertical-align: text-bottom;
    }

    @keyframes blink {
      0%, 100% { opacity: 1; }
      50% { opacity: 0; }
    }

    /* BADGE PULSE */
    .pulse-dot {
      display: inline-block;
      width: 6px;
      height: 6px;
      background: #2a2a2a;
      border-radius: 50%;
      margin-right: 8px;
      animation: pulse 2s ease-in-out infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 0.3; }
      50% { opacity: 1; }
    }

    /* GLITCH LINE */
    .glitch-line {
      height: 1px;
      background: linear-gradient(90deg, transparent, #1a1a1a 20%, #1a1a1a 80%, transparent);
      margin: 20px 0;
      width: 100%;
    }

    /* METRIC RINGS */
    .metric-ring {
      display: flex;
      justify-content: center;
      gap: 40px;
      padding: 10px 0;
    }

    .metric-item {
      text-align: center;
    }

    .metric-number {
      color: #fff;
      font-size: 22px;
      font-weight: 300;
      letter-spacing: 2px;
    }

    .metric-label {
      color: #444;
      font-size: 9px;
      letter-spacing: 2px;
      text-transform: uppercase;
      margin-top: 4px;
    }

    .metric-divider {
      color: #1a1a1a;
      font-size: 20px;
      font-weight: 100;
    }
  </style>
</head>
<body>
<div class="terminal">

  <!-- LOGO -->
  <div class="logo">
██╗  ██╗ █████╗ ██╗     ██╗ █████╗ ███╗   ██╗████████╗
██║  ██║██╔══██╗██║     ██║██╔══██╗████╗  ██║╚══██╔══╝
███████║███████║██║     ██║███████║██╔██╗ ██║   ██║
██╔══██║██╔══██║██║     ██║██╔══██║██║╚██╗██║   ██║
██║  ██║██║  ██║███████╗██║██║  ██║██║ ╚████║   ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝
  </div>

  <!-- SUBTITLE -->
  <div class="subtitle">
    <span>⬩</span> WONT LET YOU CROSS ME <span>⬩</span>
  </div>

  <!-- METRIC RINGS -->
  <div class="metric-ring">
    <div class="metric-item">
      <div class="metric-number">15,622</div>
      <div class="metric-label">Contributions</div>
    </div>
    <div class="metric-divider">◆</div>
    <div class="metric-item">
      <div class="metric-number">4</div>
      <div class="metric-label">Current Stream</div>
    </div>
    <div class="metric-divider">◆</div>
    <div class="metric-item">
      <div class="metric-number">26</div>
      <div class="metric-label">Loyalty Status</div>
    </div>
  </div>

  <div class="glitch-line"></div>

  <!-- GRID: WORK / LEARN / SEEK -->
  <div class="grid">
    <div class="card">
      <div class="card-label"><span class="bullet">◆</span> WORKING</div>
      <div class="card-content">
        <span class="highlight">K A I T E Y O</span><br>
        <span class="highlight">I S E K A I Y O</span>
      </div>
    </div>
    <div class="card">
      <div class="card-label"><span class="bullet">◆</span> LEARNING</div>
      <div class="card-content">
        <span class="highlight">J A V A</span><br>
        <span class="highlight">R U S T</span><br>
        <span class="highlight">T Y P E S C R I P T</span><br>
        <span class="dim">H T M L</span>
      </div>
    </div>
    <div class="card">
      <div class="card-label"><span class="bullet">◆</span> SEEKING</div>
      <div class="card-content">
        <span class="highlight">SYSTEM DESIGN</span><br>
        <span class="highlight">U X</span><br>
        <span class="dim">DESIGN LANGUAGE</span>
      </div>
    </div>
  </div>

  <!-- TOOLKIT -->
  <div class="toolkit-wrap">
    <div class="toolkit-box">
      <div class="toolkit-label">◆ TOOLKIT</div>
      <div class="toolkit-items">
        FIGMA <span class="sep">◆</span>
        KOTLIN <span class="sep">◆</span>
        PHOTOSHOP <span class="sep">◆</span>
        PYTHON <span class="sep">◆</span>
        RUST <span class="sep">◆</span>
        TYPESCRIPT
      </div>
    </div>
  </div>

  <!-- STATS -->
  <div class="stats-wrap">
    <div class="stats-grid">
      <div class="stats-box">
        <div class="stats-label">◆ OVERALL</div>
        <img src="https://github-readme-stats.vercel.app/api?username=ValiantZippu&show_icons=true&theme=dark&hide_border=true&bg_color=0d0d0d&title_color=ffffff&icon_color=444&text_color=666&count_private=true" alt="stats">
      </div>
      <div class="stats-box">
        <div class="stats-label">◆ STREAK</div>
        <img src="https://github-readme-streak-stats.herokuapp.com/?user=ValiantZippu&theme=dark&hide_border=true&background=0d0d0d&stroke=222&ring=444&fire=666&currStreakLabel=888" alt="streak">
      </div>
      <div class="stats-box full">
        <div class="stats-label">◆ LANGUAGES</div>
        <img src="https://github-readme-stats.vercel.app/api/top-langs?username=ValiantZippu&layout=compact&theme=dark&hide_border=true&bg_color=0d0d0d&title_color=ffffff&text_color=666" alt="languages">
      </div>
    </div>
  </div>

  <!-- TROPHIES -->
  <div style="margin-bottom: 30px;">
    <div style="background:#0f0f0f;border:1px solid #181818;border-radius:8px;padding:20px;text-align:center;">
      <div style="color:#444;font-size:10px;letter-spacing:4px;text-transform:uppercase;margin-bottom:12px;">◆ ACHIEVEMENTS</div>
      <img src="https://github-profile-trophy.vercel.app/?username=ValiantZippu&theme=darkhub&no-frame=true&row=2&column=4&margin-w=12&margin-h=12" alt="trophies" style="max-width:100%;">
    </div>
  </div>

  <!-- CONNECT -->
  <div class="connect-wrap">
    <div class="connect-box">
      <div class="connect-label">◆ CONNECT</div>
      <div class="connect-links">
        <a href="https://github.com/ValiantZippu">GITHUB</a>
        <a href="mailto:emailzippu@gmail.com">EMAIL</a>
        <a href="https://idontworkforothers.com">WEBSITE</a>
      </div>
    </div>
  </div>

  <!-- FOOTER ASCII -->
  <div class="footer-ascii">
<span class="highlight">████████████████████████████████████████████████████████████</span>
<span class="highlight">█                                                          █</span>
<span class="highlight">█</span>  © 2026 VALIANT ZIPPU  ◆  ALL RIGHTS RESERVED           <span class="highlight">█</span>
<span class="highlight">█                                                          █</span>
<span class="highlight">████████████████████████████████████████████████████████████</span>
  </div>

  <!-- FOOTER TEXT -->
  <div class="footer-text">
    <span style="color:#1a1a1a;">⬩</span> EXISTENCE RECORDED <span style="color:#1a1a1a;">⬩</span>
    <span style="display:block;margin-top:8px;color:#111;font-size:8px;letter-spacing:2px;">
      <span class="pulse-dot"></span> SYSTEM ACTIVE
    </span>
  </div>

  <!-- VIEW COUNTER -->
  <div style="text-align:center;margin-top:20px;padding-top:16px;border-top:1px solid #0f0f0f;">
    <img src="https://komarev.com/ghpvc/?username=ValiantZippu&color=333&style=flat-square&label=RECORDS" alt="views" style="opacity:0.5;">
  </div>

  <!-- CURSOR -->
  <div style="text-align:right;margin-top:10px;color:#111;font-size:10px;letter-spacing:2px;">
    <span class="cursor"></span> root@valiant:~$
  </div>

</div>
</body>
</html>
