<?php
ini_set('session.cookie_domain', '.hcr2.xyz');
ini_set('session.cookie_path', '/');
ini_set('session.cookie_secure', 1);
ini_set('session.cookie_httponly', 1);
ini_set('session.cookie_samesite', 'Lax');

require_once __DIR__ . '/../auth/config.php';
require_once __DIR__ . '/../auth/check_auth.php';

$user = ensure_authorized();

global $ALLOWED_DISCORD_IDS;
if (!in_array((string)$user['sub'], $ALLOWED_DISCORD_IDS, true)) {
    http_response_code(403);
    echo "<h1>403 Forbidden</h1><p>You are logged in as " . htmlspecialchars($user['username']) . ", but you are not an admin.</p>";
    exit;
}

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Admin — HCR2 Records</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      body { font-family: Arial, sans-serif; background:#f4f4f9; color:#333; padding:20px; }
      h1 { color:#007bff; }
      
      .accordion-container { max-width:900px; margin:0 auto; }
      .accordion-item { background:#fff; margin:12px 0; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.08); overflow:hidden; }
      .accordion-header { background:#f8f9fa; padding:16px 20px; cursor:pointer; display:flex; justify-content:space-between; align-items:center; border:1px solid #e0e0e0; transition:all 0.2s ease; user-select:none; }
      .accordion-header:hover { background:#f0f1f3; }
      .accordion-header.active { background:#007bff; color:#fff; border-color:#007bff; }
      .accordion-header h2 { margin:0; font-size:18px; flex-grow:1; }
      .accordion-toggle { font-size:20px; transition:transform 0.2s ease; }
      .accordion-header.active .accordion-toggle { transform:rotate(180deg); }
      .accordion-content { display:none; padding:20px; border-top:1px solid #e0e0e0; }
      .accordion-content.active { display:block; }
      
      .form-container { background:transparent; padding:0; border-radius:0; max-width:none; margin:0; box-shadow:none; }
      .form-container h2 { display:none; }
      
      input, select, button { width:100%; padding:10px; margin:8px 0; border:1px solid #ccc; border-radius:6px; }
      button { background:#007bff; color:#fff; border:none; cursor:pointer; transition:background 0.2s; }
      button:hover { background:#0056b3; }
      .topbar { display:flex; justify-content:space-between; align-items:center; max-width:900px; margin:0 auto 20px; }
      .topbar a { text-decoration:none; color:#007bff; }
      
      .edit-news-overlay { display:none; position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(0,0,0,0.6); z-index:9999; align-items:center; justify-content:center; }
      .edit-news-overlay.active { display:flex; }
      .edit-news-modal { background:#fff; border-radius:8px; padding:24px; width:90%; max-width:600px; box-shadow:0 4px 20px rgba(0,0,0,0.3); }
      .edit-news-modal h2 { margin-top:0; margin-bottom:16px; color:#007bff; }
      .edit-news-modal label { display:block; margin-top:12px; margin-bottom:4px; font-weight:bold; }
      .edit-news-modal input[type="text"], .edit-news-modal textarea { width:100%; padding:10px; border:1px solid #ccc; border-radius:6px; font-family:Arial,sans-serif; box-sizing:border-box; }
      .edit-news-modal textarea { min-height:200px; resize:vertical; }
      .edit-news-modal-buttons { display:flex; gap:8px; margin-top:20px; justify-content:flex-end; }
      .edit-news-modal-buttons button { width:auto; padding:10px 20px; }
      .edit-news-modal-buttons .cancel-btn { background:#ccc; color:#000; }
      .edit-news-modal-buttons .cancel-btn:hover { background:#bbb; }
      .edit-news-modal-buttons .save-btn { background:#28a745; }
      .edit-news-modal-buttons .save-btn:hover { background:#218838; }
    </style>
</head>
<body>
    <div class="topbar">
        <h1>Admin Panel — Edit/Add/Delete Records</h1>
        <div>
            <span>
                Logged in as
                <?php
                echo htmlspecialchars(
                    $user['username'] ?? $user['sub']
                );
                ?>
            </span>
            &nbsp;|&nbsp;<a href="/logout">Logout</a>
            &nbsp;|&nbsp;<a href="/index.html">Back to Public</a>
        </div>
    </div>

    <div class="accordion-container">
      <!-- Submit Record -->
      <div class="accordion-item">
        <div class="accordion-header" onclick="toggleAccordion(this)">
          <h2>Submit a New Record ✅</h2>
          <span class="accordion-toggle">▼</span>
        </div>
        <div class="accordion-content">
          <div class="form-container">
            <h2>Submit a New Record ✅</h2>
            <form id="record-form" onsubmit="submitRecord(event)">
            <label>Map</label>
            <select id="map-select" required></select>
            <label>Vehicle</label>
            <select id="vehicle-select" required></select>
            <label>Distance</label>
            <input type="number" id="distance-input" required>
            <label>Tuning Setup (optional)</label>
            <input type="text" id="tuning-setup-filter" placeholder="Filter by part name or use part: prefix (e.g., 'magnet' or 'part:magnet')..." oninput="filterTuningSetups()" style="margin-bottom: 4px;">
            <select id="tuning-setup-select"></select>
            <label>Existing Player</label>
            <input type="text" id="player-filter" placeholder="Filter players..." oninput="filterPlayers()">
            <select id="player-select" onchange="handlePlayerSelection()"><option value="">Select existing player</option></select>
            <label>Or add new player</label>
            <input type="text" id="new-player-input" oninput="newPlayerTyped()">
            <label>Country</label>
            <input type="text" id="country-input">
            <label style="display: flex; align-items: center; gap: 8px;">
                <input type="checkbox" id="questionable-input" style="width: auto;">
                Mark as Questionable (TAS or uncertain legitimacy)
            </label>
            <label>Note (optional)</label>
            <textarea id="questionable-reason-submit" placeholder="add any notes for record (shows for everyone)" style="width:100%; padding:10px; border-radius:6px; border:1px solid #ccc; min-height:50px; resize:vertical; font-family:Arial,sans-serif;"></textarea>
            <button type="submit">Submit Record</button>
        </form>
        <p id="form-message"></p>
          </div>
        </div>
      </div>

      <!-- Delete Record -->
      <div class="accordion-item">
        <div class="accordion-header" onclick="toggleAccordion(this)">
          <h2>Delete a Record ❌</h2>
          <span class="accordion-toggle">▼</span>
        </div>
        <div class="accordion-content">
          <div class="form-container">
            <h2>Delete a Record ❌</h2>
            <form id="delete-form" onsubmit="deleteRecord(event)">
            <label>Filter Record</label>
            <input type="text" id="delete-filter" placeholder="Filter by distance, map, vehicle, or player..." oninput="filterDeleteRecords()">
            <label>Record</label>
            <select id="record-select" required><option value="">Select a record</option></select>
            <button type="submit">Delete Record</button>
        </form>
        <p id="delete-message"></p>
          </div>
        </div>
      </div>
      
      <!-- Mark Records as Questionable -->
      <div class="accordion-item">
        <div class="accordion-header" onclick="toggleAccordion(this)">
          <h2>Mark Records as Questionable ❓</h2>
          <span class="accordion-toggle">▼</span>
        </div>
        <div class="accordion-content">
          <div class="form-container">
            <h2>Mark Records as Questionable ❓</h2>
            <form id="questionable-form" onsubmit="markQuestionable(event)">
            <label>Filter Record</label>
            <input type="text" id="questionable-filter-input" placeholder="Filter by distance, map, vehicle, or player..." oninput="filterQuestionableRecords()">
            <label>Record</label>
            <select id="questionable-record-select" required><option value="">Select a record</option></select>
            <label>Status</label>
            <select id="questionable-status-select" required>
                <option value="">Select status</option>
                <option value="0">Mark as Verified ✓</option>
                <option value="1">Mark as Questionable ❓</option>
            </select>
            <label>Note (optional)</label>
            <textarea id="questionable-reason-input" placeholder="add any notes for records" style="width:100%; padding:10px; border-radius:6px; border:1px solid #ccc; min-height:60px; resize:vertical; font-family:Arial,sans-serif;"></textarea>
            <button type="submit">Update Status</button>
        </form>
        <p id="questionable-message"></p>
          </div>
        </div>
      </div>
      
      <!-- Assign Tuning Setup -->
      <div class="accordion-item">
        <div class="accordion-header" onclick="toggleAccordion(this)">
          <h2>Assign Tuning Setup to Existing Record 🔧</h2>
          <span class="accordion-toggle">▼</span>
        </div>
        <div class="accordion-content">
          <div class="form-container">
            <h2>Assign Tuning Setup to Existing Record 🔧</h2>
            <form id="assign-setup-form" onsubmit="assignSetup(event)">
            <label>Filter Record (without tuning setup)</label>
            <input type="text" id="assign-filter" placeholder="Filter by distance, map, vehicle, or player..." oninput="filterAssignRecords()">
            <label>Record (without tuning setup)</label>
            <select id="assign-record-select" required><option value="">Select a record</option></select>
            <label>Tuning Setup</label>
            <input type="text" id="assign-tuning-setup-filter" placeholder="Filter by part name or use part: prefix (e.g., 'magnet' or 'part:magnet')..." oninput="filterAssignTuningSetups()" style="margin-bottom: 4px;">
            <select id="assign-tuning-setup-select" required><option value="">Select a setup</option></select>
            <button type="submit">Assign Setup</button>
        </form>
        <p id="assign-message"></p>
          </div>
        </div>
      </div>

      <!-- Add Vehicle -->
      <div class="accordion-item">
        <div class="accordion-header" onclick="toggleAccordion(this)">
          <h2>Add a Vehicle ➕</h2>
          <span class="accordion-toggle">▼</span>
        </div>
        <div class="accordion-content">
          <div class="form-container">
            <h2>Add a Vehicle ➕</h2>
            <form id="add-vehicle-form" onsubmit="addVehicle(event)" enctype="multipart/form-data">
            <label>Vehicle Name</label>
            <input type="text" id="vehicle-name-input" required placeholder="e.g., Jeep">
            <label>Icon (SVG - optional)</label>
            <input type="file" id="vehicle-icon-input" accept=".svg,image/svg+xml" style="cursor: pointer;">
            <small style="display: block; margin: -6px 0 8px 0; color: #666;">Upload a .svg icon file. Will be saved as: vehicle_name.svg</small>
            <button type="submit">Add Vehicle</button>
        </form>
        <p id="add-vehicle-message"></p>
          </div>
        </div>
      </div>

      <!-- Add Map -->
      <div class="accordion-item">
        <div class="accordion-header" onclick="toggleAccordion(this)">
          <h2>Add a Map ➕</h2>
          <span class="accordion-toggle">▼</span>
        </div>
        <div class="accordion-content">
          <div class="form-container">
            <h2>Add a Map ➕</h2>
            <form id="add-map-form" onsubmit="addMap(event)" enctype="multipart/form-data">
            <label>Map Name</label>
            <input type="text" id="map-name-input" required placeholder="e.g., Forest Trials">
            <label>Icon (SVG - optional)</label>
            <input type="file" id="map-icon-input" accept=".svg,image/svg+xml" style="cursor: pointer;">
            <small style="display: block; margin: -6px 0 8px 0; color: #666;">Upload a .svg icon file. Will be saved as: map_name.svg</small>
            <button type="submit">Add Map</button>
        </form>
        <p id="add-map-message"></p>
          </div>
        </div>
      </div>
      
      <!-- Add Tuning Part -->
      <div class="accordion-item">
        <div class="accordion-header" onclick="toggleAccordion(this)">
          <h2>Add Tuning Part ➕</h2>
          <span class="accordion-toggle">▼</span>
        </div>
        <div class="accordion-content">
          <div class="form-container">
            <h2>Add Tuning Part ➕</h2>
            <form id="add-tuning-part-form" onsubmit="addTuningPart(event)" enctype="multipart/form-data">
            <label>Tuning Part Name</label>
            <input type="text" id="tuning-part-name-input" required placeholder="e.g., Turbo">
            <label>Icon (SVG - optional)</label>
            <input type="file" id="tuning-part-icon-input" accept=".svg,image/svg+xml" style="cursor: pointer;">
            <small style="display: block; margin: -6px 0 8px 0; color: #666;">Upload a .svg icon file. Will be saved as: part_name.svg</small>
            <button type="submit">Add Tuning Part</button>
        </form>
        <p id="add-tuning-part-message"></p>
          </div>
        </div>
      </div>

      <!-- Add Tuning Setup -->
      <div class="accordion-item">
        <div class="accordion-header" onclick="toggleAccordion(this)">
          <h2>Add Tuning Setup ➕</h2>
          <span class="accordion-toggle">▼</span>
        </div>
        <div class="accordion-content">
          <div class="form-container">
            <h2>Add Tuning Setup ➕</h2>
            <form id="add-tuning-setup-form" onsubmit="addTuningSetup(event)">
            <label>Select Tuning Parts (3-4)</label>
            <div id="tuning-parts-checkboxes"></div>
            <button type="submit">Add Tuning Setup</button>
        </form>
        <p id="add-tuning-setup-message"></p>
          </div>
        </div>
      </div>

      <!-- Pending Submissions -->
      <div class="accordion-item" id="pending-submissions-container">
        <div class="accordion-header" onclick="toggleAccordion(this)">
          <h2>Pending Submissions (from users)</h2>
          <span class="accordion-toggle">▼</span>
        </div>
        <div class="accordion-content">
          <div class="form-container">
            <h2>Pending Submissions (from users)</h2>
            <div id="pending-list">Loading...</div>
          </div>
        </div>
      </div>

      <!-- Site News -->
      <div class="accordion-item">
        <div class="accordion-header" onclick="toggleAccordion(this)">
          <h2>Site News (Admins)</h2>
          <span class="accordion-toggle">▼</span>
        </div>
        <div class="accordion-content">
          <div class="form-container">
            <h2>Site News (Admins)</h2>
            <form id="news-form" onsubmit="postNews(event)">
            <label>Title</label>
            <input type="text" id="news-title-input" required>
            <label>Content</label>
            <textarea id="news-content-input" rows="6" style="width:100%; padding:10px; border-radius:6px; border:1px solid #ccc;" required></textarea>
            <div style="display:flex; gap:8px; margin-top:12px;"><button type="submit">Post News</button><button type="button" onclick="loadAdminNews()" style="background:#ccc;color:#000;">Refresh</button></div>
        </form>
        <p id="news-message"></p>
        <h3 style="margin-top:18px;">Recent News</h3>
        <div id="admin-news-list">Loading...</div>
          </div>
        </div>
      </div>

      <!-- Database & Backups -->
      <div class="accordion-item">
        <div class="accordion-header" onclick="toggleAccordion(this)">
          <h2>Database & Backups</h2>
          <span class="accordion-toggle">▼</span>
        </div>
        <div class="accordion-content">
          <div class="form-container">
            <h2>Database & Backups</h2>
            <div style="display:flex; gap:8px; flex-wrap:wrap;">
            <a href="/auth/admin_actions.php?action=download_db" style="display:inline-block; padding:10px 14px; background:#007bff; color:#fff; border-radius:6px; text-decoration:none;">Download DB</a>
            <button type="button" onclick="createBackup()">Create Backup</button>
            <button type="button" onclick="listBackups()" style="background:#ccc;color:#000;">List Backups</button>
            <button type="button" onclick="runIntegrity()" style="background:#28a745;color:#fff;">Integrity Check</button>
        </div>
        <div id="backups-list" style="margin-top:12px;">Backups will appear here.</div>

        <h3 style="margin-top:12px;">Import SQL</h3>
        <form id="import-form" onsubmit="importSQL(event)" enctype="multipart/form-data">
            <input type="file" name="sqlfile" accept=".sql" required>
            <div style="display:flex; gap:8px; margin-top:8px;"><button type="submit">Import SQL</button></div>
            <p id="import-message"></p>
        </form>
          </div>
        </div>
      </div>

      <!-- Maintenance Mode -->
      <div class="accordion-item" id="maintenance-container">
        <div class="accordion-header" onclick="toggleAccordion(this)">
          <h2>Maintenance Mode</h2>
          <span class="accordion-toggle">▼</span>
        </div>
        <div class="accordion-content">
          <div class="form-container">
        <h2>Maintenance Mode</h2>
        <p id="maintenance-status">Loading...</p>
        <div style="display:flex; gap:8px; flex-wrap:wrap;">
            <button type="button" onclick="setMaintenance('enable')" id="maintenance-enable">Enable</button>
            <button type="button" onclick="setMaintenance('disable')" id="maintenance-disable" style="background:#ccc;color:#000;">Disable</button>
            <button type="button" onclick="refreshMaintenance()" style="background:#f0f0f0;color:#000;">Refresh</button>
        </div>
        <p id="maintenance-message"></p>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit News Modal -->
    <div id="edit-news-overlay" class="edit-news-overlay">
        <div class="edit-news-modal">
            <h2>Edit News</h2>
            <label for="edit-news-title">Title</label>
            <input type="text" id="edit-news-title" placeholder="News title">
            <label for="edit-news-content">Content</label>
            <textarea id="edit-news-content" placeholder="News content"></textarea>
            <div class="edit-news-modal-buttons">
                <button class="cancel-btn" onclick="closeEditNewsModal()">Cancel</button>
                <button class="save-btn" onclick="saveEditedNews()">Save</button>
            </div>
        </div>
    </div>

<script>

function toggleAccordion(header) {
    const isActive = header.classList.contains('active');
    const content = header.nextElementSibling;
    
    if (isActive) {
        header.classList.remove('active');
        content.classList.remove('active');
    } else {
        header.classList.add('active');
        content.classList.add('active');
    }
}


function esc(input) {
    if (input === null || input === undefined) return '';
    return String(input)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

let allPlayers = [];
let allRecords = [];
let allTuningSetups = [];

async function fetchJSON(url) {
    const u = url + (url.indexOf('?') >= 0 ? '&' : '?') + 't=' + Date.now();
    const res = await fetch(u, { credentials: 'same-origin' });
    const text = await res.text();
    if (!res.ok) {
        let message = 'Server error ' + res.status;
        if (text) {
            try {
                const parsed = JSON.parse(text);
                if (parsed && parsed.error) {
                    message += ': ' + parsed.error;
                } else {
                    message += ': ' + text;
                }
            } catch (e) {
                message += ': ' + text;
            }
        }
        throw new Error(message);
    }
    if (!text) {
        throw new Error('Empty JSON response from server');
    }
    try {
        return JSON.parse(text);
    } catch (e) {
        throw new Error('Invalid JSON response: ' + e.message + (text ? ' - ' + text : ''));
    }
}

function populateFormOptions() {
    fetchJSON('/php/load_data.php?type=maps').then(data => {
        const sel = document.getElementById('map-select');
        sel.innerHTML = '<option value="">Select a Map</option>';
        (data || []).forEach(m => sel.appendChild(new Option(m.nameMap, m.idMap)));
    });
    fetchJSON('/php/load_data.php?type=vehicles').then(data => {
        const sel = document.getElementById('vehicle-select');
        sel.innerHTML = '<option value="">Select a Vehicle</option>';
        (data || []).forEach(v => sel.appendChild(new Option(v.nameVehicle, v.idVehicle)));
    });
    fetchJSON('/php/load_data.php?type=players').then(data => {
        allPlayers = data || [];
        const sel = document.getElementById('player-select');
        sel.innerHTML = '<option value="">Select existing player</option>';
        allPlayers.forEach(p => sel.appendChild(new Option(p.namePlayer, p.idPlayer)));
    });
    fetchJSON('/php/load_data.php?type=tuning_setups').then(data => {
        allTuningSetups = data || [];
        const sel = document.getElementById('tuning-setup-select');
        sel.innerHTML = '<option value="">No tuning setup</option>';
        (allTuningSetups || []).forEach(s => {
            const parts = s.parts ? s.parts.map(p => p.nameTuningPart).join(', ') : '';
            sel.appendChild(new Option(`Setup ${s.idTuningSetup}: ${parts}`, s.idTuningSetup));
        });
        document.getElementById('tuning-setup-filter').value = '';
    });
    fetchJSON('/php/load_data.php?type=tuning_parts').then(data => {
        const container = document.getElementById('tuning-parts-checkboxes');
        container.innerHTML = '';
        (data || []).forEach(p => {
            const label = document.createElement('label');
            label.innerHTML = `<input type="checkbox" value="${p.idTuningPart}"> <span>${esc(p.nameTuningPart)}</span>`;
            container.appendChild(label);
        });
    });
    populateDeleteOptions();
    populateAssignSetupOptions();
}

function populateDeleteOptions() {
    fetchJSON('/php/load_data.php?type=records').then(data => {
        allRecords = data || [];
        const sel = document.getElementById('record-select');
        sel.innerHTML = '<option value="">Select a record</option>';
        (allRecords || []).forEach(r => {
            const opt = document.createElement('option');
            opt.value = r.idRecord;
            opt.textContent = `${r.distance} - ${r.map_name} - ${r.vehicle_name} - ${r.player_name}`;
            sel.appendChild(opt);
        });
        document.getElementById('delete-filter').value = '';
        populateQuestionableOptions();
    });
}

function populateQuestionableOptions() {
    const sel = document.getElementById('questionable-record-select');
    sel.innerHTML = '<option value="">Select a record</option>';
    (allRecords || []).forEach(r => {
        const opt = document.createElement('option');
        opt.value = r.idRecord;
        const status = r.questionable === 1 ? '❓' : '✓';
        opt.textContent = `${status} ${r.distance} - ${r.map_name} - ${r.vehicle_name} - ${r.player_name}`;
        sel.appendChild(opt);
    });
    document.getElementById('questionable-filter-input').value = '';
}

function filterPlayers() {
    const q = document.getElementById('player-filter').value.toLowerCase();
    const sel = document.getElementById('player-select');
    sel.innerHTML = '<option value="">Select existing player</option>';
    allPlayers.filter(p => p.namePlayer.toLowerCase().includes(q)).forEach(p => sel.appendChild(new Option(p.namePlayer, p.idPlayer)));
}

function filterDeleteRecords() {
    const q = document.getElementById('delete-filter').value.toLowerCase();
    const sel = document.getElementById('record-select');
    sel.innerHTML = '<option value="">Select a record</option>';
    (allRecords || []).filter(r => {
        const text = `${r.distance} ${r.map_name} ${r.vehicle_name} ${r.player_name}`.toLowerCase();
        return text.includes(q);
    }).forEach(r => {
        const opt = document.createElement('option');
        opt.value = r.idRecord;
        opt.textContent = `${r.distance} - ${r.map_name} - ${r.vehicle_name} - ${r.player_name}`;
        sel.appendChild(opt);
    });
}

function filterQuestionableRecords() {
    const q = document.getElementById('questionable-filter-input').value.toLowerCase();
    const sel = document.getElementById('questionable-record-select');
    sel.innerHTML = '<option value="">Select a record</option>';
    (allRecords || []).filter(r => {
        const text = `${r.distance} ${r.map_name} ${r.vehicle_name} ${r.player_name}`.toLowerCase();
        return text.includes(q);
    }).forEach(r => {
        const opt = document.createElement('option');
        opt.value = r.idRecord;
        const status = r.questionable === 1 ? '❓' : '✓';
        opt.textContent = `${status} ${r.distance} - ${r.map_name} - ${r.vehicle_name} - ${r.player_name}`;
        sel.appendChild(opt);
    });
}

function filterTuningSetups() {
    const q = document.getElementById('tuning-setup-filter').value.toLowerCase().trim();
    const sel = document.getElementById('tuning-setup-select');
    sel.innerHTML = '<option value="">No tuning setup</option>';
    
    (allTuningSetups || []).filter(s => {
        if (!q) return true;
        const parts = s.parts ? s.parts.map(p => p.nameTuningPart).join(', ').toLowerCase() : '';
        const setupInfo = `setup ${s.idTuningSetup} ${parts}`.toLowerCase();
        
        // Support "part:turbo" syntax
        if (q.startsWith('part:')) {
            const partQuery = q.substring(5);
            return parts.includes(partQuery);
        }
        return setupInfo.includes(q);
    }).forEach(s => {
        const parts = s.parts ? s.parts.map(p => p.nameTuningPart).join(', ') : '';
        sel.appendChild(new Option(`Setup ${s.idTuningSetup}: ${parts}`, s.idTuningSetup));
    });
}

function filterAssignTuningSetups() {
    const q = document.getElementById('assign-tuning-setup-filter').value.toLowerCase().trim();
    const sel = document.getElementById('assign-tuning-setup-select');
    sel.innerHTML = '<option value="">Select a setup</option>';
    
    (allTuningSetups || []).filter(s => {
        if (!q) return true;
        const parts = s.parts ? s.parts.map(p => p.nameTuningPart).join(', ').toLowerCase() : '';
        const setupInfo = `setup ${s.idTuningSetup} ${parts}`.toLowerCase();
        
        if (q.startsWith('part:')) {
            const partQuery = q.substring(5);
            return parts.includes(partQuery);
        }
        return setupInfo.includes(q);
    }).forEach(s => {
        const parts = s.parts ? s.parts.map(p => p.nameTuningPart).join(', ') : '';
        sel.appendChild(new Option(`Setup ${s.idTuningSetup}: ${parts}`, s.idTuningSetup));
    });
}

function handlePlayerSelection() {
    const pid = document.getElementById('player-select').value;
    const countryInput = document.getElementById('country-input');
    const newPlayerInput = document.getElementById('new-player-input');
    if (pid) {
        const p = allPlayers.find(x => String(x.idPlayer) === String(pid));
        countryInput.value = p ? (p.country || '') : '';
        countryInput.disabled = true;
        newPlayerInput.value = '';
    } else {
        countryInput.value = '';
        countryInput.disabled = false;
    }
}

function newPlayerTyped() {
    if (document.getElementById('new-player-input').value.trim() !== '') {
        document.getElementById('player-select').value = '';
        document.getElementById('country-input').disabled = false;
    }
}

function submitRecord(e) {
    e.preventDefault();
    const mapId = document.getElementById('map-select').value;
    const vehicleId = document.getElementById('vehicle-select').value;
    const distance = document.getElementById('distance-input').value;
    const tuningSetupId = document.getElementById('tuning-setup-select').value;
    const playerId = document.getElementById('player-select').value;
    const newPlayerName = document.getElementById('new-player-input').value;
    const country = document.getElementById('country-input').value;
    const questionable = document.getElementById('questionable-input').checked ? 1 : 0;
    const questionableReason = document.getElementById('questionable-reason-submit').value.trim();
    const selectedPlayerOption = document.getElementById('player-select').selectedOptions[0];
    const selectedPlayerName = selectedPlayerOption ? selectedPlayerOption.textContent : '';

    if (!playerId && !newPlayerName) {
        showFormMessage('Please select an existing player or add a new one.', true);
        return;
    }
    if (!playerId && newPlayerName && !country) {
        showFormMessage('Please provide a country for the new player.', true);
        return;
    }

    const hasPlayerId = (playerId !== null && playerId !== undefined && playerId !== '');
    const formData = hasPlayerId ? { mapId, vehicleId, distance, tuningSetupId: tuningSetupId || null, playerId, playerName: selectedPlayerName, questionable, questionableReason: questionableReason || null } : { mapId, vehicleId, distance, tuningSetupId: tuningSetupId || null, playerId: null, newPlayerName, country, questionable, questionableReason: questionableReason || null };

    fetch('/php/submit_record.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify(formData)
    }).then(async resp => {
        const text = await resp.text();
        let data;
        try {
            data = JSON.parse(text);
        } catch (err) {
            console.error('Invalid JSON response from submit_record:', text);
            showFormMessage('Server returned invalid response: ' + text, true);
            return;
        }
        if (!resp.ok) {
            showFormMessage(data.error || 'Server error', true);
            return;
        }
        if (data.success) {
            const msg = `✅ Record submitted! | ${data.playerName || 'Unknown'} | ${data.mapName || 'Unknown'} | ${data.vehicleName || 'Unknown'} | ${data.distance || '?'}m`;
            showFormMessage(msg, false);
            document.getElementById('record-form').reset();
            populateFormOptions();
            populateDeleteOptions();
            setTimeout(() => document.getElementById('form-message').textContent = '', 5000);
        } else {
            showFormMessage(data.error || 'Unknown error', true);
        }
    }).catch(err => {
        console.error('Fetch error when submitting record:', err);
        showFormMessage('Error submitting record: ' + err.message, true);
    });
}

function deleteRecord(e) {
    e.preventDefault();
    const recordId = document.getElementById('record-select').value;
    if (!recordId) {
        showDeleteMessage('Please select a record to delete.', true);
        return;
    }
    fetch('/php/delete_record.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ recordId })
    }).then(async resp => {
        const data = await resp.json().catch(()=>({ error: 'Invalid server response' }));
        if (!resp.ok) {
            showDeleteMessage(data.error || 'Server error', true);
            return;
        }
        if (data.success) {
            showDeleteMessage('Record deleted successfully!', false);
            populateDeleteOptions();
        } else {
            showDeleteMessage(data.error || 'Unknown error', true);
        }
    }).catch(()=> showDeleteMessage('Error deleting record.', true));
}

function markQuestionable(e) {
    e.preventDefault();
    const recordId = document.getElementById('questionable-record-select').value;
    const status = document.getElementById('questionable-status-select').value;
    const reason = document.getElementById('questionable-reason-input').value.trim();
    if (!recordId || status === '') {
        showQuestionableMessage('Please select a record and status.', true);
        return;
    }
    fetch('/php/set_questionable.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ recordId, questionable: parseInt(status), note: reason || null })
    }).then(async resp => {
        const text = await resp.text();
        let data;
        try {
            data = JSON.parse(text);
        } catch (err) {
            console.error('Invalid JSON response from set_questionable:', text);
            showQuestionableMessage('Server returned invalid response: ' + text, true);
            return;
        }
        if (!resp.ok) {
            showQuestionableMessage(data.error || 'Server error', true);
            return;
        }
        if (data.success) {
            const msg = status === '1' ? 'Record marked as questionable ❓' : 'Record marked as verified ✓';
            showQuestionableMessage(msg, false);
            document.getElementById('questionable-form').reset();
            populateDeleteOptions();
            setTimeout(() => document.getElementById('questionable-message').textContent = '', 3000);
        } else {
            showQuestionableMessage(data.error || 'Unknown error', true);
        }
    }).catch(err => {
        console.error('Fetch error when marking questionable:', err);
        showQuestionableMessage('Error updating record: ' + err.message, true);
    });
}

function showQuestionableMessage(msg, isError) {
    const el = document.getElementById('questionable-message');
    el.textContent = msg;
    el.style.color = isError ? 'red' : 'green';
}

function populateAssignSetupOptions() {
    fetchJSON('/php/load_data.php?type=records').then(data => {
        const sel = document.getElementById('assign-record-select');
        sel.innerHTML = '<option value="">Select a record</option>';
        (data || []).filter(r => !r.idTuningSetup).forEach(r => {
            const opt = document.createElement('option');
            opt.value = r.idRecord;
            opt.textContent = `${r.distance} - ${r.map_name} - ${r.vehicle_name} - ${r.player_name}`;
            sel.appendChild(opt);
        });
    });
    if (allTuningSetups.length > 0) {
        const sel = document.getElementById('assign-tuning-setup-select');
        sel.innerHTML = '<option value="">Select a setup</option>';
        (allTuningSetups || []).forEach(s => {
            const parts = s.parts ? s.parts.map(p => p.nameTuningPart).join(', ') : '';
            sel.appendChild(new Option(`Setup ${s.idTuningSetup}: ${parts}`, s.idTuningSetup));
        });
        document.getElementById('assign-tuning-setup-filter').value = '';
    } else {
        fetchJSON('/php/load_data.php?type=tuning_setups').then(data => {
            allTuningSetups = data || [];
            const sel = document.getElementById('assign-tuning-setup-select');
            sel.innerHTML = '<option value="">Select a setup</option>';
            (allTuningSetups || []).forEach(s => {
                const parts = s.parts ? s.parts.map(p => p.nameTuningPart).join(', ') : '';
                sel.appendChild(new Option(`Setup ${s.idTuningSetup}: ${parts}`, s.idTuningSetup));
            });
            document.getElementById('assign-tuning-setup-filter').value = '';
        });
    }
}
    
function showFormMessage(msg, isError) {
    const el = document.getElementById('form-message');
    el.textContent = msg;
    el.style.color = isError ? 'red' : 'green';
}
function showDeleteMessage(msg, isError) {
    const el = document.getElementById('delete-message');
    el.textContent = msg;
    el.style.color = isError ? 'red' : 'green';
}

function filterAssignRecords() {
    const q = document.getElementById('assign-filter').value.toLowerCase();
    const sel = document.getElementById('assign-record-select');
    sel.innerHTML = '<option value="">Select a record</option>';
    fetchJSON('/php/load_data.php?type=records').then(data => {
        (data || []).filter(r => !r.idTuningSetup).filter(r => {
            const text = `${r.distance} ${r.map_name} ${r.vehicle_name} ${r.player_name}`.toLowerCase();
            return text.includes(q);
        }).forEach(r => {
            const opt = document.createElement('option');
            opt.value = r.idRecord;
            opt.textContent = `${r.distance} - ${r.map_name} - ${r.vehicle_name} - ${r.player_name}`;
            sel.appendChild(opt);
        });
    });
}

function assignSetup(e) {
    e.preventDefault();
    const recordId = document.getElementById('assign-record-select').value;
    const tuningSetupId = document.getElementById('assign-tuning-setup-select').value;
    
    if (!recordId) {
        showAssignMessage('Please select a record.', true);
        return;
    }
    if (!tuningSetupId) {
        showAssignMessage('Please select a tuning setup.', true);
        return;
    }
    
    fetch('/php/assign_setup.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ recordId, tuningSetupId })
    }).then(async resp => {
        const data = await resp.json().catch(()=>({ error: 'Invalid server response' }));
        if (!resp.ok) {
            showAssignMessage(data.error || 'Server error', true);
            return;
        }
        if (data.success) {
            showAssignMessage('Tuning setup assigned successfully!', false);
            populateAssignSetupOptions();
            populateDeleteOptions();
            document.getElementById('assign-setup-form').reset();
            setTimeout(() => document.getElementById('assign-message').textContent = '', 5000);
        } else {
            showAssignMessage(data.error || 'Unknown error', true);
        }
    }).catch(()=> showAssignMessage('Error assigning setup.', true));
}

function addVehicle(e) {
    e.preventDefault();
    const vehicleName = document.getElementById('vehicle-name-input').value.trim();
    if (!vehicleName) {
        showAddVehicleMessage('Please enter a vehicle name.', true);
        return;
    }
    const formData = new FormData();
    formData.append('vehicleName', vehicleName);
    const iconFile = document.getElementById('vehicle-icon-input').files[0];
    if (iconFile) {
        formData.append('icon', iconFile);
    }
    fetch('/php/add_vehicle.php', {
        method: 'POST',
        credentials: 'same-origin',
        body: formData
    }).then(async resp => {
        const data = await resp.json().catch(()=>({ error: 'Invalid server response' }));
        if (!resp.ok) {
            showAddVehicleMessage(data.error || 'Server error', true);
            return;
        }
        if (data.success) {
            showAddVehicleMessage('Vehicle added successfully!' + (data.iconMessage ? ' ' + data.iconMessage : ''), false);
            document.getElementById('add-vehicle-form').reset();
            populateFormOptions();
        } else {
            showAddVehicleMessage(data.error || 'Unknown error', true);
        }
    }).catch(()=> showAddVehicleMessage('Error adding vehicle.', true));
}

function addMap(e) {
    e.preventDefault();
    const mapName = document.getElementById('map-name-input').value.trim();
    if (!mapName) {
        showAddMapMessage('Please enter a map name.', true);
        return;
    }
    const formData = new FormData();
    formData.append('mapName', mapName);
    const iconFile = document.getElementById('map-icon-input').files[0];
    if (iconFile) {
        formData.append('icon', iconFile);
    }
    fetch('/php/add_map.php', {
        method: 'POST',
        credentials: 'same-origin',
        body: formData
    }).then(async resp => {
        const data = await resp.json().catch(()=>({ error: 'Invalid server response' }));
        if (!resp.ok) {
            showAddMapMessage(data.error || 'Server error', true);
            return;
        }
        if (data.success) {
            showAddMapMessage('Map added successfully!' + (data.iconMessage ? ' ' + data.iconMessage : ''), false);
            document.getElementById('add-map-form').reset();
            populateFormOptions();
        } else {
            showAddMapMessage(data.error || 'Unknown error', true);
        }
    }).catch(()=> showAddMapMessage('Error adding map.', true));
}

function showAddVehicleMessage(msg, isError) {
    const el = document.getElementById('add-vehicle-message');
    el.textContent = msg;
    el.style.color = isError ? 'red' : 'green';
}

function showAddMapMessage(msg, isError) {
    const el = document.getElementById('add-map-message');
    el.textContent = msg;
    el.style.color = isError ? 'red' : 'green';
}

function showAssignMessage(msg, isError) {
    const el = document.getElementById('assign-message');
    el.textContent = msg;
    el.style.color = isError ? 'red' : 'green';
}

function addTuningPart(e) {
    e.preventDefault();
    const partName = document.getElementById('tuning-part-name-input').value.trim();
    if (!partName) {
        showAddTuningPartMessage('Please enter a tuning part name.', true);
        return;
    }
    const formData = new FormData();
    formData.append('partName', partName);
    const iconFile = document.getElementById('tuning-part-icon-input').files[0];
    if (iconFile) {
        formData.append('icon', iconFile);
    }
    fetch('/php/add_tuning_part.php', {
        method: 'POST',
        credentials: 'same-origin',
        body: formData
    }).then(async resp => {
        const data = await resp.json().catch(()=>({ error: 'Invalid server response' }));
        if (!resp.ok) {
            showAddTuningPartMessage(data.error || 'Server error', true);
            return;
        }
        if (data.success) {
            showAddTuningPartMessage('Tuning part added successfully!' + (data.iconMessage ? ' ' + data.iconMessage : ''), false);
            document.getElementById('add-tuning-part-form').reset();
            populateFormOptions();
        } else {
            showAddTuningPartMessage(data.error || 'Unknown error', true);
        }
    }).catch(()=> showAddTuningPartMessage('Error adding tuning part.', true));
}

function addTuningSetup(e) {
    e.preventDefault();
    const checkboxes = document.querySelectorAll('#tuning-parts-checkboxes input[type="checkbox"]:checked');
    const partIds = Array.from(checkboxes).map(cb => parseInt(cb.value));
    if (partIds.length < 2 || partIds.length > 4) {
        showAddTuningSetupMessage('Please select 2 to 4 tuning parts.', true);
        return;
    }
    fetch('/php/add_tuning_setup.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ partIds })
    }).then(async resp => {
        const data = await resp.json().catch(()=>({ error: 'Invalid server response' }));
        if (!resp.ok) {
            showAddTuningSetupMessage(data.error || 'Server error', true);
            return;
        }
        if (data.success) {
            showAddTuningSetupMessage('Tuning setup added successfully!', false);
            checkboxes.forEach(cb => cb.checked = false);
            populateFormOptions();
        } else {
            showAddTuningSetupMessage(data.error || 'Unknown error', true);
        }
    }).catch(()=> showAddTuningSetupMessage('Error adding tuning setup.', true));
}

function showAddTuningPartMessage(msg, isError) {
    const el = document.getElementById('add-tuning-part-message');
    el.textContent = msg;
    el.style.color = isError ? 'red' : 'green';
}

function showAddTuningSetupMessage(msg, isError) {
    const el = document.getElementById('add-tuning-setup-message');
    el.textContent = msg;
    el.style.color = isError ? 'red' : 'green';
}

async function loadPendingSubmissions() {
    const container = document.getElementById('pending-list');
    if (!container) return;
    container.textContent = 'Loading...';
    try {
        const res = await fetch('/auth/admin_pending.php', { credentials: 'same-origin' });
        const data = await res.json();
        if (data.error) {
            container.textContent = 'Error: ' + data.error;
            return;
        }
        const pending = data.pending || [];
        if (pending.length === 0) {
            container.textContent = 'No pending submissions.';
            return;
        }
        let html = '<table class="admin-pending-table"><thead><tr><th>ID</th><th>Map</th><th>Vehicle</th><th>Distance</th><th>Player</th><th>Country</th><th>Tuning Parts</th><th>When</th><th>Actions</th></tr></thead><tbody>';
        pending.forEach(p => {
            const mapLabel = p.mapName ? p.mapName : p.idMap;
            const vehicleLabel = p.vehicleName ? p.vehicleName : p.idVehicle;
            const tuning = p.tuningParts ? esc(p.tuningParts) : '';
            html += `<tr><td data-label="ID">${p.id}</td><td data-label="Map">${mapLabel}</td><td data-label="Vehicle">${vehicleLabel}</td><td data-label="Distance">${p.distance}</td><td data-label="Player">${p.playerName}</td><td data-label="Country">${p.playerCountry}</td><td data-label="Tuning Parts">${tuning}</td><td data-label="When">${p.submitted_at}</td><td data-label="Actions"><button onclick="approveSubmission(${p.id})">Approve</button> <button onclick="rejectSubmission(${p.id})" style="background:#ccc;color:#000;">Reject</button></td></tr>`;
        });
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (err) {
        console.error('Failed to load pending submissions', err);
        container.textContent = 'Failed to load pending submissions.';
    }
}

async function approveSubmission(id) {
    if (!confirm('Approve submission #' + id + '? This will replace the existing record for the same map/vehicle.')) return;
    try {
        const res = await fetch('/auth/admin_pending.php', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action: 'approve', id }) });
        const data = await res.json();
        if (data.success) {
            loadPendingSubmissions();
            populateDeleteOptions();
            populateFormOptions();
            alert('Submission approved.');
        } else {
            alert('Error: ' + (data.error || 'Unknown'));
        }
    } catch (err) {
        console.error(err);
        alert('Request failed');
    }
}

async function rejectSubmission(id) {
    if (!confirm('Reject submission #' + id + '?')) return;
    try {
        const res = await fetch('/auth/admin_pending.php', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action: 'reject', id }) });
        const data = await res.json();
        if (data.success) {
            loadPendingSubmissions();
            alert('Submission rejected.');
        } else {
            alert('Error: ' + (data.error || 'Unknown'));
        }
    } catch (err) {
        console.error(err);
        alert('Request failed');
    }
}

window.onload = () => {
    populateFormOptions();
    loadPendingSubmissions();
    loadAdminNews();
    listBackups();
    refreshMaintenance();
    
    document.getElementById('edit-news-overlay').addEventListener('click', (e) => {
        if (e.target.id === 'edit-news-overlay') {
            closeEditNewsModal();
        }
    });
};

async function postNews(e) {
    e.preventDefault();
    const title = document.getElementById('news-title-input').value.trim();
    const content = document.getElementById('news-content-input').value.trim();
    const msgEl = document.getElementById('news-message');
    if (!title || !content) {
        if (msgEl) { msgEl.textContent = 'Please provide both title and content.'; msgEl.style.color = 'red'; }
        return;
    }
    try {
        const res = await fetch('/auth/post_news.php', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title, content }) });
        const data = await res.json();
        if (!res.ok) {
            if (msgEl) { msgEl.textContent = data.error || 'Posting failed'; msgEl.style.color = 'red'; }
            return;
        }
        if (data.success) {
            if (msgEl) { msgEl.textContent = 'News posted.'; msgEl.style.color = 'green'; }
            document.getElementById('news-form').reset();
            loadAdminNews();
            setTimeout(()=>{ msgEl.textContent = ''; }, 3000);
        } else {
            if (msgEl) { msgEl.textContent = data.error || 'Unknown error'; msgEl.style.color = 'red'; }
        }
    } catch (err) {
        console.error('Post news failed', err);
        if (msgEl) { msgEl.textContent = 'Network error posting news.'; msgEl.style.color = 'red'; }
    }
}

function getRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const secondsAgo = Math.floor((now - date) / 1000);
    
    if (secondsAgo < 60) return 'just now';
    const minutesAgo = Math.floor(secondsAgo / 60);
    if (minutesAgo < 60) return minutesAgo + ' min ago';
    const hoursAgo = Math.floor(minutesAgo / 60);
    if (hoursAgo < 24) return hoursAgo + ' hour' + (hoursAgo !== 1 ? 's' : '') + ' ago';
    const daysAgo = Math.floor(hoursAgo / 24);
    if (daysAgo === 1) return 'yesterday';
    if (daysAgo < 7) return daysAgo + ' days ago';
    if (daysAgo < 30) {
        const weeksAgo = Math.floor(daysAgo / 7);
        return weeksAgo + ' week' + (weeksAgo !== 1 ? 's' : '') + ' ago';
    }
    const monthsAgo = Math.floor(daysAgo / 30);
    if (monthsAgo < 12) return monthsAgo + ' month' + (monthsAgo !== 1 ? 's' : '') + ' ago';
    const yearsAgo = Math.floor(monthsAgo / 12);
    return yearsAgo + ' year' + (yearsAgo !== 1 ? 's' : '') + ' ago';
}

function formatNewsDate(dateString) {
    const date = new Date(dateString);
    const time = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    const relative = getRelativeTime(dateString);
    return `${relative} (${time})`;
}

async function editNewsItem(id) {
    try {
        const res = await fetch('/php/get_news.php?limit=100', { credentials: 'same-origin' });
        const data = await res.json();
        const newsItem = data.news.find(n => n.id === id);
        if (!newsItem) {
            alert('News item not found.');
            return;
        }
        
        document.getElementById('edit-news-title').value = newsItem.title;
        document.getElementById('edit-news-content').value = newsItem.content;
        window.currentEditingNewsId = id;
        
        document.getElementById('edit-news-overlay').classList.add('active');
        document.getElementById('edit-news-title').focus();
    } catch (err) {
        console.error('Failed to load news item', err);
        alert('Failed to load news item.');
    }
}

function closeEditNewsModal() {
    document.getElementById('edit-news-overlay').classList.remove('active');
    window.currentEditingNewsId = null;
    document.getElementById('edit-news-title').value = '';
    document.getElementById('edit-news-content').value = '';
}

async function saveEditedNews() {
    const id = window.currentEditingNewsId;
    if (!id) {
        alert('No news item selected.');
        return;
    }
    
    const title = document.getElementById('edit-news-title').value.trim();
    const content = document.getElementById('edit-news-content').value.trim();
    
    if (!title || !content) {
        alert('Title and content cannot be empty.');
        return;
    }
    
    try {
        const res = await fetch('/auth/edit_news.php', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id, title, content })
        });
        const data = await res.json();
        if (!res.ok) {
            alert('Save failed: ' + (data.error || 'Unknown error'));
            return;
        }
        if (data.success) {
            closeEditNewsModal();
            loadAdminNews();
        }
    } catch (err) {
        console.error('Save news failed', err);
        alert('Network error saving news.');
    }
}

async function deleteNewsItem(id) {
    if (!confirm('Are you sure you want to delete this news item?')) return;
    try {
        const res = await fetch('/auth/delete_news.php', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id })
        });
        const data = await res.json();
        if (!res.ok) {
            alert('Delete failed: ' + (data.error || 'Unknown error'));
            return;
        }
        if (data.success) {
            loadAdminNews();
        }
    } catch (err) {
        console.error('Delete news failed', err);
        alert('Network error deleting news.');
    }
}

