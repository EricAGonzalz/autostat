<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CFB Rankings</title>

  <style>
    :root{
      --bg:#f4f4f4;
      --card:#ffffff;
      --text:#111;
      --muted:#666;
      --grid:#dddddd;

      --head-bg:#0b0b0b;
      --head-fg:#ffffff;

      --chip:#f0f0f0;
      --chip-border:#d6d6d6;

      --row-alt:#fafafa;
      --row-hover:#efefef;

      /* Champion highlight */
      --champ-bg:#fff7cc;
      --champ-border:#d6b800;
      --champ-text:#1a1a1a;

      /* "KenPom-like" separators */
      --divide:#bdbdbd;

      /* Links */
      --link:#0a58ca;
      --link-hover:#eef5ff;
    }

    body{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 20px;
      background: var(--bg);
      color: var(--text);
    }

    .page{
      max-width: 1300px;
      margin: 0 auto;
    }

    .topbar{
      background: var(--card);
      border: 1px solid #cfcfcf;
      border-top: 4px solid #111;
      border-radius: 2px;
      box-shadow: none;
      padding: 14px 14px 10px 14px;
    }

    .brandrow{
      display: flex;
      gap: 12px;
      align-items: baseline;
      justify-content: space-between;
      flex-wrap: wrap;
    }

    h1{
      margin: 0;
      font-size: 22px;
      letter-spacing: 0.2px;
    }

    .subtitle{
      margin: 6px 0 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.35;
    }

    .statusline{
      margin: 8px 0 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.35;
    }

    .controls{
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px solid #e8e8e8;
    }

    .control{
      display: flex;
      gap: 6px;
      align-items: center;
      background: var(--chip);
      border: 1px solid var(--chip-border);
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 13px;
    }

    .control label{
      color: #333;
      white-space: nowrap;
    }

    .control input,
    .control select{
      border: 0;
      background: transparent;
      outline: none;
      font-size: 13px;
      min-width: 140px;
    }

    .control input::placeholder{
      color: #888;
    }

    .links{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
      margin-top: 10px;
      color: var(--muted);
      font-size: 13px;
    }

    .links a{
      color: var(--link);
      text-decoration: none;
      padding: 2px 6px;
      border-radius: 6px;
      cursor: pointer;
    }

    .links a:hover{
      text-decoration: underline;
      background: var(--link-hover);
    }

    .spacer{
      flex: 1;
    }

    .header-link{
      color: var(--link);
      text-decoration: none;
      padding: 6px 9px;
      border-radius: 7px;
      font-size: 13px;
      white-space: nowrap;
    }

    .header-link:hover{
      text-decoration: underline;
      background: var(--link-hover);
    }

    #table-wrapper{
      margin-top: 14px;
      overflow-x: auto;
      background: var(--card);
      border: 1px solid #cfcfcf;
      border-radius: 2px;
      box-shadow: none;
      padding: 10px;
    }

    table{
      border-collapse: collapse;
      width: 100%;
      font-size: 13px;
    }

    thead th{
      position: sticky;
      top: 0;
      z-index: 3;
      background: var(--head-bg);
      color: var(--head-fg);
      border: 1px solid #222;
    }

    thead tr.group th{
      font-weight: 700;
      font-size: 12px;
      letter-spacing: 0.3px;
      text-transform: none;
      padding-top: 8px;
      padding-bottom: 8px;
    }

    th, td{
      padding: 6px 8px;
      border: 1px solid var(--grid);
      text-align: right;
      vertical-align: middle;
      white-space: nowrap; /* keeps headers aligned and icons on one line */
    }

    /* Left align "text columns" */
    td.col-team, th.col-team,
    td.col-conf, th.col-conf{
      text-align: left;
    }

    tbody tr:nth-child(even){
      background: var(--row-alt);
    }

    tbody tr:hover{
      background: var(--row-hover);
    }

    /* KenPom-like vertical separators between column groups */
    .divide-left{
      border-left: 2px solid var(--divide) !important;
    }

    /* Sorting UI */
    th.sortable{
      cursor: pointer;
      position: relative;
      padding-right: 18px;
      user-select: none;
    }
    th.sortable::after{
      content: "↕";
      position: absolute;
      right: 6px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 0.75em;
      opacity: 0.65;
    }
    th.sortable[data-sort="asc"]::after{ content:"▲"; opacity:0.95; }
    th.sortable[data-sort="desc"]::after{ content:"▼"; opacity:0.95; }

    /* Champion highlight */
    tr.champion{
      background: var(--champ-bg) !important;
      color: var(--champ-text);
      font-weight: 700;
    }
    tr.champion td{
      border-color: #e7da7a;
    }
    tr.champion td:first-child{
      border-left: 3px solid var(--champ-border);
    }
    .trophy{
      margin-left: 6px;
      font-size: 13px;
      opacity: 0.95;
    }

    .note{
      margin: 10px 2px 0 2px;
      color: var(--muted);
      font-size: 12.5px;
      line-height: 1.35;
      display: none;
    }

    .loading{
      margin: 10px 2px 0 2px;
      color: var(--muted);
      font-size: 12.5px;
      line-height: 1.35;
      display: none;
    }

    .conference-menu{
      position: relative;
      display: inline-block;
    }

    .conference-menu-button{
      border: 0;
      background: transparent;
      color: var(--text);
      font-size: 13px;
      min-width: 140px;
      text-align: left;
      cursor: pointer;
      padding: 0;
      display: inline-flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }

    .conference-menu-button .caret{
      font-size: 10px;
      transition: transform 0.15s ease;
    }

    .conference-menu.open .conference-menu-button .caret{
      transform: rotate(180deg);
    }

    .conference-menu-list{
      display: none;
      position: absolute;
      left: 0;
      top: calc(100% + 10px);
      z-index: 30;
      min-width: 230px;
      max-height: 340px;
      overflow-y: auto;
      padding: 8px;
      background: var(--card);
      border: 1px solid var(--chip-border);
      border-radius: 10px;
      box-shadow: 0 6px 20px rgba(0,0,0,0.16);
    }

    .conference-menu.open .conference-menu-list{
      display: block;
    }

    .conference-menu-actions{
      display: flex;
      gap: 6px;
      padding-bottom: 7px;
      margin-bottom: 5px;
      border-bottom: 1px solid #e8e8e8;
    }

    .conference-menu-actions button{
      border: 0;
      background: var(--chip);
      color: var(--text);
      border-radius: 7px;
      padding: 5px 8px;
      font-size: 12px;
      cursor: pointer;
    }

    .conference-menu-actions button:hover{
      background: var(--link-hover);
    }

    .conference-option{
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 5px;
      border-radius: 6px;
      cursor: pointer;
      white-space: nowrap;
    }

    .conference-option:hover{
      background: var(--link-hover);
    }

    .conference-option input{
      min-width: 0;
      margin: 0;
    }

    .print-button{
      border: 1px solid var(--chip-border);
      background: var(--card);
      color: var(--text);
      border-radius: 999px;
      padding: 7px 14px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
    }

    .print-button:hover{
      background: var(--link-hover);
    }

    .publish-menu{
      position: relative;
      display: inline-block;
    }

    .publish-menu-button{
      display: inline-flex;
      align-items: center;
      gap: 7px;
    }

    .publish-menu-button .caret{
      font-size: 10px;
      transition: transform 0.15s ease;
    }

    .publish-menu.open .publish-menu-button .caret{
      transform: rotate(180deg);
    }

    .publish-menu-list{
      display: none;
      position: absolute;
      right: 0;
      top: calc(100% + 6px);
      z-index: 20;
      min-width: 190px;
      padding: 5px;
      margin: 0;
      list-style: none;
      background: var(--card);
      border: 1px solid var(--chip-border);
      border-radius: 10px;
      box-shadow: 0 6px 20px rgba(0,0,0,0.16);
    }

    .publish-menu.open .publish-menu-list{
      display: block;
    }

    .publish-menu-list button{
      width: 100%;
      border: 0;
      background: transparent;
      color: var(--text);
      text-align: left;
      padding: 9px 10px;
      border-radius: 7px;
      font-size: 13px;
      cursor: pointer;
    }

    .publish-menu-list button:hover{
      background: var(--link-hover);
    }

    .png-export-stage{
      position: fixed;
      left: -20000px;
      top: 0;
      width: 1320px;
      pointer-events: none;
      z-index: -1;
    }

    .png-report-page{
      box-sizing: border-box;
      width: 1320px;
      height: 1020px;
      padding: 46px 48px 38px 48px;
      background: #fff;
      color: #000;
      font-family: Arial, Helvetica, sans-serif;
      display: flex;
      flex-direction: column;
    }

    .png-report-page .png-report-header{
      margin-bottom: 14px;
      padding-bottom: 10px;
      border-bottom: 3px solid #111;
    }

    .png-report-page .png-report-header h1{
      margin: 0;
      font-size: 28px;
      letter-spacing: 0.2px;
    }

    .png-report-page .png-report-season{
      margin: 4px 0 0 0;
      font-size: 17px;
      font-weight: 700;
    }

    .png-report-page .png-report-meta{
      margin: 4px 0 0 0;
      font-size: 12px;
      color: #444;
    }

    .png-report-page table{
      width: 100%;
      border-collapse: collapse;
      font-size: 11px;
    }

    .png-report-page thead th{
      position: static;
      background: #111;
      color: #fff;
      border: 1px solid #222;
    }

    .png-report-page th,
    .png-report-page td{
      padding: 4px 5px;
      border: 1px solid #b9b9b9;
      text-align: right;
      white-space: nowrap;
    }

    .png-report-page td.col-team,
    .png-report-page th.col-team,
    .png-report-page td.col-conf,
    .png-report-page th.col-conf{
      text-align: left;
    }

    .png-report-page tbody tr:nth-child(even){
      background: #f5f5f5;
    }

    .png-report-page tr.champion{
      background: #fff2b3 !important;
      font-weight: 700;
    }

    .png-report-page .png-report-footer{
      margin-top: auto;
      padding-top: 8px;
      border-top: 1px solid #888;
      display: flex;
      justify-content: space-between;
      gap: 20px;
      font-size: 10px;
      color: #444;
    }

    .print-report-header,
    .print-report-footer{
      display: none;
    }

    @media print{
      @page{
        size: landscape;
        margin: 0.45in 0.4in 0.55in 0.4in;
      }

      body{
        margin: 0;
        background: #fff;
        color: #000;
        font-family: Arial, Helvetica, sans-serif;
      }

      .page{
        max-width: none;
      }

      .team-link{
        color: inherit !important;
        text-decoration: none !important;
      }

      .topbar{
        display: none !important;
      }

      .controls,
      .links,
      .print-button,
      .publish-menu,
      .loading,
      .note{
        display: none !important;
      }

      .print-report-header{
        display: block !important;
        margin: 0 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #111;
      }

      .print-report-header h1{
        margin: 0;
        font-size: 18pt;
        letter-spacing: 0.2px;
      }

      .print-report-header .report-season{
        margin: 3px 0 0 0;
        font-size: 11pt;
        font-weight: 700;
      }

      .print-report-header .report-meta{
        margin: 3px 0 0 0;
        font-size: 8.5pt;
        color: #444;
      }

      #table-wrapper{
        margin-top: 0;
        overflow: visible;
        box-shadow: none;
        border-radius: 0;
        padding: 0;
      }

      table{
        width: 100%;
        border-collapse: collapse;
        font-size: 7.5pt;
      }

      thead{
        display: table-header-group;
      }

      thead th{
        position: static;
        background: #111 !important;
        color: #fff !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }

      th, td{
        padding: 4px 5px;
        border: 1px solid #b9b9b9;
      }

      tbody tr:nth-child(even){
        background: #f5f5f5 !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }

      tr.champion{
        background: #fff2b3 !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }

      tbody tr{
        break-inside: avoid;
        page-break-inside: avoid;
      }

      .print-report-footer{
        display: block !important;
        margin-top: 8px;
        padding-top: 6px;
        border-top: 1px solid #888;
        font-size: 7.5pt;
        color: #444;
      }
    }

    @media (max-width: 720px){
      body{ margin: 12px; }
      .control input, .control select{ min-width: 120px; }
    }
  
    .team-link{
      color: var(--link);
      text-decoration: none;
      font-weight: 600;
    }

    .team-link:hover{
      text-decoration: underline;
      background: var(--link-hover);
      border-radius: 4px;
    }

    .team-link:focus-visible{
      outline: 2px solid var(--link);
      outline-offset: 2px;
      border-radius: 3px;
    }

    .live-dot{
      display:inline-block;
      width:8px;
      height:8px;
      margin-left:7px;
      border-radius:50%;
      background:#d71920;
      box-shadow:0 0 0 2px rgba(215,25,32,.12);
      vertical-align:middle;
      animation:livePulse 1.5s ease-in-out infinite;
    }

    @keyframes livePulse{
      0%,100%{ opacity:1; }
      50%{ opacity:.38; }
    }

    @media (prefers-reduced-motion: reduce){
      .live-dot{ animation:none; }
    }

  </style>
</head>

<body>
  <div class="page">
    <div class="topbar">
      <div class="brandrow">
        <div>
          <h1 id="pageTitle">CFB Rankings</h1>
          <p class="subtitle" id="pageSubtitle">Only FBS vs FBS games are used in calculations.</p>
          <p class="statusline" id="statusLine"></p>
        </div>

        <div class="spacer"></div>

        <a class="header-link" href="matchup.html">Matchup Predictor</a>

        <div class="control" title="Choose a season to view">
          <label for="yearSelect">Season</label>
          <select id="yearSelect"></select>
        </div>
      </div>

      <div class="controls">
        <div class="control" title="Filter by team name">
          <label for="teamSearch">Team</label>
          <input id="teamSearch" type="text" placeholder="Search teams..." />
        </div>

        <div class="control" title="Filter by one or more conferences">
          <label>Conf</label>
          <div class="conference-menu" id="conferenceMenu">
            <button id="conferenceMenuButton" class="conference-menu-button" type="button" aria-haspopup="true" aria-expanded="false">
              <span id="conferenceMenuText">All conferences</span>
              <span class="caret" aria-hidden="true">▼</span>
            </button>
            <div class="conference-menu-list" id="conferenceMenuList">
              <div class="conference-menu-actions">
                <button id="conferenceSelectAll" type="button">Select all</button>
                <button id="conferenceClear" type="button">Clear</button>
              </div>
              <div id="conferenceOptions"></div>
            </div>
          </div>
        </div>

        <div class="control" title="Show only the top N teams by Rk">
          <label for="topN">Filter</label>
          <select id="topN">
            <option value="0" selected>All</option>
            <option value="25">Top 25</option>
            <option value="50">Top 50</option>
            <option value="100">Top 100</option>
          </select>
        </div>

<div class="control" title="Quick toggle for row striping">
  <label for="stripeToggle">Striping</label>
  <select id="stripeToggle">
    <option value="on" selected>On</option>
    <option value="off">Off</option>
  </select>
</div>

        <div class="publish-menu" id="publishMenu">
          <button id="publishMenuButton" class="print-button publish-menu-button" type="button" aria-haspopup="true" aria-expanded="false" title="Publish the currently displayed rankings">
            Publish
            <span class="caret" aria-hidden="true">▼</span>
          </button>
          <div class="publish-menu-list" role="menu" aria-label="Publish options">
            <button id="publishPdf" type="button" role="menuitem">Publish to PDF</button>
            <button id="publishPng" type="button" role="menuitem">Publish PNGs as ZIP</button>
          </div>
        </div>
      </div>

      <div class="links" id="finalLinks">
        <span>Final Results:</span>
        <!-- Year links are generated automatically -->
      </div>
    </div>

    <section class="print-report-header" aria-hidden="true">
      <h1>College Football Efficiency Rankings</h1>
      <p class="report-season" id="printReportSeason"></p>
      <p class="report-meta" id="printReportMeta"></p>
    </section>

    <div id="table-wrapper">
      <table id="rankings">
        <thead></thead>
        <tbody></tbody>
      </table>

      <div class="loading" id="loadingLine">Loading…</div>
      <div class="note" id="champNote"></div>
    </div>

    <footer class="print-report-footer" aria-hidden="true">
      Rankings use FBS-vs-FBS games only. Generated from the CFB Rankings dataset for publication.
    </footer>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js"></script>
  <script>
    const DATA_DIR = "data";
    const FIRST_SEASON = 2009;

    // Set this to the "current live season" year (you can change once per season, or keep it automatic).
    const CURRENT_SEASON = new Date().getFullYear();

    // Default year to open if no ?year= is provided
    const DEFAULT_YEAR = "2026";

    // Optional: champions file. If missing, champion highlighting just won't happen.
    const CHAMPIONS_JSON_URL = `${DATA_DIR}/champions.json`;

    const RAW_BASE =
      "https://raw.githubusercontent.com/EricAGonzalz/CFBRankings/main/data/";

    function csvForYear(year) {
      return `${RAW_BASE}${year}%20Master.csv`;
    }

    // Column grouping (edit this mapping if your CSV headers change)
    const GROUPS = [
      { title: "Team", cols: ["Rk", "Team", "Conference", "W", "L"] },
      { title: "Ratings", cols: ["NetRtg", "AdjRtg", "AdjRk"] },
      { title: "Wins", cols: ["Win %", "PyW %", "Luck", "Luck Z"] },
      { title: "Efficiency", cols: ["ORtg", "Ortg" , "DRtg"] },
      { title: "Totals", cols: ["PF", "PA", "ODrives", "DDrives"] },
      { title: "Schedule", cols: ["SOS", "SOSFac"] }
    ];

    // ---- Cached DOM references (avoids repeated getElementById lookups) ----
    const els = {
      pageTitle: document.getElementById("pageTitle"),
      statusLine: document.getElementById("statusLine"),
      yearSelect: document.getElementById("yearSelect"),
      teamSearch: document.getElementById("teamSearch"),
      conferenceMenu: document.getElementById("conferenceMenu"),
      conferenceMenuButton: document.getElementById("conferenceMenuButton"),
      conferenceMenuText: document.getElementById("conferenceMenuText"),
      conferenceOptions: document.getElementById("conferenceOptions"),
      conferenceSelectAll: document.getElementById("conferenceSelectAll"),
      conferenceClear: document.getElementById("conferenceClear"),
      topN: document.getElementById("topN"),
      stripeToggle: document.getElementById("stripeToggle"),
      publishMenu: document.getElementById("publishMenu"),
      publishMenuButton: document.getElementById("publishMenuButton"),
      publishPdf: document.getElementById("publishPdf"),
      publishPng: document.getElementById("publishPng"),
      printReportSeason: document.getElementById("printReportSeason"),
      printReportMeta: document.getElementById("printReportMeta"),
      finalLinks: document.getElementById("finalLinks"),
      table: document.getElementById("rankings"),
      loadingLine: document.getElementById("loadingLine"),
      champNote: document.getElementById("champNote"),
    };
    els.thead = els.table.querySelector("thead");
    els.tbody = els.table.querySelector("tbody");

    // State
    let CHAMPIONS_BY_YEAR = {};       // loaded from champions.json (if present)
    let ACTIVE_YEAR = null;
    let ACTIVE_CHAMPION = null;       // string team name, or null
    let ACTIVE_CHAMPION_LC = null;    // lowercased, precomputed once per year
    let ACTIVE_IS_FINAL = false;      // true if champion exists for that year
    let AVAILABLE_YEARS = [];         // years to show in the season dropdown

    // Companion live metadata written by autostat.py.
    let LIVE_META = {
      updatedAt: null,
      liveGames: [],
      liveTeams: new Set(),
      gameByTeam: new Map()
    };

    let STATE = null; // replaces window.__CFB_STATE__

    // Small debounce helper so typing in the search box doesn't re-render on every keystroke
    function debounce(fn, wait) {
      let t;
      return (...args) => {
        clearTimeout(t);
        t = setTimeout(() => fn(...args), wait);
      };
    }

    // Robust CSV parser (handles quoted commas, quotes, and CRLF/LF)
    function parseCSV(text) {
      const rows = [];
      let row = [];
      let cell = "";
      let inQuotes = false;

      for (let i = 0; i < text.length; i++) {
        const ch = text[i];
        const next = text[i + 1];

        if (ch === '"') {
          if (inQuotes && next === '"') {
            cell += '"';
            i++;
          } else {
            inQuotes = !inQuotes;
          }
          continue;
        }

        if (ch === "," && !inQuotes) {
          row.push(cell);
          cell = "";
          continue;
        }

        if ((ch === "\n" || ch === "\r") && !inQuotes) {
          if (ch === "\r" && next === "\n") i++;
          row.push(cell);
          cell = "";
          if (row.some(v => String(v).trim() !== "")) rows.push(row);
          row = [];
          continue;
        }

        cell += ch;
      }

      row.push(cell);
      if (row.some(v => String(v).trim() !== "")) rows.push(row);

      if (!rows.length) return { header: [], rows: [] };
      return { header: rows[0].map(h => h.trim()), rows: rows.slice(1) };
    }

    // Repair classic mojibake like "San JosÃ©" -> "San José" (display-only)
    function fixMojibake(s) {
      if (typeof s !== "string") return s;

      // Only attempt on strings that look like classic UTF-8->Latin1 mojibake
      if (!/[ÃÂâ€]/.test(s)) return s;

      try {
        const bytes = new Uint8Array([...s].map(ch => ch.charCodeAt(0) & 0xff));
        const fixed = new TextDecoder("utf-8", { fatal: false }).decode(bytes);
        if (fixed && fixed !== s) return fixed;
      } catch {
        // ignore
      }
      return s;
    }

    function indexByHeader(header) {
      const map = new Map();
      header.forEach((h, i) => map.set(h, i));
      return map;
    }

    function getSelectedConferences() {
      return Array.from(els.conferenceOptions.querySelectorAll('input[type="checkbox"]:checked'))
        .map(input => input.value);
    }

    function updateConferenceMenuText() {
      const selected = getSelectedConferences();
      const total = els.conferenceOptions.querySelectorAll('input[type="checkbox"]').length;

      if (!selected.length || selected.length === total) {
        els.conferenceMenuText.textContent = "All conferences";
      } else if (selected.length === 1) {
        els.conferenceMenuText.textContent = selected[0];
      } else {
        els.conferenceMenuText.textContent = `${selected.length} conferences`;
      }
    }

    function buildConferenceOptions(allRows, headerMap) {
      const confIndex = headerMap.get("Conference");
      els.conferenceOptions.innerHTML = "";

      if (confIndex === undefined) {
        updateConferenceMenuText();
        return;
      }

      const set = new Set();
      for (const r of allRows) {
        const v = (r[confIndex] ?? "").trim();
        if (v) set.add(v);
      }

      const frag = document.createDocumentFragment();
      Array.from(set).sort().forEach(conf => {
        const label = document.createElement("label");
        label.className = "conference-option";

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.value = conf;
        checkbox.checked = true;
        checkbox.addEventListener("change", () => {
          updateConferenceMenuText();
          renderBody();
        });

        const text = document.createElement("span");
        text.textContent = conf;

        label.appendChild(checkbox);
        label.appendChild(text);
        frag.appendChild(label);
      });
      els.conferenceOptions.appendChild(frag);
      updateConferenceMenuText();
    }

    function getGroupBoundaryStarts(headerMap, orderedCols) {
      const starts = new Set();
      let running = 0;
      let firstAdded = false;

      for (const group of GROUPS) {
        const existing = group.cols.filter(c => headerMap.has(c) && orderedCols.includes(c));
        if (!existing.length) continue;

        if (!firstAdded) firstAdded = true;
        else starts.add(running);

        running += existing.length;
      }

      const groupedSet = new Set(GROUPS.flatMap(g => g.cols));
      const leftovers = orderedCols.filter(c => !groupedSet.has(c) && headerMap.has(c));
      if (leftovers.length && running > 0) starts.add(running);

      return starts;
    }

    function inferOrderedColumns(header) {
      const inGroups = GROUPS.flatMap(g => g.cols).filter(c => header.includes(c));
      const leftovers = header.filter(c => !inGroups.includes(c));
      return [...inGroups, ...leftovers];
    }

    function buildGroupedHeader(thead, header, headerMap, orderedCols, boundaryStarts) {
      const frag = document.createDocumentFragment();

      const trGroup = document.createElement("tr");
      trGroup.className = "group";

      const trCols = document.createElement("tr");
      let currentGroupStartIndex = 0;

      for (const group of GROUPS) {
        const existing = group.cols.filter(c => headerMap.has(c) && orderedCols.includes(c));
        if (!existing.length) continue;

        const th = document.createElement("th");
        th.textContent = group.title;
        th.colSpan = existing.length;

        if (currentGroupStartIndex !== 0) th.classList.add("divide-left");

        trGroup.appendChild(th);
        currentGroupStartIndex += existing.length;
      }

      const groupedSet = new Set(GROUPS.flatMap(g => g.cols));
      const leftovers = orderedCols.filter(c => !groupedSet.has(c) && headerMap.has(c));
      if (leftovers.length) {
        const th = document.createElement("th");
        th.textContent = "Other";
        th.colSpan = leftovers.length;
        th.classList.add("divide-left");
        trGroup.appendChild(th);
      }

      orderedCols.forEach((col, idx) => {
        if (!headerMap.has(col)) return;

        const th = document.createElement("th");
        th.textContent = col;
        th.classList.add("sortable");
        th.dataset.index = String(idx);
        th.dataset.sort = "none";

        if (col === "Team") th.classList.add("col-team");
        if (col === "Conference") th.classList.add("col-conf");

        if (boundaryStarts.has(idx)) th.classList.add("divide-left");

        trCols.appendChild(th);
      });

      frag.appendChild(trGroup);
      frag.appendChild(trCols);
      thead.innerHTML = "";
      thead.appendChild(frag);
    }

    function buildTable(header, allRows) {
      const thead = els.thead;
      const tbody = els.tbody;

      tbody.innerHTML = "";

      const headerMap = indexByHeader(header);
      const orderedCols = inferOrderedColumns(header);
      const boundaryStarts = getGroupBoundaryStarts(headerMap, orderedCols);

      buildConferenceOptions(allRows, headerMap);
      buildGroupedHeader(thead, header, headerMap, orderedCols, boundaryStarts);

      const rendered = [];
      for (const raw of allRows) {
        if (!raw.some(v => String(v ?? "").trim() !== "")) continue;

        const cells = new Array(orderedCols.length);
        for (let i = 0; i < orderedCols.length; i++) {
          const idx = headerMap.get(orderedCols[i]);
          cells[i] = idx === undefined ? "" : (raw[idx] ?? "");
        }

        rendered.push(cells);
      }

      // Precompute everything renderBody() needs so it never has to recompute
      // per-call (boundary positions, column indices, etc.) — these are fixed
      // for the lifetime of this table/season.
      STATE = {
        header,
        headerMap,
        orderedCols,
        boundaryStarts,
        teamCol: orderedCols.indexOf("Team"),
        confCol: orderedCols.indexOf("Conference"),
        rkCol: orderedCols.indexOf("Rk"),
        rows: rendered
      };

      renderBody();
      makeSortable(thead);
    }

    function renderBody() {
      const tbody = els.tbody;
      if (!STATE) {
        tbody.innerHTML = "";
        return;
      }

      const teamSearches = els.teamSearch.value
        .toLowerCase()
        .split(/[,;\n]+/)
        .map(team => team.trim())
        .filter(Boolean);

      const selectedConferences = getSelectedConferences();
      const conferenceOptionCount = els.conferenceOptions.querySelectorAll('input[type="checkbox"]').length;
      const topN = Number(els.topN.value || 0);

      const { teamCol, confCol, rkCol, boundaryStarts, orderedCols } = STATE;

      let filtered = STATE.rows;

      if (teamSearches.length && teamCol >= 0) {
        filtered = filtered.filter(r => {
          const teamName = String(r[teamCol] ?? "").toLowerCase();
          return teamSearches.some(search => teamName.includes(search));
        });
      }

      if (confCol >= 0 && selectedConferences.length > 0 && selectedConferences.length < conferenceOptionCount) {
        const selectedSet = new Set(selectedConferences);
        filtered = filtered.filter(r => selectedSet.has(String(r[confCol] ?? "")));
      } else if (confCol >= 0 && conferenceOptionCount > 0 && selectedConferences.length === 0) {
        filtered = [];
      }

      if (topN > 0 && rkCol >= 0) {
        filtered = filtered.filter(r => {
          const n = Number(String(r[rkCol] ?? "").trim());
          return Number.isFinite(n) && n <= topN;
        });
      }

      const frag = document.createDocumentFragment();

      for (const cells of filtered) {
        const tr = document.createElement("tr");

        // Champion highlight: only if this season is final and champion is set
        let isChampion = false;
        if (ACTIVE_IS_FINAL && ACTIVE_CHAMPION_LC && teamCol >= 0) {
          const teamName = String(cells[teamCol] ?? "").trim().toLowerCase();
          if (teamName === ACTIVE_CHAMPION_LC) {
            tr.classList.add("champion");
            isChampion = true;
          }
        }

        for (let idx = 0; idx < cells.length; idx++) {
          const td = document.createElement("td");
          const fixed = fixMojibake(cells[idx]);

          const colName = orderedCols[idx];
          if (colName === "Team") td.classList.add("col-team");
          if (colName === "Conference") td.classList.add("col-conf");
          if (boundaryStarts.has(idx)) td.classList.add("divide-left");

          // Team names link to a single reusable team page. The selected
          // season is included so historical seasons can open the same page.
          if (colName === "Team" && String(fixed ?? "").trim()) {
            const teamLink = document.createElement("a");
            teamLink.className = "team-link";
            teamLink.textContent = fixed;
            teamLink.href =
              `team.html?team=${encodeURIComponent(String(fixed).trim())}` +
              `&year=${encodeURIComponent(String(ACTIVE_YEAR || DEFAULT_YEAR))}`;
            teamLink.title = `View ${fixed} team profile`;
            td.appendChild(teamLink);
          } else {
            td.textContent = fixed;
          }

          // ESPN-style live light beside teams currently playing.
          if (colName === "Team") {
            const teamKey = String(fixed ?? "").trim().toLowerCase();
            if (LIVE_META.liveTeams.has(teamKey)) {
              const dot = document.createElement("span");
              dot.className = "live-dot";
              dot.title = buildLiveTooltip(fixed);
              dot.setAttribute("aria-label", "Live game in progress");
              td.appendChild(dot);
            }
          }

          // Trophy for champion team
          if (colName === "Team" && isChampion) {
            const span = document.createElement("span");
            span.className = "trophy";
            span.textContent = "🏆";
            td.appendChild(span);
          }

          tr.appendChild(td);
        }

        frag.appendChild(tr);
      }

      tbody.innerHTML = "";
      tbody.appendChild(frag);
    }

    function makeSortable(thead) {
      const ths = thead.querySelectorAll("tr:last-child th.sortable");

      ths.forEach(th => {
        th.addEventListener("click", () => {
          const index = Number(th.dataset.index);
          const current = th.dataset.sort || "none";
          const next = current === "asc" ? "desc" : "asc";

          ths.forEach(h => (h.dataset.sort = "none"));
          th.dataset.sort = next;

          if (!STATE) return;

          STATE.rows.sort((a, b) => {
            const aText = String(a[index] ?? "");
            const bText = String(b[index] ?? "");

            const aNum = Number(aText);
            const bNum = Number(bText);
            const aIsNum = aText.trim() !== "" && Number.isFinite(aNum);
            const bIsNum = bText.trim() !== "" && Number.isFinite(bNum);

            let cmp;
            if (aIsNum && bIsNum) cmp = aNum - bNum;
            else cmp = aText.localeCompare(bText, undefined, { numeric: true, sensitivity: "base" });

            return next === "asc" ? cmp : -cmp;
          });

          renderBody();
        });
      });
    }

    let stripeStyleEl = null;
    function setStriping(on) {
      if (on) {
        if (stripeStyleEl) {
          stripeStyleEl.remove();
          stripeStyleEl = null;
        }
        return;
      }

      if (!stripeStyleEl) {
        stripeStyleEl = document.createElement("style");
        stripeStyleEl.id = "no-striping-style";
        stripeStyleEl.textContent = `
          tbody tr:nth-child(even){ background: transparent !important; }
        `;
        document.head.appendChild(stripeStyleEl);
      }
    }

    function setLoading(isLoading) {
      els.loadingLine.style.display = isLoading ? "block" : "none";
    }

    function setChampionNote() {
      const note = els.champNote;
      if (ACTIVE_IS_FINAL && ACTIVE_CHAMPION) {
        note.textContent = `${ACTIVE_CHAMPION} is highlighted as the national champion.`;
        note.style.display = "block";
      } else {
        note.textContent = "";
        note.style.display = "none";
      }
    }

    function setStatusLine(extraText) {
      els.statusLine.textContent = extraText || "";
    }

    function liveJsonForYear(year) {
      return `${RAW_BASE}${year}%20Live.json`;
    }

    function formatUpdatedAt(isoString) {
      if (!isoString) return null;
      const dt = new Date(isoString);
      if (Number.isNaN(dt.getTime())) return null;

      return new Intl.DateTimeFormat("en-US", {
        timeZone: "America/New_York",
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "numeric",
        minute: "2-digit",
        timeZoneName: "short"
      }).format(dt);
    }

    function buildLiveTooltip(teamName) {
      const game = LIVE_META.gameByTeam.get(String(teamName || "").toLowerCase());
      if (!game) return "Live game in progress";

      const home = game.homeTeam || "Home";
      const away = game.awayTeam || "Away";
      const hp = game.homePoints ?? 0;
      const ap = game.awayPoints ?? 0;
      const period = game.period ? `Q${game.period}` : "Live";
      const clock = game.clock ? ` ${game.clock}` : "";

      return `${away} ${ap} - ${home} ${hp} • ${period}${clock}`;
    }

    async function loadLiveMetadata(year) {
      LIVE_META = {
        updatedAt: null,
        liveGames: [],
        liveTeams: new Set(),
        gameByTeam: new Map()
      };

      try {
        const url = `${liveJsonForYear(year)}?t=${Date.now()}`;
        const r = await fetch(url, { cache: "no-store" });
        if (!r.ok) return LIVE_META;

        const data = await r.json();
        const games = Array.isArray(data?.liveGames) ? data.liveGames : [];
        const teams = new Set(
          (Array.isArray(data?.liveTeams) ? data.liveTeams : [])
            .map(t => String(t).toLowerCase())
        );

        const gameByTeam = new Map();
        for (const game of games) {
          for (const team of [game.homeTeam, game.awayTeam]) {
            if (team) gameByTeam.set(String(team).toLowerCase(), game);
          }
        }

        LIVE_META = {
          updatedAt: data?.updatedAt || null,
          liveGames: games,
          liveTeams: teams,
          gameByTeam
        };
      } catch (err) {
        console.warn("Live metadata could not be loaded:", err);
      }

      return LIVE_META;
    }

    function currentStatusText() {
      if (ACTIVE_IS_FINAL && ACTIVE_CHAMPION) {
        return `Final season. Champion: ${ACTIVE_CHAMPION}.`;
      }

      const parts = [];
      const updated = formatUpdatedAt(LIVE_META.updatedAt);

      if (updated) parts.push(`Last updated: ${updated}`);
      else parts.push("Live season");

      const liveCount = LIVE_META.liveGames.length;
      if (liveCount > 0) {
        parts.push(`${liveCount} live FBS game${liveCount === 1 ? "" : "s"} included`);
      } else {
        parts.push("No live FBS games currently in progress");
      }

      return parts.join(" • ");
    }

    async function loadChampionsJson() {
      try {
        const r = await fetch(CHAMPIONS_JSON_URL, { cache: "no-store" });
        if (!r.ok) return {};
        const data = await r.json();
        return (data && typeof data === "object") ? data : {};
      } catch {
        return {};
      }
    }

    // Builds the list of selectable seasons. (No network probing is done here —
    // that would mean one request per year just to populate a dropdown. If you
    // want to hide years with no CSV, maintain an explicit list instead.)
    function buildSeasonYearList() {
      const years = [];
      for (let y = CURRENT_SEASON; y >= FIRST_SEASON; y--) {
        years.push(String(y));
      }
      return years;
    }

    function populateYearSelect(years) {
      const sel = els.yearSelect;
      const frag = document.createDocumentFragment();
      years.forEach(y => {
        const opt = document.createElement("option");
        opt.value = y;
        opt.textContent = y;
        frag.appendChild(opt);
      });
      sel.innerHTML = "";
      sel.appendChild(frag);
    }

    function populateFinalLinks() {
      const wrap = els.finalLinks;

      // Remove existing generated links (keep the "Final results:" label)
      wrap.querySelectorAll("a.yearLink").forEach(a => a.remove());

      // Only show links for years that have a champion set
      const finalYears = AVAILABLE_YEARS.filter(y => !!CHAMPIONS_BY_YEAR[y]);

      const frag = document.createDocumentFragment();
      finalYears.forEach(y => {
        const a = document.createElement("a");
        a.href = "#";
        a.className = "yearLink";
        a.dataset.year = y;
        a.textContent = y;
        a.addEventListener("click", (e) => {
          e.preventDefault();
          els.yearSelect.value = y;
          loadYear(y);
          history.replaceState({}, "", `?year=${encodeURIComponent(y)}`);
        });
        frag.appendChild(a);
      });
      wrap.appendChild(frag);
    }

    async function loadYear(year) {
      if (!year) return;

      ACTIVE_YEAR = String(year);
      ACTIVE_CHAMPION = CHAMPIONS_BY_YEAR[ACTIVE_YEAR] || null;
      ACTIVE_CHAMPION_LC = ACTIVE_CHAMPION ? ACTIVE_CHAMPION.toLowerCase() : null;
      ACTIVE_IS_FINAL = !!ACTIVE_CHAMPION; // final if champion exists

      els.pageTitle.textContent = `CFB Rankings ${ACTIVE_YEAR}`;

      setChampionNote();

      // Clear filters on year change (optional; comment out if you want to keep filters)
      els.teamSearch.value = "";
      els.topN.value = "0";

      const url = csvForYear(ACTIVE_YEAR);

      setLoading(true);
      setStatusLine(`Loading ${url}…`);

      try {
        const r = await fetch(url, { cache: "no-store" });
        if (!r.ok) throw new Error("HTTP " + r.status);

        const text = await r.text();
        const { header, rows } = parseCSV(text);

        // Load live metadata before rendering rows so live teams get their red dot.
        await loadLiveMetadata(ACTIVE_YEAR);

        if (!header.length) {
          console.error("CSV appears empty or malformed.");
          setStatusLine("CSV appears empty or malformed.");
          return;
        }

        buildTable(header, rows);

        const isStriped = els.stripeToggle.value === "on";
        setStriping(isStriped);

        // Status includes the generated-file timestamp and live-game count.
        setStatusLine(currentStatusText());

      } catch (err) {
        console.error("Failed to load CSV:", err);
        setStatusLine("Failed to load this season's CSV. Make sure the file exists in /data.");
      } finally {
        setLoading(false);
      }
    }

    // Hook up UI
    els.teamSearch.addEventListener("input", debounce(renderBody, 150));
    els.conferenceMenuButton.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = els.conferenceMenu.classList.toggle("open");
      els.conferenceMenuButton.setAttribute("aria-expanded", String(isOpen));
    });

    els.conferenceSelectAll.addEventListener("click", () => {
      els.conferenceOptions.querySelectorAll('input[type="checkbox"]').forEach(input => input.checked = true);
      updateConferenceMenuText();
      renderBody();
    });

    els.conferenceClear.addEventListener("click", () => {
      els.conferenceOptions.querySelectorAll('input[type="checkbox"]').forEach(input => input.checked = false);
      updateConferenceMenuText();
      renderBody();
    });

    document.addEventListener("click", (e) => {
      if (!els.conferenceMenu.contains(e.target)) {
        els.conferenceMenu.classList.remove("open");
        els.conferenceMenuButton.setAttribute("aria-expanded", "false");
      }
    });
    els.topN.addEventListener("change", renderBody);

    els.stripeToggle.addEventListener("change", (e) => {
      setStriping(e.target.value === "on");
    });

    function getPublishMetadata() {
      const selectedConferences = getSelectedConferences();
      const totalConferences = els.conferenceOptions.querySelectorAll('input[type="checkbox"]').length;
      const conf = (!selectedConferences.length || selectedConferences.length === totalConferences)
        ? "All conferences"
        : selectedConferences.join(", ");
      const top = els.topN.value === "0" ? "All teams" : `Top ${els.topN.value}`;
      const team = els.teamSearch.value.trim();
      const filterParts = [conf, top];
      if (team) filterParts.push(`Team filter: ${team}`);

      const seasonText = `${ACTIVE_YEAR} Season${ACTIVE_IS_FINAL ? " — Final Rankings" : " — Current Rankings"}`;
      const metaText = `${filterParts.join(" • ")} • Generated ${new Date().toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" })}`;
      return { seasonText, metaText };
    }

    function closePublishMenu() {
      els.publishMenu.classList.remove("open");
      els.publishMenuButton.setAttribute("aria-expanded", "false");
    }

    els.publishMenuButton.addEventListener("click", (e) => {
      e.stopPropagation();
      const willOpen = !els.publishMenu.classList.contains("open");
      els.publishMenu.classList.toggle("open", willOpen);
      els.publishMenuButton.setAttribute("aria-expanded", String(willOpen));
    });

    document.addEventListener("click", (e) => {
      if (!els.publishMenu.contains(e.target)) closePublishMenu();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closePublishMenu();
    });

    els.publishPdf.addEventListener("click", () => {
      closePublishMenu();
      const { seasonText, metaText } = getPublishMetadata();
      els.printReportSeason.textContent = seasonText;
      els.printReportMeta.textContent = metaText;
      window.print();
    });

    function canvasToPngBlob(canvas) {
      return new Promise((resolve, reject) => {
        canvas.toBlob((blob) => {
          if (!blob) {
            reject(new Error("Could not create PNG image."));
            return;
          }
          resolve(blob);
        }, "image/png");
      });
    }

    function downloadBlob(blob, filename) {
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }

    function buildPngReportPage(rows, pageNumber, pageCount, seasonText, metaText) {
      const page = document.createElement("section");
      page.className = "png-report-page";

      const header = document.createElement("header");
      header.className = "png-report-header";
      header.innerHTML = `
        <h1>College Football Efficiency Rankings</h1>
        <p class="png-report-season"></p>
        <p class="png-report-meta"></p>
      `;
      header.querySelector(".png-report-season").textContent = seasonText;
      header.querySelector(".png-report-meta").textContent = metaText;
      page.appendChild(header);

      const table = document.createElement("table");
      table.innerHTML = `<thead>${els.thead.innerHTML}</thead><tbody></tbody>`;
      const tbody = table.querySelector("tbody");
      rows.forEach(row => tbody.appendChild(row.cloneNode(true)));
      page.appendChild(table);

      const footer = document.createElement("footer");
      footer.className = "png-report-footer";
      const left = document.createElement("span");
      left.textContent = "Rankings use FBS-vs-FBS games only. Generated from the CFB Rankings dataset for publication.";
      const right = document.createElement("span");
      right.textContent = `Page ${pageNumber} of ${pageCount}`;
      footer.append(left, right);
      page.appendChild(footer);

      return page;
    }

    els.publishPng.addEventListener("click", async () => {
      closePublishMenu();

      if (typeof html2canvas !== "function" || typeof JSZip !== "function") {
        alert("PNG publishing could not load the export libraries. Check your internet connection and try again.");
        return;
      }

      const visibleRows = Array.from(els.tbody.querySelectorAll("tr"));
      if (!visibleRows.length) {
        alert("There are no visible rankings to publish.");
        return;
      }

      const { seasonText, metaText } = getPublishMetadata();
      const rowsPerPage = 36;
      const pageCount = Math.ceil(visibleRows.length / rowsPerPage);
      const stage = document.createElement("div");
      stage.className = "png-export-stage";
      document.body.appendChild(stage);

      const oldText = els.publishMenuButton.childNodes[0].nodeValue;
      els.publishMenuButton.childNodes[0].nodeValue = "Publishing PNGs ";
      els.publishMenuButton.disabled = true;

      try {
        const zip = new JSZip();
        const safeYear = String(ACTIVE_YEAR || "rankings").replace(/[^0-9A-Za-z_-]/g, "_");

        for (let pageIndex = 0; pageIndex < pageCount; pageIndex++) {
          const start = pageIndex * rowsPerPage;
          const pageRows = visibleRows.slice(start, start + rowsPerPage);
          const page = buildPngReportPage(pageRows, pageIndex + 1, pageCount, seasonText, metaText);
          stage.appendChild(page);

          const canvas = await html2canvas(page, {
            backgroundColor: "#ffffff",
            scale: 2,
            useCORS: true,
            logging: false,
            width: 1320,
            height: 1020
          });

          const pngBlob = await canvasToPngBlob(canvas);
          const filename = `CFB_Rankings_${safeYear}_Page_${String(pageIndex + 1).padStart(2, "0")}.png`;
          zip.file(filename, pngBlob);
          page.remove();
        }

        const zipBlob = await zip.generateAsync({
          type: "blob",
          compression: "DEFLATE",
          compressionOptions: { level: 6 }
        });
        downloadBlob(zipBlob, `CFB_Rankings_${safeYear}_PNGs.zip`);
      } catch (err) {
        console.error("PNG publishing failed:", err);
        alert("PNG publishing failed. See the browser console for details.");
      } finally {
        stage.remove();
        els.publishMenuButton.childNodes[0].nodeValue = oldText;
        els.publishMenuButton.disabled = false;
      }
    });

    els.yearSelect.addEventListener("change", (e) => {
      const y = e.target.value;
      history.replaceState({}, "", `?year=${encodeURIComponent(y)}`);
      loadYear(y);
    });

    // Boot
    (async function init() {
      // champions.json is optional
      CHAMPIONS_BY_YEAR = await loadChampionsJson();

      AVAILABLE_YEARS = buildSeasonYearList();

      populateYearSelect(AVAILABLE_YEARS);
      populateFinalLinks();

      // Initial year from URL param, else DEFAULT_YEAR if present, else first available
      const params = new URLSearchParams(location.search);
      const requested = params.get("year");
      const initial = (requested && AVAILABLE_YEARS.includes(requested))
        ? requested
        : (AVAILABLE_YEARS.includes(DEFAULT_YEAR) ? DEFAULT_YEAR : AVAILABLE_YEARS[0]);

      els.yearSelect.value = initial;
      await loadYear(initial);

      // Default striping
      setStriping(true);
    })();
  </script>
</body>
</html>
