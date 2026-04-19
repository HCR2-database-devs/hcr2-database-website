let allData = []; 
let currentDataType = ''; 
let allPlayers = []; 

window._dataCache = window._dataCache || {};
function cachedFetchJson(url, ttl = 60000) {
    const key = url;
    const now = Date.now();
    const existing = window._dataCache[key];
    if (existing && (now - existing.ts) < ttl) {
        return Promise.resolve(existing.value);
    }
    return fetch(url, { cache: 'no-store' }).then(response => {
        return response.text().then(text => {
            if (!response.ok) {
                let message = 'Server error ' + response.status;
                if (text) {
                    try {
                        const parsed = JSON.parse(text);
                        if (parsed && parsed.error) {
                            message += ': ' + parsed.error;
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
                const json = JSON.parse(text);
                window._dataCache[key] = { ts: Date.now(), value: json };
                return json;
            } catch (e) {
                throw new Error('Invalid JSON response: ' + e.message + (text ? ' - ' + text : ''));
            }
        });
    });
}

function showElementWithFade(el) {
    if (!el) return;
    el.style.display = 'block';
    el.style.willChange = 'opacity, transform';
    el.style.opacity = 0;
    el.style.transform = 'translateY(6px)';
    requestAnimationFrame(() => {
        el.style.transition = 'opacity 260ms ease, transform 260ms ease';
        el.style.opacity = 1;
        el.style.transform = 'translateY(0)';
    });
}

function hideElementWithFade(el) {
    if (!el) return;
    el.style.willChange = 'opacity, transform';
    el.style.transition = 'opacity 200ms ease, transform 200ms ease';
    el.style.opacity = 0;
    el.style.transform = 'translateY(6px)';
    setTimeout(() => {
        if (el) el.style.display = 'none';
    }, 220);
}

(function ensureDarkTogglePlacement() {
    try {
        const btn = document.getElementById('dark-mode-toggle');
        const menu = document.getElementById('mobile-menu');
        if (btn && menu && menu.contains(btn)) {
            menu.parentNode.insertBefore(btn, menu.nextSibling);
            try { btn.style.pointerEvents = 'auto'; } catch(e){}
            console.log('Early-moved #dark-mode-toggle out of #mobile-menu');
        }
    } catch (e) {
    }
})();

function initDarkMode() {
    const savedMode = localStorage.getItem('darkMode');
    if (savedMode === 'true') {
        document.documentElement.setAttribute('data-theme', 'dark');
        updateDarkModeButton(true);
    }
}

function toggleDarkMode() {
    try {
        console.log('toggleDarkMode invoked');
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        if (isDark) {
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('darkMode', 'false');
            updateDarkModeButton(false);
            console.log('dark mode disabled');
        } else {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('darkMode', 'true');
            updateDarkModeButton(true);
            console.log('dark mode enabled');
        }
    } catch (e) {
        console.error('toggleDarkMode error', e);
    }
}

const darkModeBtn = document.getElementById("dark-mode-toggle");
if (darkModeBtn) {
    darkModeBtn.addEventListener("click", toggleDarkMode);
    try { darkModeBtn.style.pointerEvents = 'auto'; } catch(e){}
    console.log('darkModeBtn bound directly');
} else {
    console.log('darkModeBtn not found at bind time');
}

function updateDarkModeButton(isDark) {
    const btn = document.getElementById('dark-mode-toggle');
    if (btn) {
        btn.textContent = isDark ? '☀️' : '🌙';
    }
}

document.addEventListener('DOMContentLoaded', initDarkMode);

document.addEventListener('DOMContentLoaded', function() {
    try {
        const btn = document.getElementById('dark-mode-toggle');
        const menu = document.getElementById('mobile-menu');
        if (btn && menu && menu.contains(btn)) {
            menu.parentNode.insertBefore(btn, menu.nextSibling);
            try { btn.style.pointerEvents = 'auto'; } catch(e){}
            console.log('Moved #dark-mode-toggle out of #mobile-menu to avoid aria-hidden issues');
        }
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        updateDarkModeButton(isDark);
        try {
            btn.removeEventListener && btn.removeEventListener('click', toggleDarkMode);
            btn.addEventListener && btn.addEventListener('click', toggleDarkMode);
            console.log('darkModeBtn rebound on DOMContentLoaded');
        } catch(e) {}
    } catch (e) { console.error('Failed to relocate dark-mode button', e); }
});

function updateNewsIndicator() {
    const newsBtn = document.getElementById('news-btn-container');
    if (!newsBtn) return;
    
    const unreadNews = localStorage.getItem('unreadNews');
    let indicator = newsBtn.querySelector('.news-indicator');
    
    if (unreadNews === 'true') {
        if (!indicator) {
            indicator = document.createElement('span');
            indicator.className = 'news-indicator';
            newsBtn.appendChild(indicator);
        }
        indicator.style.display = 'block';
    } else {
        if (indicator) {
            indicator.style.display = 'none';
        }
    }
}

function markNewsAsRead() {
    localStorage.setItem('unreadNews', 'false');
    updateNewsIndicator();
}

document.addEventListener('DOMContentLoaded', updateNewsIndicator);

function lazyLoadImages() {
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

document.addEventListener('DOMContentLoaded', lazyLoadImages);

function esc(input) {
    if (input === null || input === undefined) return '';
    return String(input)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function getCountryCode(country) {
    if (!country) return null;
    const c = String(country).trim();
    if (c.length === 2 && /^[A-Za-z]{2}$/.test(c)) return c.toLowerCase();
    const norm = c.toLowerCase();
    const map = {
        'finland': 'fi', 'sweden': 'se', 'norway': 'no', 'denmark': 'dk', 'germany': 'de', 'france': 'fr',
        'spain': 'es', 'italy': 'it', 'netherlands': 'nl', 'poland': 'pl', 'russia': 'ru', 'brazil': 'br',
        'united states': 'us', 'united states of america': 'us', 'usa': 'us', 'canada': 'ca', 'australia': 'au',
        'japan': 'jp', 'china': 'cn', 'south korea': 'kr', 'korea': 'kr', 'united kingdom': 'gb', 'uk': 'gb',
        'ireland': 'ie', 'portugal': 'pt', 'belgium': 'be', 'switzerland': 'ch', 'austria': 'at', 'czechia': 'cz',
        'slovakia': 'sk', 'hungary': 'hu', 'romania': 'ro', 'bulgaria': 'bg', 'india': 'in', 'mexico': 'mx',
        'argentina': 'ar', 'chile': 'cl', 'colombia': 'co', 'south africa': 'za', 'new zealand': 'nz',
        'greece': 'gr', 'turkey': 'tr', 'egypt': 'eg', 'uae': 'ae', 'united arab emirates': 'ae',
        'saudi arabia': 'sa', 'israel': 'il', 'philippines': 'ph', 'singapore': 'sg', 'malaysia': 'my',
        'thailand': 'th', 'vietnam': 'vn', 'indonesia': 'id', 'pakistan': 'pk', 'bangladesh': 'bd',
        'libya': 'ly', 'tunisia': 'tn', 'morocco': 'ma', 'algeria': 'dz', 'venezuela': 've',
        'peru': 'pe', 'ecuador': 'ec', 'panama': 'pa', 'costa rica': 'cr', 'dominican republic': 'do',
        'croatia': 'hr', 'serbia': 'rs', 'slovenia': 'si', 'latvia': 'lv', 'lithuania': 'lt', 'estonia': 'ee',
        'iceland': 'is', 'luxembourg': 'lu', 'monaco': 'mc', 'andorra': 'ad', 'liechtenstein': 'li',
        'ukraine': 'ua', 'belarus': 'by', 'kazakhstan': 'kz', 'georgia': 'ge', 'armenia': 'am', 'azerbaijan': 'az',
        'cyprus': 'cy', 'malta': 'mt', 'haiti': 'ht', 'jamaica': 'jm', 'trinidad and tobago': 'tt',
        'turkiye': 'tr', 'taiwan': 'tw', 'hong kong': 'hk', 'macau': 'mo', 'sri lanka': 'lk', 'nepal': 'np',
        'bosnia and herzegovina': 'ba', 'north macedonia': 'mk', 'montenegro': 'me', 'kosovo': 'xk',
        'uzbekistan': 'uz', 'kyrgyzstan': 'kg', 'tajikistan': 'tj', 'afghanistan': 'af', 'iran': 'ir',
        'iraq': 'iq', 'syria': 'sy', 'lebanon': 'lb', 'jordan': 'jo', 'qatar': 'qa', 'bahrain': 'bh',
        'kuwait': 'kw', 'oman': 'om', 'yemen': 'ye', 'cuba': 'cu', 'guatemala': 'gt', 'el salvador': 'sv',
        'honduras': 'hn', 'nicaragua': 'ni', 'bolivia': 'bo', 'paraguay': 'py', 'uruguay': 'uy',
        'albania': 'al', 'morocco': 'ma', 'senegal': 'sn', 'ghana': 'gh', 'kenya': 'ke', 'uganda': 'ug',
        'tanzania': 'tz', 'zambia': 'zm', 'zimbabwe': 'zw', 'namibia': 'na', 'botswana': 'bw', 'mozambique': 'mz',
        'other countries': 'question'
    };
    if (map[norm]) return map[norm];
    const last = norm.split(/[,\s]+/).pop();
    if (map[last]) return map[last];
    return null;
}

function renderTuningParts(partsString) {
    if (!partsString || typeof partsString !== 'string' || partsString.trim() === '') return '';
    const parts = partsString.split(',').map(p => p.trim()).filter(p => p);
    return parts.map(part => {
        const iconName = part.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_-]/g, '');
        const svgSrc = `/img/tuning_parts_icons/${iconName}.svg`;
        const pngSrc = `/img/tuning_parts_icons/${iconName}.png`;
               return `<img class="tuning-part-icon" src="${svgSrc}" alt="${esc(part)} icon" title="${esc(part)}" onerror="this.onerror=null; this.src='${pngSrc}'; if(!this.complete) this.style.display='none';">`;
    }).join(' ');
}

function renderTuningPartWithIcon(partName) {
    if (!partName || typeof partName !== 'string') return esc(partName || 'Unknown');
    const name = String(partName).trim().replace(/,/g, '');
    const iconName = name.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_-]/g, '');
    const svgSrc = `/img/tuning_parts_icons/${iconName}.svg`;
    const pngSrc = `/img/tuning_parts_icons/${iconName}.png`;
           return `<span class="tuning-part-cell"><img class="tuning-part-icon" src="${svgSrc}" alt="${esc(name)} icon" title="${esc(name)}" onerror="this.onerror=null; this.src='${pngSrc}'; if(!this.complete) this.style.display='none';"> ${esc(name)}</span>`;
}

function renderCountryWithFlag(country) {
    const code = getCountryCode(country);
    const name = country || '';
    if (String(name).trim().toLowerCase() === 'other countries') {
        return esc(name);
    }
    if (code) {
        const src = `https://flagcdn.com/24x18/${code}.png`;
               return `<span class="country-cell"><img class="country-flag" src="${src}" alt="${esc(name)} flag"> ${esc(name)}</span>`;
    }
    return esc(name || 'Unknown');
}

function renderMapWithIcon(mapName) {
    if (!mapName) return esc(mapName || 'Unknown');
    const name = String(mapName).trim();
    const iconName = name.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_-]/g, '');
    const svgSrc = `/img/map_icons/${iconName}.svg`;
    const pngSrc = `/img/map_icons/${iconName}.png`;
           return `<span class="map-cell"><img class="map-icon" src="${svgSrc}" alt="${esc(name)} icon" onerror="this.src='${pngSrc}'; this.onerror=null; if(!this.complete) this.style.display='none';"> ${esc(name)}</span>`;
}