async function loadAdminNews() {
    const el = document.getElementById('admin-news-list');
    if (!el) return;
    el.textContent = 'Loading...';
    try {
        const res = await fetch('/php/get_news.php?limit=20', { credentials: 'same-origin' });
        const data = await res.json();
        if (data.error) { el.textContent = 'Error: ' + data.error; return; }
        const items = Array.isArray(data.news) ? data.news : [];
        if (items.length === 0) { el.textContent = 'No news yet.'; return; }
        let html = '<ul style="list-style:none;padding:0;margin:0;">';
        items.forEach(n => {
            const dateFormatted = formatNewsDate(n.created_at);
            html += `<li style="padding:12px;border-bottom:1px solid #eee;display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
                <div style="flex-grow:1;">
                    <strong style="font-size:15px;">${esc(n.title)}</strong>
                    <div style="font-size:12px;color:#888;margin:6px 0;">${dateFormatted} — ${esc(n.author||'')}</div>
                    <div style="white-space:pre-wrap;font-size:14px;margin-top:6px;">${esc(n.content)}</div>
                </div>
                <div style="display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end;">
                    <button onclick="editNewsItem(${n.id})" style="background:#28a745;color:#fff;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;font-size:12px;">Edit</button>
                    <button onclick="deleteNewsItem(${n.id})" style="background:#dc3545;color:#fff;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;font-size:12px;">Delete</button>
                </div>
            </li>`;
        });
        html += '</ul>';
        el.innerHTML = html;
    } catch (err) {
        console.error('Load admin news failed', err);
        el.textContent = 'Failed to load news.';
    }
}

