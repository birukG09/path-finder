let map;
let markers = [];
let polylines = [];
let locationsData = [];
let edgesData = [];

function initMap() {
    map = L.map('map').setView([9.0107, 38.7613], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);

    loadLocations();
}

async function loadLocations() {
    try {
        const response = await fetch('/api/locations');
        const data = await response.json();
        locationsData = data.locations;
        edgesData = data.edges;

        populateDropdowns();
        displayLocationsOnMap();
        displayEdgesOnMap();
    } catch (error) {
        console.error('Error loading locations:', error);
    }
}

function populateDropdowns() {
    const startSelect = document.getElementById('start');
    const goalSelect = document.getElementById('goal');

    locationsData.forEach(location => {
        const option1 = document.createElement('option');
        option1.value = location.name;
        option1.textContent = location.name;
        startSelect.appendChild(option1);

        const option2 = document.createElement('option');
        option2.value = location.name;
        option2.textContent = location.name;
        goalSelect.appendChild(option2);
    });
}

function displayLocationsOnMap() {
    locationsData.forEach(location => {
        const marker = L.marker([location.lat, location.lng])
            .addTo(map)
            .bindPopup(`<b>${location.name}</b>`);
        
        const icon = L.divIcon({
            className: 'custom-marker',
            html: `<div style="background: white; padding: 4px 8px; border-radius: 4px; border: 2px solid #3498db; font-size: 11px; font-weight: bold; white-space: nowrap; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">${location.name}</div>`,
            iconSize: [0, 0],
            iconAnchor: [0, 0]
        });
        
        marker.setIcon(icon);
        markers.push(marker);
    });
}

function displayEdgesOnMap() {
    edgesData.forEach(edge => {
        const fromLoc = locationsData.find(l => l.name === edge.from);
        const toLoc = locationsData.find(l => l.name === edge.to);

        if (fromLoc && toLoc) {
            const line = L.polyline([
                [fromLoc.lat, fromLoc.lng],
                [toLoc.lat, toLoc.lng]
            ], {
                color: '#cccccc',
                weight: 2,
                opacity: 0.5
            }).addTo(map);
            
            polylines.push(line);
        }
    });
}

function clearPathDisplay() {
    polylines.forEach(line => {
        map.removeLayer(line);
    });
    polylines = [];
    
    displayEdgesOnMap();
    
    document.getElementById('warnings').classList.remove('show');
    document.getElementById('results').classList.remove('show');
}

async function findPath() {
    const start = document.getElementById('start').value;
    const goal = document.getElementById('goal').value;
    const algorithm = document.getElementById('algorithm').value;

    if (!start || !goal) {
        alert('Please select both starting and goal locations');
        return;
    }

    clearPathDisplay();

    try {
        const response = await fetch('/api/findpath', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ start, goal, algorithm })
        });

        const data = await response.json();

        if (!response.ok) {
            alert(data.error || 'Error finding path');
            return;
        }

        displayWarnings(data.warnings);
        displayResults(data.paths, data.cost, data.numPaths, data.algorithm);
        displayPathsOnMap(data.paths);

    } catch (error) {
        console.error('Error finding path:', error);
        alert('Error finding path. Please try again.');
    }
}

function displayWarnings(warnings) {
    const warningsDiv = document.getElementById('warnings');
    
    if (warnings && warnings.length > 0) {
        warningsDiv.innerHTML = warnings.map(w => `<p>${w}</p>`).join('');
        warningsDiv.classList.add('show');
    } else {
        warningsDiv.classList.remove('show');
    }
}

function displayResults(paths, cost, numPaths, algorithm) {
    const resultsDiv = document.getElementById('results');
    
    let html = '<h3>Path Found</h3>';
    if (algorithm) {
        html += `<p><strong>Algorithm:</strong> ${algorithm}</p>`;
    }
    html += `<p><strong>Total Distance:</strong> ${cost} km</p>`;
    
    if (numPaths > 1) {
        html += `<p><strong>Number of optimal paths:</strong> ${numPaths}</p>`;
        paths.forEach((path, index) => {
            const pathNames = path.map(p => p.name).join(' → ');
            html += `<div class="path-item"><strong>Path ${index + 1}:</strong> ${pathNames}</div>`;
        });
    } else {
        const pathNames = paths[0].map(p => p.name).join(' → ');
        html += `<p><strong>Route:</strong> ${pathNames}</p>`;
    }
    
    resultsDiv.innerHTML = html;
    resultsDiv.classList.add('show');
}

function displayPathsOnMap(paths) {
    const colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'];
    
    paths.forEach((path, index) => {
        const pathCoords = path.map(p => [p.lat, p.lng]);
        
        const pathLine = L.polyline(pathCoords, {
            color: colors[index % colors.length],
            weight: 4,
            opacity: 1.0
        }).addTo(map);
        
        polylines.push(pathLine);
    });

    if (paths.length > 0 && paths[0].length > 0) {
        const bounds = L.latLngBounds(paths[0].map(p => [p.lat, p.lng]));
        map.fitBounds(bounds, { padding: [50, 50] });
    }
}

function toggleLegend() {
    const legend = document.getElementById('legend');
    legend.classList.toggle('show');
}

function closeLegend() {
    const legend = document.getElementById('legend');
    legend.classList.remove('show');
}

document.addEventListener('DOMContentLoaded', function() {
    initMap();
    document.getElementById('findPath').addEventListener('click', findPath);
    document.getElementById('clearPath').addEventListener('click', clearPathDisplay);
    document.getElementById('legendToggle').addEventListener('click', toggleLegend);
    document.getElementById('legendClose').addEventListener('click', closeLegend);
});