function renderVehicleWithIcon(vehicleName) {
    if (!vehicleName) return esc(vehicleName || 'Unknown');
    const name = String(vehicleName).trim();
    const iconName = name.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_-]/g, '');
    const svgSrc = `/img/vehicle_icons/${iconName}.svg`;
    const pngSrc = `/img/vehicle_icons/${iconName}.png`;
    return `<span class="vehicle-cell"><img class="vehicle-icon" src="${svgSrc}" alt="${esc(name)} icon" onerror="this.src='${pngSrc}'; this.onerror=null; if(!this.complete) this.style.display='none';"> ${esc(name)}</span>`;
}
document.addEventListener('click', function (e) {
    const btn = e.target.closest && e.target.closest('#dark-mode-toggle');
    if (btn) {
        try { toggleDarkMode(); } catch (e) { /* no-op */ }
    }
});
function formatDistance(value, decimals = null) {
    if (value === null || value === undefined || value === '') return '';
    const num = Number(value);
    if (isNaN(num)) return esc(value);
    if (decimals !== null) {
        return esc(num.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals }));
    }
    return esc(Math.round(num).toLocaleString());
}

function fetchWithTimeout(resource, options = {}, timeout = 3000) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    const opts = Object.assign({}, options, { signal: controller.signal });
    return fetch(resource, opts).finally(() => clearTimeout(id));
}

async function fetchAuthStatusWithRetries(retries = 3, initialTimeout = 3000) {
    let timeout = initialTimeout;
    for (let attempt = 0; attempt < retries; attempt++) {
        try {
            const res = await fetchWithTimeout('auth/status.php', { cache: 'no-cache', credentials: 'same-origin' }, timeout);
            return res;
        } catch (err) {
            await new Promise(r => setTimeout(r, 250 * (attempt + 1)));
            timeout = Math.min(10000, Math.floor(timeout * 1.5));
        }
    }
    return null;
}

function fetchStats() {
	if (window.closeMobileMenu) try { window.closeMobileMenu(); } catch (e) {}
    const statsContainer = document.getElementById('stats-container');
    const dataContainer = document.getElementById('data-container');
    const filterContainer = document.getElementById('filter-container');
    if (currentDataType === 'stats' && statsContainer && statsContainer.style.display === 'block') {
        hideElementWithFade(statsContainer);
        currentDataType = '';
        return;
    }
    currentDataType = 'stats';
    if (dataContainer) hideElementWithFade(dataContainer);
    if (filterContainer) hideElementWithFade(filterContainer);
    if (statsContainer) showElementWithFade(statsContainer);

    cachedFetchJson('php/load_data.php?type=records&t=' + Date.now(), 60000)
    .then(data => {
        if (data.error) {
            console.error('Error:', data.error);
            if (statsContainer) statsContainer.innerHTML = '<p style="color:red;">' + data.error + '</p>';
        } else {
            displayStats(data);
        }
    }).catch(error => {
        console.error('Fetch error:', error);
        if (statsContainer) statsContainer.innerHTML = '<p style="color:red;">Error fetching stats data from server.</p>';
    });
}

function displayStats(data) {
const statsContainer = document.getElementById('stats-container');
statsContainer.innerHTML = '<h2>DETAILED STATISTICS</h2>';

window.statsData = data;

let vehicleStatsHTML = '<div class="stats-section">';
vehicleStatsHTML += '<div class="vehicle-header" style="position: relative; display: flex; align-items: center; justify-content: flex-end; margin-bottom: 15px;">';
vehicleStatsHTML += '<h3 class="vehicle-title" style="position: absolute; left: 50%; transform: translateX(-50%); margin: 0;">Vehicle Statistics</h3>';
vehicleStatsHTML += '<div class="vehicle-select-wrap" style="margin-left: auto;">';
vehicleStatsHTML += '<select id="vehicle-sort-select" onchange="updateVehicleStats()" style="padding: 8px 12px; border-radius: 4px; border: 1px solid #ccc; font-size: 14px;">';
vehicleStatsHTML += '<option value="total-distance">Total Distance</option>';
vehicleStatsHTML += '<option value="longest-distance">Longest Distance</option>';
vehicleStatsHTML += '<option value="avg-placement">Average Placement </option>';
vehicleStatsHTML += '<option value="highest-placement">Highest Placement</option>';
vehicleStatsHTML += '<option value="lowest-placement">Lowest Placement</option>';
vehicleStatsHTML += '</select>';
vehicleStatsHTML += '</div>';
vehicleStatsHTML += '</div>';
vehicleStatsHTML += '<div id="vehicle-stats-table"></div>';
vehicleStatsHTML += '</div>';
statsContainer.innerHTML += vehicleStatsHTML;

updateVehicleStats();

const specialMaps = ['Forest Trials', 'Intense City', 'Raging Winter'];
const vehicleStars = {};
data.forEach(record => {
    if (!vehicleStars[record.vehicle_name]) {
        vehicleStars[record.vehicle_name] = 0;
    }
    
    const isSpecialMap = specialMaps.includes(record.map_name);
    let stars = 0;
    
    if (isSpecialMap) {
        stars = record.distance >= 5000 ? 15000 : record.distance * 3;
    } else {
        stars = record.distance >= 10000 ? 10000 : record.distance;
    }
    
    vehicleStars[record.vehicle_name] += stars;
});

const sortedVehiclesByStars = Object.entries(vehicleStars)
    .sort((a, b) => b[1] - a[1]);

let totalStars = 0;
sortedVehiclesByStars.forEach(v => { totalStars += v[1]; });

let starsHTML = '<div class="stats-section"><h3>Vehicle Rankings by Adventure Stars</h3>';
starsHTML += '<div class="chart-container stars-chart">';

const maxStars = Math.max(...sortedVehiclesByStars.map(v => v[1]));
sortedVehiclesByStars.forEach((vehicle, index) => {
    const barWidth = (vehicle[1] / maxStars) * 100;
    const vehicleDisplay = renderVehicleWithIcon(vehicle[0]);
    starsHTML += `
        <div class="chart-bar">
            <span class="player-rank">${index + 1}.</span>
            <span class="player-name">${vehicleDisplay}</span>
            <div class="bar-wrap">
                <div class="bar-fill" style="width: ${barWidth}%; background: linear-gradient(to right, #85a728ff, #28a745);">
                    <span class="bar-value">${formatDistance(vehicle[1])}</span>
                </div>
            </div>
        </div>
    `;
});

starsHTML += `<div class="total-stars"> ⭐ Total Adventure Stars : </div>`;
starsHTML += `<div class="total-stars-value">${formatDistance(totalStars)}</div>`;
starsHTML += '</div></div>';
statsContainer.innerHTML += starsHTML;

try {
    const starFills = statsContainer.querySelectorAll('.stars-chart .bar-fill');
    (starFills || []).forEach((el, i) => {
        const pct = (sortedVehiclesByStars[i] && sortedVehiclesByStars[i][1]) ? (sortedVehiclesByStars[i][1] / maxStars) * 100 : 0;
        el.style.width = pct.toFixed(2) + '%';
    });
} catch (e) {}

const playerRecords = {};
data.forEach(record => {
    playerRecords[record.player_name] = (playerRecords[record.player_name] || 0) + 1;
});

const sortedPlayers = Object.entries(playerRecords)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);

let playersHTML = '<div class="stats-section"><h3>Top 10 Players by Record Count</h3>';
playersHTML += '<div class="chart-container players-chart">';

const maxRecords = Math.max(...sortedPlayers.map(p => p[1]));
sortedPlayers.forEach((player, index) => {
    const barWidth = (player[1] / maxRecords) * 100;
    playersHTML += `
        <div class="chart-bar">
            <span class="player-rank">${index + 1}.</span>
            <span class="player-name">${esc(player[0])}</span>
            <div class="bar-wrap">
                <div class="bar-fill" style="width: ${barWidth}%;">
                    <span class="bar-value">${player[1]}</span>
                </div>
            </div>
        </div>
    `;
});

playersHTML += '</div></div>';
statsContainer.innerHTML += playersHTML;

try {
    const fills = statsContainer.querySelectorAll('.players-chart .bar-fill');
    const max = Math.max(...sortedPlayers.map(p => p[1])) || 1;
    fills.forEach((el, i) => {
        const val = (sortedPlayers[i] && sortedPlayers[i][1]) ? sortedPlayers[i][1] : 0;
        const pct = (val / max) * 100;
        el.style.width = pct.toFixed(2) + '%';
    });
} catch (e) {
}

const countryCounts = {};
data.forEach(record => {
    const c = (record.player_country || record.country || 'Unknown') || 'Unknown';
    countryCounts[c] = (countryCounts[c] || 0) + 1;
});

const grouped = {};
let otherCount = 0;
Object.entries(countryCounts).forEach(([country, count]) => {
    if (count <= 5) {
        otherCount += count;
    } else {
        grouped[country] = count;
    }
});
if (otherCount > 0) grouped['Other countries'] = otherCount;

const countryEntries = Object.entries(grouped).sort((a, b) => b[1] - a[1]);
const countryTotal = countryEntries.reduce((s, e) => s + e[1], 0) || 1;

let pieHTML = '<div class="stats-section"><h3>Records by Country</h3><div class="pie-container">';
pieHTML += '<canvas id="country-pie" width="500" height="375" aria-label="Pie chart showing records by country"></canvas>';
    pieHTML += '<div class="pie-legend">';
countryEntries.forEach((entry, idx) => {
    pieHTML += `<div class="legend-item"><span class="legend-color" data-idx="${idx}"></span><span class="legend-label">${esc(entry[0])} (${entry[1]})</span></div>`;
});
pieHTML += '</div></div></div>';
statsContainer.innerHTML += pieHTML;