async function createBackup() {
    try {
        const res = await fetch('/auth/admin_actions.php', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams({ action: 'create_backup' }) });
        const data = await res.json();
        if (data.success) {
            alert('Backup created: ' + data.filename);
            listBackups();
        } else {
            alert('Failed to create backup: ' + (data.error || 'unknown'));
        }
    } catch (err) { console.error(err); alert('Request failed'); }
}

async function listBackups() {
    const el = document.getElementById('backups-list');
    if (!el) return;
    el.textContent = 'Loading...';
    try {
        const res = await fetch('/auth/admin_actions.php', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams({ action: 'list_backups' }) });
        const data = await res.json();
        const list = Array.isArray(data.backups) ? data.backups : [];
        if (list.length === 0) { el.textContent = 'No backups found.'; return; }
        let html = '<table style="width:100%; border-collapse: collapse;"><tr><th>Name</th><th>Size</th><th>Modified</th><th>Actions</th></tr>';
        list.forEach(b => {
            html += `<tr style="border-top:1px solid #eee;"><td>${b.name}</td><td>${b.size}</td><td>${b.mtime}</td><td><button onclick="restoreBackup('${b.name}')">Restore</button> <button onclick="deleteBackup('${b.name}')" style="background:#ccc;color:#000;">Delete</button></td></tr>`;
        });
        html += '</table>';
        el.innerHTML = html;
    } catch (err) { console.error(err); el.textContent = 'Failed to load backups.'; }
}