setTimeout(function drawPieDelay() {
    const canvas = document.getElementById('country-pie');
    if (!canvas || !canvas.getContext) {
        console.warn('Canvas not found or no 2D context');
        return;
    }
    const ctx = canvas.getContext('2d');
    
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const radius = Math.min(canvas.width, canvas.height) / 2 - 10;

    let startAngle = -0.5 * Math.PI;
    countryEntries.forEach((entry, idx) => {
        const slice = entry[1] / countryTotal * Math.PI * 2;
        const hue = (idx * 137.508) % 360;
        const color = `hsl(${hue},70%,50%)`;
        
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.arc(cx, cy, radius, startAngle, startAngle + slice);
        ctx.closePath();
        ctx.fillStyle = color;
        ctx.fill();

        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.stroke();

        const legendBox = document.querySelector(`.legend-color[data-idx="${idx}"]`);
        if (legendBox) legendBox.style.background = color;

        startAngle += slice;
    });
}, 50);

const mapStats = {};
const mapRecordCount = {};
data.forEach(record => {
    if (!mapStats[record.map_name]) {
        mapStats[record.map_name] = { distance: 0, count: 0 };
    }
    mapStats[record.map_name].distance += record.distance;
    mapStats[record.map_name].count += 1;
});

const sortedMaps = Object.entries(mapStats)
    .sort((a, b) => b[1].distance - a[1].distance);

let mapHTML = '<div class="stats-section"><h3>Map Statistics</h3><table>';
mapHTML += '<tr><th>Map Name</th><th>Total Records</th><th>Total Distance</th><th>Average Distance</th></tr>';
    sortedMaps.forEach(map => {
    const avgDistanceNum = (map[1].distance / map[1].count);
    mapHTML += `<tr><td>${renderMapWithIcon(map[0])}</td><td>${map[1].count}</td><td>${formatDistance(map[1].distance)}</td><td>${formatDistance(avgDistanceNum, 2)}</td></tr>`;
});
mapHTML += '</table></div>';
statsContainer.innerHTML += mapHTML;

const mapStars = {};
data.forEach(record => {
    if (!mapStars[record.map_name]) {
        mapStars[record.map_name] = 0;
    }
    
    const isSpecialMap = specialMaps.includes(record.map_name);
    let stars = 0;
    
    if (isSpecialMap) {
        stars = record.distance >= 5000 ? 15000 : record.distance * 3;
    } else {
        stars = record.distance >= 10000 ? 10000 : record.distance;
    }
    
    mapStars[record.map_name] += stars;
});

const sortedMapsByStars = Object.entries(mapStars)
    .sort((a, b) => b[1] - a[1]);

let totalMapStars = 0;
sortedMapsByStars.forEach(m => { totalMapStars += m[1]; });

let mapStarsHTML = '<div class="stats-section"><h3>Map Rankings by Adventure Stars</h3>';
mapStarsHTML += '<div class="chart-container stars-chart">';

const maxMapStars = Math.max(...sortedMapsByStars.map(m => m[1]));
sortedMapsByStars.forEach((map, index) => {
    const barWidth = (map[1] / maxMapStars) * 100;
    const mapDisplay = renderMapWithIcon(map[0]);
    mapStarsHTML += `
        <div class="chart-bar">
            <span class="player-rank">${index + 1}.</span>
            <span class="player-name">${mapDisplay}</span>
            <div class="bar-wrap">
                <div class="bar-fill" style="width: ${barWidth}%; background: linear-gradient(to right, #4287f5ff, #00d4ff);">
                    <span class="bar-value">${formatDistance(map[1])}</span>
                </div>
            </div>
        </div>
    `;
});

mapStarsHTML += `<div class="total-stars"> ⭐ Total Adventure Stars : </div>`;
mapStarsHTML += `<div class="total-stars-value">${formatDistance(totalMapStars)}</div>`;
mapStarsHTML += '</div></div>';
statsContainer.innerHTML += mapStarsHTML;
    
const tuningPartStats = {};
const tuningSetupStats = {};
data.forEach(record => {
    if (record.tuning_parts && typeof record.tuning_parts === 'string') {
        const parts = record.tuning_parts.split(', ');
        parts.forEach(part => {
            if (!tuningPartStats[part]) {
                tuningPartStats[part] = 0;
            }
            tuningPartStats[part]++;
        });
    }
    if (record.idTuningSetup) {
        const setupKey = `Setup ${record.idTuningSetup}`;
        if (!tuningSetupStats[setupKey]) {
            tuningSetupStats[setupKey] = { count: 0, parts: record.tuning_parts || '' };
        }
        tuningSetupStats[setupKey].count++;
    }
});

let tuningHTML = '<div class="stats-section"><h3>Tuning Part Statistics</h3><div class="tuning-stats">';

const sortedParts = Object.entries(tuningPartStats).sort((a, b) => b[1] - a[1]).slice(0, 10);
if (sortedParts.length > 0) {
    tuningHTML += '<div class="stat-subsection"><h4>Most Used Individual Parts</h4><table>';
    tuningHTML += '<tr><th>Rank</th><th>Part</th><th>Usage Count</th></tr>';
    sortedParts.forEach((part, index) => {
        tuningHTML += `<tr><td>${index + 1}</td><td>${renderTuningPartWithIcon(part[0])}</td><td>${part[1]}</td></tr>`;
    });
    tuningHTML += '</table></div>';
}

const sortedSetups = Object.entries(tuningSetupStats).sort((a, b) => b[1].count - a[1].count).slice(0, 10);
if (sortedSetups.length > 0) {
    tuningHTML += '<div class="stat-subsection"><h4>Most Used Setups</h4><table>';
    tuningHTML += '<tr><th>Rank</th><th>Setup</th><th>Usage Count</th></tr>';
    sortedSetups.forEach((setup, index) => {
        const setupName = setup[0] + (setup[1].parts ? `: ${setup[1].parts}` : '');
        tuningHTML += `<tr><td>${index + 1}</td><td>${setupName}</td><td>${setup[1].count}</td></tr>`;
    });
    tuningHTML += '</table></div>';
}

tuningHTML += '</div></div>';
statsContainer.innerHTML += tuningHTML;

const totalRecords = data.length;
const totalDistance = data.reduce((sum, record) => sum + record.distance, 0);
const avgDistance = (totalDistance / totalRecords).toFixed(2);
const uniquePlayers = new Set(data.map(r => r.player_name)).size;
const uniqueVehicles = new Set(data.map(r => r.vehicle_name)).size;
const uniqueMaps = new Set(data.map(r => r.map_name)).size;

let overallHTML = '<div class="stats-section"><h3>Overall Statistics</h3><div class="overall-stats">';
overallHTML += `<div class="stat-box"><strong>Total Records:</strong> ${esc(totalRecords)}</div>`;
overallHTML += `<div class="stat-box"><strong>Total Distance:</strong> ${formatDistance(totalDistance)}</div>`;
overallHTML += `<div class="stat-box"><strong>Average Distance:</strong> ${formatDistance(avgDistance, 2)}</div>`;
overallHTML += `<div class="stat-box"><strong>Unique Players:</strong> ${esc(uniquePlayers)}</div>`;
overallHTML += `<div class="stat-box"><strong>Unique Vehicles:</strong> ${esc(uniqueVehicles)}</div>`;
overallHTML += `<div class="stat-box"><strong>Unique Maps:</strong> ${esc(uniqueMaps)}</div>`;
overallHTML += '</div></div>';
statsContainer.innerHTML += overallHTML;
}

function updateVehicleStats() {
const data = window.statsData;
const sortType = document.getElementById('vehicle-sort-select').value;
const tableContainer = document.getElementById('vehicle-stats-table');
let html = '<table>';

if (sortType === 'total-distance') {
    
    const vehicleStats = {};
    data.forEach(record => {
        if (!vehicleStats[record.vehicle_name]) {
            vehicleStats[record.vehicle_name] = 0;
        }
        vehicleStats[record.vehicle_name] += record.distance;
    });

    const sortedVehicles = Object.entries(vehicleStats).sort((a, b) => b[1] - a[1]);
    
    html += '<tr><th>Rank</th><th>Vehicle Name</th><th>Total Distance</th></tr>';
    sortedVehicles.forEach((vehicle, index) => {
        html += `<tr><td>${index + 1}</td><td>${renderVehicleWithIcon(vehicle[0])}</td><td>${formatDistance(vehicle[1])}</td></tr>`;
    });

} else if (sortType === 'longest-distance') {
    
    const vehicleLongest = {};
    data.forEach(record => {
        if (!vehicleLongest[record.vehicle_name]) {
            vehicleLongest[record.vehicle_name] = { distance: 0, map: '' };
        }
        if (record.distance > vehicleLongest[record.vehicle_name].distance) {
            vehicleLongest[record.vehicle_name] = { distance: record.distance, map: record.map_name };
        }
    });

    const sortedByLongest = Object.entries(vehicleLongest)
        .sort((a, b) => b[1].distance - a[1].distance);

    html += '<tr><th>Rank</th><th>Vehicle Name</th><th>Longest Distance</th><th>Map</th></tr>';
    sortedByLongest.forEach((vehicle, index) => {
        html += `<tr><td>${index + 1}</td><td>${renderVehicleWithIcon(vehicle[0])}</td><td>${formatDistance(vehicle[1].distance)}</td><td>${renderMapWithIcon(vehicle[1].map)}</td></tr>`;
    });

} else if (sortType === 'avg-placement') {
    
    const vehiclePlacements = {};
    
    
    const mapData = {};
    data.forEach(record => {
        if (!mapData[record.map_name]) {
            mapData[record.map_name] = [];
        }
        mapData[record.map_name].push(record);
    });

    
    Object.keys(mapData).forEach(mapName => {
        const mapRecords = mapData[mapName];
        
        mapRecords.sort((a, b) => b.distance - a.distance);
        
        mapRecords.forEach((record, placement) => {
            if (!vehiclePlacements[record.vehicle_name]) {
                vehiclePlacements[record.vehicle_name] = { placements: [], totalPlacement: 0 };
            }
            vehiclePlacements[record.vehicle_name].placements.push({ map: mapName, placement: placement + 1, distance: record.distance });
            vehiclePlacements[record.vehicle_name].totalPlacement += (placement + 1);
        });
    });

    
    Object.keys(vehiclePlacements).forEach(vehicleName => {
        const data = vehiclePlacements[vehicleName];
        data.avgPlacement = data.totalPlacement / data.placements.length;
    });

    const sortedByAvgPlacement = Object.entries(vehiclePlacements)
        .sort((a, b) => a[1].avgPlacement - b[1].avgPlacement);

    html += '<tr><th>Rank</th><th>Vehicle Name</th><th>Average Placement</th></tr>';
    sortedByAvgPlacement.forEach((vehicle, index) => {
        html += `<tr><td>${index + 1}</td><td>${renderVehicleWithIcon(vehicle[0])}</td><td>${vehicle[1].avgPlacement.toFixed(2)}</td></tr>`;
    });

} else if (sortType === 'highest-placement') {
    
    const vehicleHighest = {};
    
    const mapData = {};
    data.forEach(record => {
        if (!mapData[record.map_name]) {
            mapData[record.map_name] = [];
        }
        mapData[record.map_name].push(record);
    });

    
    Object.keys(mapData).forEach(mapName => {
        const mapRecords = mapData[mapName];
        mapRecords.sort((a, b) => b.distance - a.distance);
        
        mapRecords.forEach((record, placement) => {
            if (!vehicleHighest[record.vehicle_name]) {
                vehicleHighest[record.vehicle_name] = { placement: Infinity, maps: [] };
            }
            const currentPlacement = placement + 1;
            if (currentPlacement < vehicleHighest[record.vehicle_name].placement) {
                vehicleHighest[record.vehicle_name].placement = currentPlacement;
                vehicleHighest[record.vehicle_name].maps = [mapName];
            } else if (currentPlacement === vehicleHighest[record.vehicle_name].placement) {
                vehicleHighest[record.vehicle_name].maps.push(mapName);
            }
        });
    });

    const sortedByHighest = Object.entries(vehicleHighest)
        .filter(v => v[1].placement !== Infinity)
        .sort((a, b) => a[1].placement - b[1].placement);

    html += '<tr><th>Rank</th><th>Vehicle Name</th><th>Best Placement</th><th>Maps</th></tr>';
    sortedByHighest.forEach((vehicle, index) => {
        const mapsStr = vehicle[1].maps.join(', ');
        html += `<tr><td>${index + 1}</td><td>${renderVehicleWithIcon(vehicle[0])}</td><td>#${vehicle[1].placement}</td><td>${mapsStr}</td></tr>`;
    });

} else if (sortType === 'lowest-placement') {
    
    const vehicleLowest = {};
    
    const mapData = {};
    data.forEach(record => {
        if (!mapData[record.map_name]) {
            mapData[record.map_name] = [];
        }
        mapData[record.map_name].push(record);
    });

    
    Object.keys(mapData).forEach(mapName => {
        const mapRecords = mapData[mapName];
        mapRecords.sort((a, b) => b.distance - a.distance);
        
        mapRecords.forEach((record, placement) => {
            if (!vehicleLowest[record.vehicle_name]) {
                vehicleLowest[record.vehicle_name] = { placement: 0, maps: [] };
            }
            const currentPlacement = placement + 1;
            if (currentPlacement > vehicleLowest[record.vehicle_name].placement) {
                vehicleLowest[record.vehicle_name].placement = currentPlacement;
                vehicleLowest[record.vehicle_name].maps = [mapName];
            } else if (currentPlacement === vehicleLowest[record.vehicle_name].placement) {
                vehicleLowest[record.vehicle_name].maps.push(mapName);
            }
        });
    });

    const sortedByLowest = Object.entries(vehicleLowest)
        .sort((a, b) => b[1].placement - a[1].placement);

    html += '<tr><th>Rank</th><th>Vehicle Name</th><th>Worst Placement</th><th>Maps</th></tr>';
    sortedByLowest.forEach((vehicle, index) => {
        const mapsStr = vehicle[1].maps.join(', ');
        html += `<tr><td>${index + 1}</td><td>${renderVehicleWithIcon(vehicle[0])}</td><td>#${vehicle[1].placement}</td><td>${mapsStr}</td></tr>`;
    });
}

html += '</table>';
tableContainer.innerHTML = html;
}

function filterPlayers() {
    const query = document.getElementById('player-filter').value.toLowerCase();
    const select = document.getElementById('player-select');
    select.innerHTML = '<option value="">Select an Existing Player</option>';
    allPlayers
        .filter(p => p.namePlayer.toLowerCase().includes(query))
        .forEach(p => {
            const option = document.createElement('option');
            option.value = p.idPlayer;
            option.textContent = p.namePlayer;
            select.appendChild(option);
        });
    handlePlayerSelection();
}

function downloadCSV(dataArray) {
    const headers = ['Distance','Map Name','Vehicle Name','Player Name','Country'];
    const rows = dataArray.map(r => [
        r.distance,
        r.map_name,
        r.vehicle_name,
        r.player_name,
        r.player_country
    ]);

    const escapeCell = (v) => {
        if (v === null || v === undefined) return '';
        const s = v.toString();
        if (s.includes(',') || s.includes('"') || s.includes('\n')) {
            return '"' + s.replace(/"/g, '""') + '"';
        }
        return s;
    };

    const csvContent = [headers.map(escapeCell).join(',')].concat(rows.map(r => r.map(escapeCell).join(','))).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `HCR2_Records_${timestamp}.csv`;

    if (navigator.msSaveBlob) {
        navigator.msSaveBlob(blob, filename);
    } else {
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
}


function fetchData(dataType) {
    if (window.closeMobileMenu) try { window.closeMobileMenu(); } catch (e) {}

    const container = document.getElementById('data-container');
    const filterContainer = document.getElementById('filter-container');
    const statsContainer = document.getElementById('stats-container');
    currentDataType = dataType;
    if (container) showElementWithFade(container);
    resetFilters();
    if (filterContainer) filterContainer.remove();
    if (statsContainer) hideElementWithFade(statsContainer);
    return cachedFetchJson('php/load_data.php?type=' + dataType + '&t=' + Date.now(), 60000)
    .then(data => {
        if (data.error) {
            console.error('Error:', data.error);
            if (container) container.innerHTML = '<p style="color:red;">' + data.error + '</p>';
        } else {
            allData = data;
            if (dataType === 'players') {
                cachedFetchJson('php/load_data.php?type=records&t=' + Date.now(), 60000)
                    .then(recordsData => {
                        const playerRecordCounts = {};
                        (recordsData || []).forEach(record => {
                            const playerName = record.player_name || '';
                            playerRecordCounts[playerName] = (playerRecordCounts[playerName] || 0) + 1;
                        });
                        window.playerRecordCounts = playerRecordCounts;
                        displayData(data, dataType);
                    }).catch(err => {
                        console.error('Failed to load records for player counts', err);
                        window.playerRecordCounts = {};
                        displayData(data, dataType);
                    });
            } else {
                displayData(data, dataType);
            }
        }
    }).catch(error => {
        console.error('Fetch error:', error);
        if (container) container.innerHTML = '<p style="color:red;">Error fetching data from server.</p>';
    });
}

function fetchSummary() {
fetch('php/load_data.php?type=records&t=' + Date.now())
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error:', data.error);
            const sc = document.getElementById('summary-container');
            if (sc) sc.innerHTML = '<p style="color:red;">' + esc(data.error) + '</p>';
        } else {
            displaySummary(data);
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
        const sc = document.getElementById('summary-container');
        if (sc) sc.innerHTML = '<p style="color:red;">Error fetching summary data from server.</p>';
    });
}

function displaySummary(data) {
const summaryContainer = document.getElementById('summary-container');
const playerRecords = {};
const vehicleDistances = {};

data.forEach(record => {
    
    playerRecords[record.player_name] = (playerRecords[record.player_name] || 0) + 1;

    
    vehicleDistances[record.vehicle_name] = (vehicleDistances[record.vehicle_name] || 0) + record.distance;
});


    const bestPlayer = Object.keys(playerRecords).reduce((a, b) => playerRecords[a] > playerRecords[b] ? a : b);
    const bestVehicle = Object.keys(vehicleDistances).reduce((a, b) => vehicleDistances[a] > vehicleDistances[b] ? a : b);

    summaryContainer.innerHTML = `
    <h2>Summary 📝</h2>
    <div class="summary-box">
        <p><strong>Best Player:</strong> ${esc(bestPlayer)} (${playerRecords[bestPlayer]} records)</p>
        <p><strong>Best Vehicle:</strong> ${esc(bestVehicle)} (${vehicleDistances[bestVehicle]} total distance)</p>
    </div>
`;
}