async function deleteBackup(name) {
    if (!confirm('Delete backup ' + name + '?')) return;
    try {
        const res = await fetch('/auth/admin_actions.php', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams({ action: 'delete', filename: name }) });
        const data = await res.json();
        if (data.success) { listBackups(); } else { alert('Delete failed: ' + (data.error||'unknown')); }
    } catch (err) { console.error(err); alert('Request failed'); }
}

async function restoreBackup(name) {
    if (!confirm('Restore backup ' + name + '? This will replace the current DB.')) return;
    try {
        const res = await fetch('/auth/admin_actions.php', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams({ action: 'restore', filename: name }) });
        const data = await res.json();
        if (data.success) { alert('Restored.'); listBackups(); } else { alert('Restore failed: ' + (data.error||'unknown')); }
    } catch (err) { console.error(err); alert('Request failed'); }
}

async function importSQL(e) {
    e.preventDefault();
    const msgEl = document.getElementById('import-message');
    msgEl.textContent = 'Uploading...';
    const form = document.getElementById('import-form');
    const fd = new FormData(form);
    fd.append('action', 'import');
    try {
        const res = await fetch('/auth/admin_actions.php', { method: 'POST', credentials: 'same-origin', body: fd });
        const data = await res.json();
        if (data.success) { msgEl.textContent = 'Import successful.'; listBackups(); } else { msgEl.textContent = 'Import failed: ' + (data.error||'unknown'); }
    } catch (err) { console.error(err); msgEl.textContent = 'Request failed.'; }
}