function displayData(data, dataType) {
const container = document.getElementById('data-container');
container.innerHTML = ''; 

container.innerHTML += '<h2>' + dataType.toUpperCase() + '</h2>'; 

if (data.length === 0) {
    container.innerHTML += '<p>No data available.</p>';
    return;
}

let tableHTML = '<table';
if (dataType === 'records') {
    tableHTML += ' class="public-records-table"';
}
tableHTML += '>';
if (dataType === 'maps') {
    tableHTML += '<tr><th>Map ID</th><th>Map Name</th></tr>';
    data.forEach(item => {
        tableHTML += `<tr><td>${item.idMap}</td><td>${item.nameMap}</td></tr>`;
    });
} else if (dataType === 'vehicles') {
    tableHTML += '<tr><th>Vehicle ID</th><th>Vehicle Name</th></tr>';
    data.forEach(item => {
        tableHTML += `<tr><td>${item.idVehicle}</td><td>${item.nameVehicle}</td></tr>`;
    });
} else if (dataType === 'players') {
    tableHTML += '<tr><th>Player ID</th><th>Player Name</th><th>Country</th><th>World Records</th></tr>';
    data.forEach(item => {
        const recordCount = window.playerRecordCounts ? (window.playerRecordCounts[item.namePlayer] || 0) : 0;
        tableHTML += `<tr><td>${item.idPlayer}</td><td>${esc(item.namePlayer)}</td><td>${renderCountryWithFlag(item.country)}</td><td>${recordCount}</td></tr>`;
    });
} else if (dataType === 'tuning_parts') {
    tableHTML += '<tr><th>Part ID</th><th>Part Name</th></tr>';
    data.forEach(item => {
        const tpName = item.nameTuningPart || item.name || item.name_tuning_part || item.tuning_part_name || '';
        const tpId = item.idTuningPart || item.id || '';
        tableHTML += `<tr><td>${tpId}</td><td>${renderTuningPartWithIcon(tpName)}</td></tr>`;
    });
} else if (dataType === 'records') {
    const sortSelect = document.getElementById('sort-select');
    const sortVal = sortSelect ? sortSelect.value : 'default';

    const records = Array.isArray(data) ? [...data] : [];

    const getMapId = r => {
        const v = r.idMap ?? r.mapId ?? r.map_id ?? null;
        return (v !== null && !isNaN(Number(v))) ? Number(v) : null;
    };
    const getVehicleId = r => {
        const v = r.idVehicle ?? r.vehicleId ?? r.vehicle_id ?? null;
        return (v !== null && !isNaN(Number(v))) ? Number(v) : null;
    };

    if (sortVal === 'dist-asc') {
        records.sort((a, b) => Number(a.distance) - Number(b.distance));
    } else if (sortVal === 'dist-desc') {
        records.sort((a, b) => Number(b.distance) - Number(a.distance));
     } else if (sortVal === 'most-recent') {
        records.sort((a, b) => {
            const aId = a.idRecord ?? a.record_id ?? 0;
            const bId = b.idRecord ?? b.record_id ?? 0;
            return Number(bId) - Number(aId);
        });
    } else {
        records.sort((a, b) => {
            const mapComp = String(a.map_name || a.nameMap || '').localeCompare(String(b.map_name || b.nameMap || ''));
            if (mapComp !== 0) return mapComp;
            const av = getVehicleId(a), bv = getVehicleId(b);
            if (av !== null && bv !== null && av !== bv) return av - bv;
            return String(a.vehicle_name || a.nameVehicle || '').localeCompare(String(b.vehicle_name || b.nameVehicle || ''));
        });
    }

    tableHTML += '<thead><tr><th>Distance</th><th>Status</th><th>Notes</th><th>Map Name</th><th>Vehicle Name</th><th>Tuning Parts</th><th>Player Name</th><th>Player Country</th></tr></thead><tbody>';
    records.forEach(item => {
        const rid = item.idRecord ?? item.record_id ?? '';
        let statusHTML = '';
        let notesHTML = '';
        const notes = item.questionable_reason ?? item.questionableReason ?? '';
        if (item.questionable === 1) {
            statusHTML = `<span title="Questionable: ${esc(notes || 'No note provided')}" class="questionable-status">❓</span>`;
        } else {
            statusHTML = '<span title="Verified: confirmed legitimate record" class="verified-status">✓</span>';
        }
        notesHTML = notes ? `<span title="${esc(notes)}" class="record-notes">${esc(notes)}</span>` : '';
        notesHTML = notes ? `<button class="note-btn" onclick="showNoteModal('${esc(notes).replace(/'/g, "\\'")}')">📝</button>` : '';
        tableHTML += `<tr data-record-id="${rid}">
            <td data-label="Distance">${formatDistance(item.distance)}</td>
            <td data-label="Status">${statusHTML}</td>
            <td data-label="Notes">${notesHTML}</td>
            <td data-label="Map">${renderMapWithIcon(item.map_name)}</td>
            <td data-label="Vehicle">${renderVehicleWithIcon(item.vehicle_name)}</td>
            <td data-label="Tuning Parts">${renderTuningParts(item.tuning_parts)}</td>
            <td data-label="Player">${esc(item.player_name)}</td>
            <td data-label="Country">${renderCountryWithFlag(item.player_country)}</td>
            <td data-label="Share"><button class="share-btn" onclick="copyShareLink('record', '${rid}', '${esc(item.map_name)}')">🔗 Copy Link</button></td>
            </tr>`;
    });
    tableHTML += '</tbody>';
}
tableHTML += '</table>';
    container.innerHTML += tableHTML;
    try {
        const params = new URLSearchParams(window.location.search);
        const linkedRecord = params.get('recordId');
        if (linkedRecord) {
            console.log('displayData: deep-link recordId present, attempting to highlight', linkedRecord);
            setTimeout(() => {
                const row = document.querySelector(`[data-record-id="${linkedRecord}"]`) || document.querySelector(`[data-record-id="${Number(linkedRecord)}"]`);
                console.log('displayData: found row?', !!row);
                if (row) {
                    row.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    row.style.background = 'rgba(255,255,0,0.12)';
                    setTimeout(()=> row.style.background = '', 3000);
                }
            }, 50);
        }
    } catch (e) { console.error('displayData deep-link fallback failed', e); }
if (dataType === 'records') {
    const maps = [...new Set(allData.map(record => record.map_name))].filter(Boolean).sort();
    const vehicles = [...new Set(allData.map(record => record.vehicle_name))].filter(Boolean).sort();
    const tuningParts = [...new Set(allData.flatMap(record => (record.tuning_parts && typeof record.tuning_parts === 'string') ? record.tuning_parts.split(', ').map(p => p.trim()) : []))].filter(Boolean).sort();

    const mapCheckboxes = maps.map(m => `<label style="display:block; padding:4px 6px;"><input type="checkbox" value="${esc(m)}" onchange="onMultiFilterChange('map')"> ${renderMapWithIcon(m)}</label>`).join('');
    const vehicleCheckboxes = vehicles.map(v => `<label style="display:block; padding:4px 6px;"><input type="checkbox" value="${esc(v)}" onchange="onMultiFilterChange('vehicle')"> ${renderVehicleWithIcon(v)}</label>`).join('');
    const tuningPartCheckboxes = tuningParts.map(p => `<label style="display:block; padding:4px 6px;"><input type="checkbox" value="${esc(p)}" onchange="onMultiFilterChange('tuning')"> ${renderTuningPartWithIcon(p)}</label>`).join('');

    const searchHTML = `
        <div id="filter-container" class="filter-container">
            <!-- Search Row -->
            <div class="filter-row">
                <input type="text" id="search-bar" class="filter-search" placeholder="Search by player, map, or vehicle..." oninput="filterRecords()">
            </div>

            <!-- Controls Row -->
            <div class="filter-row">
                <button id="export-btn" class="filter-btn filter-btn--primary" onclick="exportToCSV()">📥 Export CSV</button>

                <div class="filter-group">
                    <div class="multi-dropdown">
                        <button id="map-btn" class="filter-btn" onclick="toggleDropdown('map')">🗺️ Map</button>
                        <div id="map-panel" class="dropdown-panel">
                            <div class="dropdown-header">
                                <strong>Maps</strong>
                                <button type="button" class="dropdown-clear" onclick="clearMultiFilter('map')">Clear</button>
                            </div>
                            <div class="dropdown-content">${mapCheckboxes}</div>
                        </div>
                    </div>

                    <div class="multi-dropdown">
                        <button id="vehicle-btn" class="filter-btn" onclick="toggleDropdown('vehicle')">🚗 Vehicle</button>
                        <div id="vehicle-panel" class="dropdown-panel">
                            <div class="dropdown-header">
                                <strong>Vehicles</strong>
                                <button type="button" class="dropdown-clear" onclick="clearMultiFilter('vehicle')">Clear</button>
                            </div>
                            <div class="dropdown-content">${vehicleCheckboxes}</div>
                        </div>
                    </div>

                    <div class="multi-dropdown">
                        <button id="tuning-btn" class="filter-btn" onclick="toggleDropdown('tuning')">⚙️ Tuning</button>
                        <div id="tuning-panel" class="dropdown-panel">
                            <div class="dropdown-header">
                                <strong>Tuning Parts</strong>
                                <button type="button" class="dropdown-clear" onclick="clearMultiFilter('tuning')">Clear</button>
                            </div>
                            <div class="dropdown-content">${tuningPartCheckboxes}</div>
                        </div>
                    </div>
                </div>

                <select id="sort-select" class="filter-select" onchange="filterRecords()" title="Sort records">
                    <option value="default">Sort: Default</option>
                    <option value="dist-asc">Sort: Distance ↑</option>
                    <option value="dist-desc">Sort: Distance ↓</option>
                    <option value="most-recent">Sort: Newest</option>
                </select>

                <div class="filter-distance">
                    <select id="distance-op" class="filter-select" onchange="filterRecords()">
                        <option value="">Distance</option>
                        <option value="gte">≥</option>
                        <option value="lte">≤</option>
                    </select>
                    <input type="number" id="distance-value" class="filter-input" placeholder="Value" oninput="filterRecords()">
                </div>

                <label class="filter-label">
                    <input type="checkbox" id="questionable-filter" class="filter-checkbox" onchange="filterRecords()">
                    <span>Questionable ❓</span>
                </label>

                <label class="filter-label">
                    <input type="checkbox" id="verified-filter" class="filter-checkbox" onchange="filterRecords()">
                    <span>Verified ✓</span>
                </label>
            </div>
        </div>
        `;
    if (!document.getElementById('filter-container')) container.insertAdjacentHTML('beforebegin', searchHTML);
} else if (dataType === 'players') {
    if (!document.getElementById('filter-container')) addPlayerFilters();
}
}

function toggleDropdown(type) {
    const panel = document.getElementById(type + '-panel');
    const btn = document.getElementById(type + '-btn');
    if (!panel) return;
    const panels = document.querySelectorAll('.dropdown-panel');
    panels.forEach(p => {
        if (p !== panel) {
            p.style.display = 'none';
            p.classList.remove('open');
            const otherBtn = document.getElementById(p.id.replace('-panel','-btn'));
            if (otherBtn) otherBtn.setAttribute('aria-expanded', 'false');
        }
    });
    const isOpen = panel.classList.contains('open') || panel.style.display === 'block';
    if (isOpen) {
        panel.style.display = 'none';
        panel.classList.remove('open');
        if (btn) btn.setAttribute('aria-expanded', 'false');
    } else {
        panel.style.display = 'block';
        panel.classList.add('open');
        if (btn) btn.setAttribute('aria-expanded', 'true');
    }
}

document.addEventListener('click', function(e){
    const openPanels = document.querySelectorAll('.dropdown-panel.open');
    if (!openPanels.length) return;
    let clickedInside = false;
    openPanels.forEach(p => {
        if (p.contains(e.target)) clickedInside = true;
        const btn = document.getElementById(p.id.replace('-panel','-btn'));
        if (btn && btn.contains(e.target)) clickedInside = true;
    });
    if (!clickedInside) {
        openPanels.forEach(p => {
            p.style.display = 'none';
            p.classList.remove('open');
            const btn = document.getElementById(p.id.replace('-panel','-btn'));
            if (btn) btn.setAttribute('aria-expanded','false');
        });
    }
});

function copyToClipboard(text) {
    if (!text) return false;
    if (navigator.clipboard && navigator.clipboard.writeText) {
        return navigator.clipboard.writeText(text).then(()=>true).catch(()=>false);
    }
    try {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed'; ta.style.left = '-9999px';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        return Promise.resolve(true);
    } catch (e) {
        return Promise.resolve(false);
    }
}

function copyShareLink(type, id, mapName) {
    const url = new URL(window.location.href);
    if (type === 'record') {
        url.searchParams.set('view','records');
        if (id) url.searchParams.set('recordId', id);
        if (mapName) url.searchParams.set('map', mapName);
    } else if (type === 'map') {
        url.searchParams.set('view','records');
        if (id) url.searchParams.set('mapId', id);
    }
    copyToClipboard(url.toString()).then(ok => {
        const btn = document.activeElement;
        if (ok) {
            if (btn && btn.classList && btn.classList.contains('share-btn')) {
                const orig = btn.textContent;
                btn.textContent = 'Copied!';
                setTimeout(()=> btn.textContent = orig, 2000);
            } else {
                alert('Link copied to clipboard');
            }
        } else {
            alert('Failed to copy link.');
        }
    });
}

function getSelectedMultiValues(type) {
    const panel = document.getElementById(type + '-panel');
    if (!panel) return [];
    return Array.from(panel.querySelectorAll('input[type=checkbox]:checked')).map(cb => cb.value);
}

function onMultiFilterChange(type) {
    const btn = document.getElementById(type + '-btn');
    const sel = getSelectedMultiValues(type);
    if (btn) btn.textContent = sel.length ? `${type.charAt(0).toUpperCase() + type.slice(1)} (${sel.length})` : `Filter by ${type.charAt(0).toUpperCase() + type.slice(1)}`;
    filterRecords();
}

function clearMultiFilter(type) {
    const panel = document.getElementById(type + '-panel');
    if (!panel) return;
    panel.querySelectorAll('input[type=checkbox]').forEach(cb => cb.checked = false);
    const btn = document.getElementById(type + '-btn');
    if (btn) btn.textContent = `Filter by ${type.charAt(0).toUpperCase() + type.slice(1)}`;
    filterRecords();
}

function resetFilters() {
    const panels = document.querySelectorAll('.dropdown-panel');
    panels.forEach(panel => panel.style.display = 'none');
    
    const inputs = document.querySelectorAll('#search-bar, #player-search');
    inputs.forEach(input => input.value = '');
    
    const selects = document.querySelectorAll('#sort-select, #distance-op, #record-count-op');
    selects.forEach(select => select.value = '');
    
    const numberInputs = document.querySelectorAll('#distance-value, #record-count-value');
    numberInputs.forEach(input => input.value = '');
    
    const checkboxes = document.querySelectorAll('.dropdown-panel input[type=checkbox], #filter-container input[type=checkbox]');
    checkboxes.forEach(cb => cb.checked = false);
    
    const filterButtons = document.querySelectorAll('#filter-container [id$="-btn"]');
    filterButtons.forEach(btn => {
        const type = btn.id.replace('-btn', '');
        btn.textContent = `Filter by ${type.charAt(0).toUpperCase() + type.slice(1)}`;
    });
}


function filterRecords() {
const searchQuery = (document.getElementById('search-bar')?.value || '').toLowerCase();
const mapSelected = getSelectedMultiValues('map');
const vehicleSelected = getSelectedMultiValues('vehicle');
const tuningSelected = getSelectedMultiValues('tuning');
const distOp = document.getElementById('distance-op')?.value || '';
const distValRaw = document.getElementById('distance-value')?.value;
const distVal = distValRaw ? Number(distValRaw) : NaN;
const showOnlyQuestionable = document.getElementById('questionable-filter')?.checked || false;
const showOnlyVerified = document.getElementById('verified-filter')?.checked || false;

const filteredData = (allData || []).filter(record => {
    const notesText = (record.questionable_reason || record.questionableReason || '').toString().toLowerCase();
    const matchesSearch = (record.player_name || '').toString().toLowerCase().includes(searchQuery) ||
                            (record.map_name || '').toString().toLowerCase().includes(searchQuery) ||
                            (record.vehicle_name || '').toString().toLowerCase().includes(searchQuery) ||
                            notesText.includes(searchQuery);
    const matchesMap = !mapSelected || mapSelected.length === 0 || mapSelected.includes(record.map_name);
    const matchesVehicle = !vehicleSelected || vehicleSelected.length === 0 || vehicleSelected.includes(record.vehicle_name);
    const recordParts = (record.tuning_parts && typeof record.tuning_parts === 'string') ? record.tuning_parts.split(', ').map(p => p.trim()) : [];
    const matchesTuning = !tuningSelected || tuningSelected.length === 0 || tuningSelected.every(part => recordParts.includes(part));

    let matchesDistance = true;
    if (distOp === 'gte' && !isNaN(distVal)) {
        matchesDistance = Number(record.distance) >= distVal;
    } else if (distOp === 'lte' && !isNaN(distVal)) {
        matchesDistance = Number(record.distance) <= distVal;
    }

    const matchesQuestionable = !showOnlyQuestionable || record.questionable === 1;
    const matchesVerified = !showOnlyVerified || record.questionable === 0;

    return matchesSearch && matchesMap && matchesVehicle && matchesTuning && matchesDistance && matchesQuestionable && matchesVerified;
});

displayData(filteredData, currentDataType);
}

function addPlayerFilters() {
const container = document.getElementById('data-container');
const countries = [...new Set(allData.map(p => p.country).filter(c => c && c.trim()))].sort();
const countryCheckboxes = countries.map(c => `<label style="display:block; padding:4px 6px;"><input type="checkbox" value="${esc(c)}" onchange="onPlayerFilterChange('country')"> ${esc(c)}</label>`).join('');

const searchHTML = `
    <div id="filter-container" class="filter-container">
        <input type="text" id="player-search" placeholder="Search by player name..." oninput="filterPlayers()">

        <div class="multi-dropdown" style="display:inline-block; position:relative; margin-left:8px;">
            <button id="country-btn" onclick="toggleDropdown('country')" type="button">Filter by Country</button>
            <div id="country-panel" class="dropdown-panel" style="display:none; position:absolute; background:#fff; border:1px solid #ccc; padding:8px; max-height:220px; overflow:auto; z-index:50;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;"><strong>Countries</strong><button type="button" onclick="clearMultiFilter('country')" style="font-size:12px;">Clear</button></div>
                ${countryCheckboxes}
            	</div>
        	</div>

            <select id="record-count-op" onchange="filterPlayers()">
                <option value="">Records</option>
                <option value="gte">≥</option>
                <option value="lte">≤</option>
            </select>
            <input type="number" id="record-count-value" placeholder="Count" oninput="filterPlayers()" style="width:100px; margin-left:6px;" min="0">
        </div>
        `;

    container.insertAdjacentHTML('beforebegin', searchHTML);
}

function filterPlayers() {
const searchQuery = (document.getElementById('player-search')?.value || '').toLowerCase();
const countrySelected = getSelectedMultiValues('country');
const recordOp = document.getElementById('record-count-op')?.value || '';
const recordValRaw = document.getElementById('record-count-value')?.value;
const recordVal = recordValRaw ? Number(recordValRaw) : NaN;

const filteredData = (allData || []).filter(player => {
    const matchesSearch = (player.namePlayer || '').toString().toLowerCase().includes(searchQuery) ||
                          (player.country || '').toString().toLowerCase().includes(searchQuery);

    const matchesCountry = !countrySelected || countrySelected.length === 0 || countrySelected.includes(player.country);

    const recordCount = window.playerRecordCounts ? (window.playerRecordCounts[player.namePlayer] || 0) : 0;
    let matchesRecordCount = true;
    if (recordOp === 'gte' && !isNaN(recordVal)) {
        matchesRecordCount = recordCount >= recordVal;
    } else if (recordOp === 'lte' && !isNaN(recordVal)) {
        matchesRecordCount = recordCount <= recordVal;
    }

    return matchesSearch && matchesCountry && matchesRecordCount;
});

displayData(filteredData, currentDataType);
}

function onPlayerFilterChange(type) {
    const btn = document.getElementById(type + '-btn');
    const sel = getSelectedMultiValues(type);
    if (btn) btn.textContent = sel.length ? `${type.charAt(0).toUpperCase() + type.slice(1)} (${sel.length})` : `Filter by ${type.charAt(0).toUpperCase() + type.slice(1)}`;
    filterPlayers();
}