async function runIntegrity() {
    try {
        const res = await fetch('/auth/admin_actions.php', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams({ action: 'integrity' }) });
        const data = await res.json();
        alert('Integrity check result: ' + (data.result || JSON.stringify(data)));
    } catch (err) { console.error(err); alert('Request failed'); }
}

async function refreshMaintenance() {
    try {
        const res = await fetch('/php/maintenance_status.php', { cache: 'no-cache', credentials: 'same-origin' });
        const j = await res.json();
        const st = document.getElementById('maintenance-status');
        if (st) st.textContent = j.maintenance ? 'MAINTENANCE: ON (admins only)' : 'MAINTENANCE: OFF';
        const msg = document.getElementById('maintenance-message'); if (msg) msg.textContent = '';
    } catch (e) { console.error(e); }
}

async function setMaintenance(action) {
    try {
        const res = await fetch('/php/set_maintenance.php', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action }) });
        const j = await res.json();
        const msg = document.getElementById('maintenance-message');
        if (j.success) {
            if (msg) { msg.style.color = 'green'; msg.textContent = 'Maintenance updated.'; }
            refreshMaintenance();
        } else {
            if (msg) { msg.style.color = 'red'; msg.textContent = j.error || 'Failed to update.'; }
        }
    } catch (e) { console.error(e); const msg = document.getElementById('maintenance-message'); if (msg) { msg.style.color='red'; msg.textContent='Request failed'; } }
}
</script>
</body>
</html>