async function checkAuthAndInit() {
try {
    const res = await fetchWithTimeout('auth/status.php', { cache: 'no-cache', credentials: 'include' }, 2500);
    const status = res ? await res.json().catch(()=>({ logged: false })) : { logged: false };
    console.log('[AUTH] Status check result:', status);
    const loginBtn = document.getElementById('login-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const adminBtn = document.getElementById('admin-btn');
    const authWarning = document.getElementById('auth-warning');

    if (status.logged) {
        console.log('[AUTH] User is logged in as:', status.username || status.id);
        if (loginBtn) loginBtn.style.display = 'none';
        if (logoutBtn) { logoutBtn.style.display = 'inline-block'; logoutBtn.textContent = 'Logout (' + (status.username || status.id) + ')'; }
    } else {
        console.log('[AUTH] User is not logged in');
        if (loginBtn) loginBtn.style.display = 'inline-block';
        if (logoutBtn) logoutBtn.style.display = 'none';
    }

    if (status.logged && status.allowed) {
        if (adminBtn) {
            adminBtn.style.display = 'inline-block';
            adminBtn.onclick = () => location.href = 'php/admin.php';
        }
        if (authWarning) authWarning.textContent = '';
    } else {
        if (adminBtn) adminBtn.style.display = 'none';
        if (status.logged && !status.allowed) {
            if (authWarning) authWarning.textContent = 'Logged in as ' + (status.username || status.id) + ' — you do not have permission to edit records.';
        } else {
            if (authWarning) authWarning.textContent = '';
        }
    }
} catch (err) {
    console.error('[AUTH] Auth check failed', err);
}
}

window.onload = () => {
    console.log('[AUTH] Initial auth check starting...');
    checkAuthAndInit();
    setTimeout(() => {
        console.log('[AUTH] Retry auth check after 1s...');
        checkAuthAndInit();
    }, 1000);
    setInterval(checkAuthAndInit, 30000);
};

 
async function initGithubVersion() {
    const repo = 'Nipatsuplayer/hcr2-database-with-website';
    const versionEl = document.getElementById('github-version');
    const linkEl = document.getElementById('github-link');
    if (!versionEl || !linkEl) return;

    try {
        let res = await fetchWithTimeout(`https://api.github.com/repos/${repo}/releases/latest`, { }, 3000).catch(()=>null);
        if (res && res.ok) {
            const data = await res.json().catch(()=>null);
            if (data && data.tag_name) {
                versionEl.textContent = esc(data.tag_name);
                linkEl.href = data.html_url || `https://github.com/${repo}/releases`;
                linkEl.title = 'View release on GitHub';
                return;
            }
        }

        res = await fetchWithTimeout(`https://api.github.com/repos/${repo}/commits`, {}, 3000).catch(()=>null);
        if (res && res.ok) {
            const commits = await res.json().catch(()=>null);
            if (Array.isArray(commits) && commits.length > 0) {
                const sha = commits[0].sha ? commits[0].sha.substring(0, 7) : commits[0].sha;
                versionEl.textContent = esc(sha || 'unknown');
                linkEl.href = commits[0].html_url || `https://github.com/${repo}`;
                linkEl.title = 'View commit on GitHub';
                return;
            }
        }
    } catch (err) {
        console.error('Failed to fetch GitHub version:', err);
    }

    versionEl.textContent = 'unknown';
    linkEl.href = `https://github.com/${repo}`;
}

window.addEventListener('load', () => {
    try { initGithubVersion(); } catch (e) { console.error(e); }
});

window.addEventListener('error', function (evt) {
    console.error('Global error:', evt.message, evt.filename + ':' + evt.lineno);
});
window.addEventListener('unhandledrejection', function (evt) {
    console.error('Unhandled promise rejection:', evt.reason);
});

 
function publicSubmitOverlayClick(e) {
    const overlay = document.getElementById('public-submit-overlay');
    const panel = document.querySelector('.modal-panel');
    if (!overlay || !panel) return;
    if (e.target === overlay) {
        togglePublicSubmitForm();
    }
}

function publicSubmitKeyHandler(e) {
    if (e.key === 'Escape') togglePublicSubmitForm();
}

function togglePublicSubmitForm() {
    if (window.closeMobileMenu) try { window.closeMobileMenu(); } catch (e) {}
    const overlay = document.getElementById('public-submit-overlay');
    if (!overlay) return;
    const isOpen = overlay.style.display === 'block';
    if (isOpen) {
        overlay.style.display = 'none';
        document.removeEventListener('keydown', publicSubmitKeyHandler);
        overlay.removeEventListener('click', publicSubmitOverlayClick);
    } else {
        overlay.style.display = 'block';
        populatePublicSubmitOptions();
        document.addEventListener('keydown', publicSubmitKeyHandler);
        overlay.addEventListener('click', publicSubmitOverlayClick);
        
        const formLoadTimeEl = document.getElementById('form-load-time');
        if (formLoadTimeEl) {
            formLoadTimeEl.value = Date.now();
        }
        
        initializeHCaptcha();
        
        setTimeout(() => {
            const first = document.getElementById('public-map-select');
            if (first) first.focus();
        }, 50);
    }
}

function initializeHCaptcha() {
    fetch('php/get_hcaptcha_sitekey.php')
        .then(res => res.json())
        .then(data => {
            if (data.sitekey) {
                const widget = document.getElementById('hcaptcha-widget');
                if (!widget) return;

                widget.setAttribute('data-sitekey', data.sitekey);

                const tryRender = () => {
                    if (window.hcaptcha && typeof window.hcaptcha.render === 'function') {
                        try {
                            const renderTarget = widget; // pass element directly
                            const widgetId = window.hcaptcha.render(renderTarget, {
                                sitekey: data.sitekey,
                                theme: 'light',
                                callback: function(token) {
                                    const el = document.getElementById('h-captcha-response');
                                    if (el) el.value = token;
                                },
                                'expired-callback': function() {
                                    const el = document.getElementById('h-captcha-response');
                                    if (el) el.value = '';
                                }
                            });
                            widget.dataset.hcaptchaWidgetId = widgetId;
                            return true;
                        } catch (e) {
                            console.error('hCaptcha render failed', e);
                            return false;
                        }
                    }
                    return false;
                };

                if (!tryRender()) {
                    let attempts = 0;
                    const maxAttempts = 30;
                    const iv = setInterval(() => {
                        attempts++;
                        if (tryRender() || attempts >= maxAttempts) {
                            clearInterval(iv);
                        }
                    }, 200);
                }
            } else {
                console.error('hCaptcha sitekey not provided by server');
            }
        })
        .catch(err => console.error('Failed to load hCaptcha site key', err));
}

function toggleNewsModal() {
    if (window.closeMobileMenu) try { window.closeMobileMenu(); } catch (e) {}
    const overlay = document.getElementById('news-overlay');
    if (!overlay) return;
    const isOpen = overlay.style.display === 'block';
    if (isOpen) {
        overlay.style.display = 'none';
    } else {
        overlay.style.display = 'block';
        loadNews();
        markNewsAsRead();
    }
}

function showNoteModal(note) {
    if (window.closeMobileMenu) try { window.closeMobileMenu(); } catch (e) {}
    const overlay = document.getElementById('note-overlay');
    const content = document.getElementById('note-content');
    if (!overlay || !content) return;
    content.textContent = note;
    overlay.style.display = 'block';
}

function hideNoteModal() {
    const overlay = document.getElementById('note-overlay');
    if (overlay) overlay.style.display = 'none';
}

async function loadNews() {
    const el = document.getElementById('news-list');
    if (!el) return;
    el.innerHTML = '<p>Loading news...</p>';
    try {
        const res = await fetch('php/get_news.php', { cache: 'no-cache' });
        const data = await res.json();
        if (data.error) {
            el.innerHTML = '<p style="color:red;">' + esc(data.error) + '</p>';
            return;
        }
        const items = Array.isArray(data.news) ? data.news : [];
        if (items.length === 0) {
            el.innerHTML = '<p>No news available.</p>';
            return;
        }
        const html = items.map(n => {
            const created = n.created_at ? n.created_at : '';
            const title = esc(n.title || '');
            const content = esc(n.content || '');
            const author = esc(n.author || '');
            return `<div class="news-item" style="padding:12px; border-bottom:1px solid #eee;"><h3 style=\"margin:0 0 6px 0;\">${title}</h3><div style=\"font-size:13px;color:#666;margin-bottom:8px;\">${created} — ${author}</div><div style=\"white-space:pre-wrap;\">${content}</div></div>`;
        }).join('');
        el.innerHTML = html;
    } catch (err) {
        console.error('Failed to load news', err);
        el.innerHTML = '<p style="color:red;">Failed to load news.</p>';
    }
}

async function populatePublicSubmitOptions() {
    try {
        const mapsRes = await fetch('php/load_data.php?type=maps&t=' + Date.now());
        const maps = await mapsRes.json();
        const mapSel = document.getElementById('public-map-select');
        if (mapSel && Array.isArray(maps)) {
            mapSel.innerHTML = '<option value="">Select a Map</option>' + maps.map(m => `<option value="${esc(m.idMap)}">${esc(m.nameMap)}</option>`).join('');
        }

        const vehiclesRes = await fetch('php/load_data.php?type=vehicles&t=' + Date.now());
        const vehicles = await vehiclesRes.json();
        const vehicleSel = document.getElementById('public-vehicle-select');
        if (vehicleSel && Array.isArray(vehicles)) {
            vehicleSel.innerHTML = '<option value="">Select a Vehicle</option>' + vehicles.map(v => `<option value="${esc(v.idVehicle)}">${esc(v.nameVehicle)}</option>`).join('');
        }
        try {
            const partsRes = await fetch('php/load_data.php?type=tuning_parts&t=' + Date.now());
            const parts = await partsRes.json();
            const partsContainer = document.getElementById('public-tuning-parts');
            if (partsContainer && Array.isArray(parts)) {
                partsContainer.innerHTML = parts.map(p => {
                    const id = esc(p.idTuningPart || p.id || '');
                    const name = esc(p.nameTuningPart || p.nameTuningPart || p.name || '');
                    return `<label><input type="checkbox" name="public-tuning-part" value="${name}" id="public-tuning-part-${id}"> ${name}</label>`;
                }).join('');
            }
        } catch (err) {
            console.error('Failed to load tuning parts for public submit', err);
        }
    } catch (err) {
        console.error('Failed to load maps/vehicles for public submit', err);
    }
}

async function submitPublicRecord(e) {
    e.preventDefault();
    const mapId = document.getElementById('public-map-select').value;
    const vehicleId = document.getElementById('public-vehicle-select').value;
    const distance = document.getElementById('public-distance-input').value;
    const playerName = document.getElementById('public-player-name').value.trim();
    const playerCountry = document.getElementById('public-player-country').value.trim();
    const msgEl = document.getElementById('public-submit-message');

    if (!mapId || !vehicleId || !distance || !playerName) {
        if (msgEl) { msgEl.textContent = 'Please complete all required fields.'; msgEl.style.color = 'red'; }
        return;
    }
    if (isNaN(Number(distance)) || Number(distance) <= 0) {
        if (msgEl) { msgEl.textContent = 'Distance must be a positive number.'; msgEl.style.color = 'red'; }
        return;
    }
    const selectedPartEls = document.querySelectorAll('#public-tuning-parts input[type="checkbox"]:checked');
    const selectedParts = Array.from(selectedPartEls).map(el => el.value);
    if (selectedParts.length < 3 || selectedParts.length > 4) {
        if (msgEl) { msgEl.textContent = 'Please choose 3 or 4 tuning parts for the record.'; msgEl.style.color = 'red'; }
        return;
    }

    try {
        const hcaptchaResponse = document.getElementById('h-captcha-response').value || '';
        if (!hcaptchaResponse) {
            if (msgEl) { msgEl.textContent = 'Please complete the hCaptcha verification.'; msgEl.style.color = 'red'; }
            return;
        }
        
        const hp_email = document.getElementById('hp_email') ? document.getElementById('hp_email').value.trim() : '';
        const hp_website = document.getElementById('hp_website') ? document.getElementById('hp_website').value.trim() : '';
        const hp_phone = document.getElementById('hp_phone') ? document.getElementById('hp_phone').value.trim() : '';
        const hp_comments = document.getElementById('hp_comments') ? document.getElementById('hp_comments').value.trim() : '';
        
        const formLoadTime = parseInt(document.getElementById('form-load-time').value) || 0;
        const submissionTime = Date.now();
        
        const res = await fetch('php/public_submit.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                mapId, vehicleId, distance: Number(distance), playerName, playerCountry,
            tuningParts: selectedParts,
                h_captcha_response: hcaptchaResponse,
                hp_email: hp_email,
                hp_website: hp_website,
                hp_phone: hp_phone,
                hp_comments: hp_comments,
                form_load_time: formLoadTime,
                submission_time: submissionTime,
            })
        });
        const data = await res.json();
        if (!res.ok) {
            if (msgEl) { msgEl.textContent = data.error || 'Submission failed'; msgEl.style.color = 'red'; }
            return;
        }
        if (data.success) {
            if (msgEl) { msgEl.textContent = data.message || 'Submitted'; msgEl.style.color = 'green'; }
            document.getElementById('public-submit-form').reset();
        } else {
            if (msgEl) { msgEl.textContent = data.error || 'Submission failed'; msgEl.style.color = 'red'; }
        }
    } catch (err) {
        console.error('Public submit failed', err);
        if (msgEl) { msgEl.textContent = 'Submission failed (network error).'; msgEl.style.color = 'red'; }
    }
}

function submitRecord(event) {
event.preventDefault();

const mapId = document.getElementById('map-select').value;
const vehicleId = document.getElementById('vehicle-select').value;
const distance = document.getElementById('distance-input').value;
const playerId = document.getElementById('player-select').value;
const newPlayerName = document.getElementById('new-player-input').value;
const country = document.getElementById('country-input').value;

if (!playerId && !newPlayerName) {
    document.getElementById('form-message').textContent = 'Please select an existing player or add a new one.';
    document.getElementById('form-message').style.color = 'red';
    return;
}

if (!playerId && newPlayerName && !country) {
    document.getElementById('form-message').textContent = 'Please provide a country for the new player.';
    document.getElementById('form-message').style.color = 'red';
    return;
}

const selectedPlayerOption = document.getElementById('player-select').selectedOptions[0];
const selectedPlayerName = selectedPlayerOption ? selectedPlayerOption.textContent : '';

const note = document.getElementById('questionable-reason-submit').value.trim();
const hasPlayerId = (playerId !== null && playerId !== undefined && playerId !== '');
const formData = hasPlayerId ? {
    mapId,
    vehicleId,
    distance,
    playerId,
    playerName: selectedPlayerName,
    questionable: document.getElementById('questionable-input').checked ? 1 : 0,
    note
} : {
    mapId,
    vehicleId,
    distance,
    playerId: null,
    newPlayerName,
    country,
    questionable: document.getElementById('questionable-input').checked ? 1 : 0,
    note
};

fetch('php/submit_record.php', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify(formData)
})
.then(async response => {
    const data = await response.json().catch(()=>({ error: 'Invalid server response' }));
    if (!response.ok) {
        const msg = data.error || (response.status === 401 ? 'Authentication required.' : response.status === 403 ? 'Forbidden: insufficient permissions.' : 'Server error');
        document.getElementById('form-message').textContent = 'Error: ' + msg;
        document.getElementById('form-message').style.color = 'red';
        return;
    }
    if (data.success) {
        const mapName = data.mapName || 'Unknown';
        const vehicleName = data.vehicleName || 'Unknown';
        const playerName = data.playerName || 'Unknown';
        const distance = data.distance || '?';
        
        const successMsg = `✅ Record submitted! | ${playerName} | ${mapName} | ${vehicleName} | ${formatDistance(distance)}m`;
        const msgEl = document.getElementById('form-message');
        msgEl.textContent = successMsg;
        msgEl.style.color = 'green';
        msgEl.style.display = 'block';
        document.getElementById('record-form').reset();

        populateDeleteOptions();
        populateFormOptions();
        
        
        setTimeout(() => {
            msgEl.textContent = '';
        }, 5000);
    } else {
        document.getElementById('form-message').textContent = 'Error: ' + (data.error || 'Unknown error');
        document.getElementById('form-message').style.color = 'red';
    }
})
.catch(error => {
    document.getElementById('form-message').textContent = 'Error submitting record.';
    document.getElementById('form-message').style.color = 'red';
});
}

function populateDeleteOptions() {
fetch('php/load_data.php?type=records&t=' + Date.now())
    .then(response => response.json())
    .then(data => {
        const recordSelect = document.getElementById('record-select');
        recordSelect.innerHTML = '<option value="">Select a Record</option>';
        (data || []).forEach(record => {
            const option = document.createElement('option');
            option.value = record.idRecord;
            option.textContent = `${formatDistance(record.distance)} - ${record.map_name} - ${record.vehicle_name} - ${record.player_name}`;
            recordSelect.appendChild(option);
        });
    });
}

function deleteRecord(event) {
event.preventDefault();

const recordId = document.getElementById('record-select').value;

if (!recordId) {
    document.getElementById('delete-message').textContent = 'Please select a record to delete.';
    document.getElementById('delete-message').style.color = 'red';
    return;
}

fetch('php/delete_record.php', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify({ recordId })
})
.then(async response => {
    const data = await response.json().catch(()=>({ error: 'Invalid server response' }));
    if (!response.ok) {
        const msg = data.error || (response.status === 401 ? 'Authentication required.' : response.status === 403 ? 'Forbidden: insufficient permissions.' : 'Server error');
        document.getElementById('delete-message').textContent = 'Error: ' + msg;
        document.getElementById('delete-message').style.color = 'red';
        return;
    }
    if (data.success) {
        document.getElementById('delete-message').textContent = 'Record deleted successfully!';
        document.getElementById('delete-message').style.color = 'green';
        populateDeleteOptions();
    } else {
        document.getElementById('delete-message').textContent = 'Error: ' + (data.error || 'Unknown error');
        document.getElementById('delete-message').style.color = 'red';
    }
})
.catch(error => {
    document.getElementById('delete-message').textContent = 'Error deleting record.';
    document.getElementById('delete-message').style.color = 'red';
});
}

function exportToCSV() {
    const searchQuery = (document.getElementById('search-bar')?.value || '').toLowerCase();
    const mapSelected = getSelectedMultiValues('map');
    const vehicleSelected = getSelectedMultiValues('vehicle');
    const distOp = document.getElementById('distance-op')?.value || '';
    const distValRaw = document.getElementById('distance-value')?.value;
    const distVal = distValRaw ? Number(distValRaw) : NaN;

    const filteredData = (allData || []).filter(record => {
        const matchesSearch = (record.player_name || '').toString().toLowerCase().includes(searchQuery) ||
                              (record.map_name || '').toString().toLowerCase().includes(searchQuery) ||
                              (record.vehicle_name || '').toString().toLowerCase().includes(searchQuery);
        const matchesMap = !mapSelected || mapSelected.length === 0 || mapSelected.includes(record.map_name);
        const matchesVehicle = !vehicleSelected || vehicleSelected.length === 0 || vehicleSelected.includes(record.vehicle_name);

        let matchesDistance = true;
        if (distOp === 'gte' && !isNaN(distVal)) {
            matchesDistance = Number(record.distance) >= distVal;
        } else if (distOp === 'lte' && !isNaN(distVal)) {
            matchesDistance = Number(record.distance) <= distVal;
        }

        return matchesSearch && matchesMap && matchesVehicle && matchesDistance;
    });

    if (!filteredData || filteredData.length === 0) {
        alert('No records to export. Please check your filters.');
        return;
    }

    downloadCSV(filteredData);
}

function closeMenu() {
        const btn = document.getElementById('mobile-menu-btn');
        const menu = document.getElementById('mobile-menu');
        if (!btn || !menu) return;
        try {
                const active = document.activeElement;
                if (menu.contains(active)) {
                        if (typeof active.blur === 'function') active.blur();
                        btn.focus();
                }
        } catch (e) {}
        btn.setAttribute('aria-expanded','false');
        menu.setAttribute('aria-hidden','true');
        document.body.classList.remove('mobile-menu-open');
    }

function openMenu() {
    const btn = document.getElementById('mobile-menu-btn');
    const menu = document.getElementById('mobile-menu');
    if (!btn || !menu) return;
    btn.setAttribute('aria-expanded','true');
    menu.setAttribute('aria-hidden','false');
    document.body.classList.add('mobile-menu-open');
  }

window.toggleMobileMenu = function(){
    const btn = document.getElementById('mobile-menu-btn');
    const menu = document.getElementById('mobile-menu');
    if (!btn || !menu) return;
    const isOpen = btn.getAttribute('aria-expanded') === 'true';

    if (isOpen) {
        closeMenu();
    } else {
        openMenu();
        try {
            const focusable = menu.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (focusable && typeof focusable.focus === 'function') focusable.focus();
        } catch (e) {}
    }
  }

  window.toggleMobileMenu = toggleMobileMenu;
  window.closeMobileMenu = closeMenu;
  window.openMobileMenu = openMenu;
    
document.addEventListener('click', function(e){
    const btn = document.getElementById('mobile-menu-btn');
    const menu = document.getElementById('mobile-menu');
    if (!btn || !menu) return;
    if (btn.contains(e.target) || menu.contains(e.target)) return;
    if (btn.getAttribute('aria-expanded') === 'true') closeMenu();
});

window.addEventListener('resize', function(){
    const btn = document.getElementById('mobile-menu-btn');
    const menu = document.getElementById('mobile-menu');
    if (!btn || !menu) return;
    if (window.innerWidth >= 800) {
        try { if (menu.contains(document.activeElement)) { document.activeElement.blur(); btn.focus(); } } catch(e) {}
        menu.removeAttribute('aria-hidden');
        btn.setAttribute('aria-expanded','false');
        document.body.classList.remove('mobile-menu-open');
    } else {
        try { if (menu.contains(document.activeElement)) { document.activeElement.blur(); btn.focus(); } } catch(e) {}
        menu.setAttribute('aria-hidden','true');
        btn.setAttribute('aria-expanded','false');
        document.body.classList.remove('mobile-menu-open');
    }
});

document.addEventListener('DOMContentLoaded', function(){
    const menu = document.getElementById('mobile-menu');
    const btn = document.getElementById('mobile-menu-btn');
    if (!menu || !btn) return;
    if (window.innerWidth >= 800) {
        try { if (menu.contains(document.activeElement)) { document.activeElement.blur(); btn.focus(); } } catch(e) {}
        menu.removeAttribute('aria-hidden');
        btn.setAttribute('aria-expanded','false');
    } else {
        try { if (menu.contains(document.activeElement)) { document.activeElement.blur(); btn.focus(); } } catch(e) {}
        menu.setAttribute('aria-hidden','true');
        btn.setAttribute('aria-expanded','false');
    }
});

function handleDeepLinkParams() {
    try {
        const params = new URLSearchParams(window.location.search);
        const view = params.get('view');
        const recordId = params.get('recordId');
        const map = params.get('map');
        const validTypes = ['maps', 'vehicles', 'players', 'tuning_parts', 'records', 'tuning_setups'];
        if (!view || !validTypes.includes(view)) {
            return;
        }
        try {
                fetchData(view).then(() => {
                    if (recordId) {
                        const row = document.querySelector(`[data-record-id="${recordId}"]`);
                        if (row) {
                            row.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            row.style.background = 'rgba(255,255,0,0.12)';
                            setTimeout(()=> row.style.background = '', 3000);
                            return;
                        }
                        const alt = document.querySelector(`[data-record-id="${Number(recordId)}"]`);
                        if (alt) { alt.scrollIntoView({ behavior: 'smooth', block: 'center' }); alt.style.background = 'rgba(255,255,0,0.12)'; setTimeout(()=> alt.style.background = '', 3000); }
                    } else if (map) {
                        const el = Array.from(document.querySelectorAll('[data-label="Map"]')).find(td => td && td.textContent && td.textContent.includes(map));
                        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }).catch(()=>{
                    setTimeout(() => {
                        if (recordId) {
                            const row = document.querySelector(`[data-record-id="${recordId}"]`);
                            if (row) {
                                row.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                row.style.background = 'rgba(255,255,0,0.12)';
                                setTimeout(()=> row.style.background = '', 3000);
                            }
                        } else if (map) {
                            const el = Array.from(document.querySelectorAll('[data-label="Map"]')).find(td => td && td.textContent && td.textContent.includes(map));
                            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }
                    }, 1000);
                });
            } catch (e) {}
        } catch (e) {
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', handleDeepLinkParams);
} else {
    try { handleDeepLinkParams(); } catch (e) {}
}