// Global variables
let map;
let selectedCountries = new Set(['US', 'IN']);
let countryData = {};
let charts = {};
let csvData = {};

// Country information with coordinates and flags
const COUNTRIES = {
    'US': { name: 'United States', coords: [39.8283, -98.5795], flag: '🇺🇸', color: '#3498db' },
    'IN': { name: 'India', coords: [20.5937, 78.9629], flag: '🇮🇳', color: '#e74c3c' },
    'CN': { name: 'China', coords: [35.8617, 104.1954], flag: '🇨🇳', color: '#f39c12' },
    'DE': { name: 'Germany', coords: [51.1657, 10.4515], flag: '🇩🇪', color: '#9b59b6' },
    'JP': { name: 'Japan', coords: [36.2048, 138.2529], flag: '🇯🇵', color: '#1abc9c' },
    'GB': { name: 'United Kingdom', coords: [55.3781, -3.4360], flag: '🇬🇧', color: '#34495e' },
    'FR': { name: 'France', coords: [46.2276, 2.2137], flag: '🇫🇷', color: '#e67e22' },
    'IT': { name: 'Italy', coords: [41.8719, 12.5674], flag: '🇮🇹', color: '#2ecc71' },
    'CA': { name: 'Canada', coords: [56.1304, -106.3468], flag: '🇨🇦', color: '#e91e63' },
    'BR': { name: 'Brazil', coords: [-14.2350, -51.9253], flag: '🇧🇷', color: '#795548' },
    'AU': { name: 'Australia', coords: [-25.2744, 133.7751], flag: '🇦🇺', color: '#607d8b' },
    'KR': { name: 'South Korea', coords: [35.9078, 127.7669], flag: '🇰🇷', color: '#ff5722' }
};

// Priority factors for analysis
const PRIORITY_FACTORS = {
    air_emissions: ['CO2', 'CH4', 'N2O', 'NOX', 'CO', 'SO2', 'NH3', 'PM10', 'PM2.5'],
    employment: ['Employment people', 'Employment hours'],
    energy: ['Energy use', 'Electricity', 'Natural gas', 'Oil'],
    water: ['Water consumption', 'Water withdrawal'],
    land: ['Cropland', 'Forest', 'Pastures', 'Artificial'],
    material: ['Metal Ores', 'Non-Metallic Minerals', 'Fossil Fuels', 'Primary Crops']
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeMap();
    loadCountryData();
    setupEventListeners();
    updateCountryPanels();
    initializeCharts();
    
    // Apply Motion.dev animations
    applyAnimations();
});

// Initialize Leaflet map
function initializeMap() {
    map = L.map('map', {
        center: [20, 0],
        zoom: 2,
        zoomControl: true,
        scrollWheelZoom: true
    });

    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(map);

    // Add country markers
    Object.entries(COUNTRIES).forEach(([code, country]) => {
        const isSelected = selectedCountries.has(code);
        const marker = L.circleMarker(country.coords, {
            radius: isSelected ? 12 : 8,
            fillColor: isSelected ? country.color : '#95a5a6',
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: isSelected ? 0.8 : 0.4
        }).addTo(map);

        // Create popup content
        const popupContent = createMapPopup(code, country, isSelected);
        marker.bindPopup(popupContent);

        // Handle marker click
        marker.on('click', () => toggleCountrySelection(code));
        
        // Store marker reference
        country.marker = marker;
    });

    updateMapLegend();
}

// Create map popup content
function createMapPopup(code, country, isSelected) {
    const data = getCountryMockData(code);
    return `
        <div class="map-popup">
            <div class="popup-header">
                <span class="popup-flag">${country.flag}</span>
                <h3>${country.name}</h3>
                <span class="popup-status ${isSelected ? 'selected' : 'available'}">${isSelected ? 'Selected' : 'Available'}</span>
            </div>
            <div class="popup-metrics">
                <div class="popup-metric">
                    <strong>${data.tradeFlows.toLocaleString()}</strong>
                    <span>Trade Flows</span>
                </div>
                <div class="popup-metric">
                    <strong>${data.factorRelationships.toLocaleString()}</strong>
                    <span>Environmental Factors</span>
                </div>
                <div class="popup-metric">
                    <strong>${data.employmentIntensity}×</strong>
                    <span>Employment Intensity</span>
                </div>
            </div>
            <button onclick="toggleCountrySelection('${code}')" class="popup-btn">
                ${isSelected ? 'Deselect' : 'Select'} Country
            </button>
        </div>
    `;
}

// Toggle country selection
function toggleCountrySelection(countryCode) {
    if (selectedCountries.has(countryCode)) {
        if (selectedCountries.size > 1) {
            selectedCountries.delete(countryCode);
        } else {
            // Prevent deselecting the last country
            return;
        }
    } else {
        if (selectedCountries.size < 12) {
            selectedCountries.add(countryCode);
        } else {
            // Show message about maximum countries
            showNotification('Maximum 12 countries can be selected');
            return;
        }
    }

    updateMapMarkers();
    updateMapLegend();
    updateCountryPanels();
    updateCharts();
    updateSelectionCount();
}

// Update map markers based on selection
function updateMapMarkers() {
    Object.entries(COUNTRIES).forEach(([code, country]) => {
        const isSelected = selectedCountries.has(code);
        const marker = country.marker;
        
        marker.setStyle({
            radius: isSelected ? 12 : 8,
            fillColor: isSelected ? country.color : '#95a5a6',
            fillOpacity: isSelected ? 0.8 : 0.4
        });

        // Update popup content
        const popupContent = createMapPopup(code, country, isSelected);
        marker.setPopupContent(popupContent);
    });
}

// Update map legend
function updateMapLegend() {
    const selectedContainer = document.getElementById('selected-countries');
    const availableContainer = document.getElementById('available-countries');
    
    selectedContainer.innerHTML = '';
    availableContainer.innerHTML = '';

    Object.entries(COUNTRIES).forEach(([code, country]) => {
        const countryItem = createCountryLegendItem(code, country);
        
        if (selectedCountries.has(code)) {
            selectedContainer.appendChild(countryItem);
        } else {
            availableContainer.appendChild(countryItem);
        }
    });
}

// Create country legend item
function createCountryLegendItem(code, country) {
    const isSelected = selectedCountries.has(code);
    const item = document.createElement('div');
    item.className = 'country-item';
    item.onclick = () => toggleCountrySelection(code);
    
    item.innerHTML = `
        <div class="country-checkbox ${isSelected ? 'selected' : ''}" style="background-color: ${isSelected ? country.color : 'transparent'}">
            ${isSelected ? '✓' : ''}
        </div>
        <span class="country-flag">${country.flag}</span>
        <span class="country-name">${country.name}</span>
    `;
    
    return item;
}

// Load country data from CSV files
async function loadCountryData() {
    try {
        // In a real implementation, you would load actual CSV files
        // For now, we'll use mock data based on the actual results
        countryData = {
            'US': {
                tradeFlows: 188735,
                factorRelationships: 125148,
                airEmissions: 49177,
                employment: 4121,
                energy: 51907,
                land: 7170,
                materials: 6853,
                water: 5920
            },
            'IN': {
                tradeFlows: 93845,
                factorRelationships: 82073,
                airEmissions: 19813,
                employment: 24039,
                energy: 15840,
                land: 3223,
                materials: 1193,
                water: 17965
            }
        };

        // Generate mock data for other countries
        Object.keys(COUNTRIES).forEach(code => {
            if (!countryData[code]) {
                countryData[code] = generateMockCountryData(code);
            }
        });

    } catch (error) {
        console.error('Error loading country data:', error);
        showNotification('Error loading data. Using sample data.');
    }
}

// Generate mock data for countries
function generateMockCountryData(countryCode) {
    const baseValues = {
        'CN': { multiplier: 2.1, employment: 1.8, water: 1.4 },
        'DE': { multiplier: 0.8, employment: 0.6, water: 0.3 },
        'JP': { multiplier: 0.9, employment: 0.5, water: 0.4 },
        'GB': { multiplier: 0.7, employment: 0.4, water: 0.2 },
        'FR': { multiplier: 0.6, employment: 0.5, water: 0.3 },
        'IT': { multiplier: 0.5, employment: 0.7, water: 0.4 },
        'CA': { multiplier: 0.4, employment: 0.3, water: 0.5 },
        'BR': { multiplier: 0.6, employment: 1.2, water: 0.8 },
        'AU': { multiplier: 0.3, employment: 0.2, water: 0.6 },
        'KR': { multiplier: 0.8, employment: 0.9, water: 0.5 }
    };

    const base = baseValues[countryCode] || { multiplier: 0.5, employment: 0.5, water: 0.5 };
    const usData = countryData['US'] || {
        tradeFlows: 188735,
        factorRelationships: 125148,
        airEmissions: 49177,
        employment: 4121,
        energy: 51907,
        land: 7170,
        materials: 6853,
        water: 5920
    };

    return {
        tradeFlows: Math.round(usData.tradeFlows * base.multiplier),
        factorRelationships: Math.round(usData.factorRelationships * base.multiplier),
        airEmissions: Math.round(usData.airEmissions * base.multiplier),
        employment: Math.round(usData.employment * base.employment),
        energy: Math.round(usData.energy * base.multiplier),
        land: Math.round(usData.land * base.multiplier),
        materials: Math.round(usData.materials * base.multiplier),
        water: Math.round(usData.water * base.water)
    };
}

// Get mock data for a country
function getCountryMockData(countryCode) {
    const data = countryData[countryCode];
    if (!data) return { tradeFlows: 0, factorRelationships: 0, employmentIntensity: 0 };
    
    const employmentIntensity = data.employment / (data.tradeFlows / 1000);
    return {
        ...data,
        employmentIntensity: employmentIntensity.toFixed(1)
    };
}

// Update country panels
function updateCountryPanels() {
    const panelGrid = document.getElementById('panel-grid');
    panelGrid.innerHTML = '';
    
    const selectedCountriesArray = Array.from(selectedCountries);
    
    // Calculate grid columns based on number of countries
    const columns = Math.min(selectedCountriesArray.length, 4);
    panelGrid.style.gridTemplateColumns = `repeat(${columns}, 1fr)`;
    
    selectedCountriesArray.forEach(countryCode => {
        const country = COUNTRIES[countryCode];
        const data = countryData[countryCode];
        
        const panel = document.createElement('div');
        panel.className = 'country-panel';
        panel.style.setProperty('--country-color', country.color);
        
        panel.innerHTML = `
            <div class="panel-header">
                <span class="panel-flag">${country.flag}</span>
                <div class="panel-info">
                    <h3>${country.name}</h3>
                    <p>Export Trade Analysis 2019</p>
                </div>
            </div>
            <div class="panel-metrics">
                <div class="metric-card">
                    <span class="metric-value">${data.tradeFlows.toLocaleString()}</span>
                    <span class="metric-label">Trade Flows</span>
                </div>
                <div class="metric-card">
                    <span class="metric-value">${data.factorRelationships.toLocaleString()}</span>
                    <span class="metric-label">Environmental Factors</span>
                </div>
                <div class="metric-card">
                    <span class="metric-value">${data.airEmissions.toLocaleString()}</span>
                    <span class="metric-label">Air Emissions</span>
                </div>
                <div class="metric-card">
                    <span class="metric-value">${data.employment.toLocaleString()}</span>
                    <span class="metric-label">Employment</span>
                </div>
            </div>
        `;
        
        panelGrid.appendChild(panel);
    });
}

// Setup event listeners
function setupEventListeners() {
    // Tab navigation
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const category = btn.dataset.category;
            switchTab(category);
        });
    });

    // Map expand button
    document.getElementById('expand-map').addEventListener('click', () => {
        const mapElement = document.getElementById('map');
        mapElement.classList.toggle('expanded');
        
        // Resize map after animation
        setTimeout(() => {
            map.invalidateSize();
        }, 500);
    });

    // Update selection count
    updateSelectionCount();
}

// Switch between chart tabs
function switchTab(category) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-category="${category}"]`).classList.add('active');

    // Update chart sections
    document.querySelectorAll('.chart-section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(`${category}-section`).classList.add('active');

    // Update charts for the active section
    updateChartsForCategory(category);
}

// Initialize all charts
function initializeCharts() {
    // Initialize charts for the active tab (air emissions by default)
    updateChartsForCategory('air');
}

// Update charts for specific category
function updateChartsForCategory(category) {
    switch(category) {
        case 'air':
            createAirEmissionsCharts();
            break;
        case 'water':
            createWaterCharts();
            break;
        case 'land':
            createLandCharts();
            break;
        case 'energy':
            createEnergyCharts();
            break;
        case 'material':
            createMaterialCharts();
            break;
        case 'employment':
            createEmploymentCharts();
            break;
    }
}

// Create air emissions charts
function createAirEmissionsCharts() {
    // Air Emissions Comparison Chart
    const ctx1 = document.getElementById('air-emissions-comparison');
    if (charts.airComparison) charts.airComparison.destroy();
    
    const selectedData = Array.from(selectedCountries).map(code => ({
        country: COUNTRIES[code].name,
        value: countryData[code].airEmissions,
        color: COUNTRIES[code].color,
        flag: COUNTRIES[code].flag
    }));

    charts.airComparison = new Chart(ctx1, {
        type: 'bar',
        data: {
            labels: selectedData.map(d => `${d.flag} ${d.country}`),
            datasets: [{
                label: 'Air Emission Factors',
                data: selectedData.map(d => d.value),
                backgroundColor: selectedData.map(d => d.color + '80'),
                borderColor: selectedData.map(d => d.color),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Air Emissions Impact Comparison',
                    font: { size: 16, weight: 'bold' }
                },
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Factor Relationships'
                    }
                }
            }
        }
    });

    // CO2 Breakdown Chart
    const ctx2 = document.getElementById('co2-breakdown');
    if (charts.co2Breakdown) charts.co2Breakdown.destroy();
    
    charts.co2Breakdown = new Chart(ctx2, {
        type: 'doughnut',
        data: {
            labels: ['Combustion CO2', 'Process CO2', 'Biogenic CO2'],
            datasets: [{
                data: [65, 25, 10],
                backgroundColor: ['#e74c3c', '#f39c12', '#27ae60'],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'CO2 Emissions Breakdown',
                    font: { size: 16, weight: 'bold' }
                }
            }
        }
    });

    // Air Pollutants Radar Chart
    const ctx3 = document.getElementById('air-pollutants-radar');
    if (charts.airRadar) charts.airRadar.destroy();
    
    const radarData = Array.from(selectedCountries).slice(0, 2).map(code => ({
        label: `${COUNTRIES[code].flag} ${COUNTRIES[code].name}`,
        data: [
            Math.random() * 100, // CO2
            Math.random() * 100, // CH4
            Math.random() * 100, // N2O
            Math.random() * 100, // NOX
            Math.random() * 100, // SO2
            Math.random() * 100  // PM2.5
        ],
        borderColor: COUNTRIES[code].color,
        backgroundColor: COUNTRIES[code].color + '30'
    }));

    charts.airRadar = new Chart(ctx3, {
        type: 'radar',
        data: {
            labels: ['CO2', 'CH4', 'N2O', 'NOX', 'SO2', 'PM2.5'],
            datasets: radarData
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Air Pollutants Profile',
                    font: { size: 16, weight: 'bold' }
                }
            },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });

    // Emissions Timeline
    const ctx4 = document.getElementById('emissions-timeline');
    if (charts.emissionsTimeline) charts.emissionsTimeline.destroy();
    
    const timelineData = Array.from(selectedCountries).map(code => ({
        label: `${COUNTRIES[code].flag} ${COUNTRIES[code].name}`,
        data: [
            Math.random() * 50000 + 30000,
            Math.random() * 50000 + 35000,
            Math.random() * 50000 + 40000,
            countryData[code].airEmissions,
            Math.random() * 50000 + 45000
        ],
        borderColor: COUNTRIES[code].color,
        backgroundColor: COUNTRIES[code].color + '20',
        tension: 0.4
    }));

    charts.emissionsTimeline = new Chart(ctx4, {
        type: 'line',
        data: {
            labels: ['2015', '2016', '2017', '2018', '2019'],
            datasets: timelineData
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Air Emissions Trend (2015-2019)',
                    font: { size: 16, weight: 'bold' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Emission Factors'
                    }
                }
            }
        }
    });
}

// Create water charts
function createWaterCharts() {
    // Water Usage Comparison
    const ctx1 = document.getElementById('water-usage-comparison');
    if (charts.waterComparison) charts.waterComparison.destroy();
    
    const selectedData = Array.from(selectedCountries).map(code => ({
        country: COUNTRIES[code].name,
        consumption: countryData[code].water * 0.6,
        withdrawal: countryData[code].water * 0.4,
        color: COUNTRIES[code].color,
        flag: COUNTRIES[code].flag
    }));

    charts.waterComparison = new Chart(ctx1, {
        type: 'bar',
        data: {
            labels: selectedData.map(d => `${d.flag} ${d.country}`),
            datasets: [
                {
                    label: 'Water Consumption',
                    data: selectedData.map(d => d.consumption),
                    backgroundColor: '#3498db80',
                    borderColor: '#3498db',
                    borderWidth: 2
                },
                {
                    label: 'Water Withdrawal',
                    data: selectedData.map(d => d.withdrawal),
                    backgroundColor: '#2980b980',
                    borderColor: '#2980b9',
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Water Usage Patterns by Country',
                    font: { size: 16, weight: 'bold' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    stacked: true,
                    title: {
                        display: true,
                        text: 'Water Factor Relationships'
                    }
                },
                x: { stacked: true }
            }
        }
    });

    // Water Intensity by Sectors
    const ctx2 = document.getElementById('water-intensity-sectors');
    if (charts.waterSectors) charts.waterSectors.destroy();
    
    charts.waterSectors = new Chart(ctx2, {
        type: 'horizontalBar',
        data: {
            labels: ['Textiles', 'Agriculture', 'Food Processing', 'Chemicals', 'Electronics'],
            datasets: [{
                label: 'Water Intensity',
                data: [85, 92, 45, 38, 15],
                backgroundColor: ['#e74c3c', '#f39c12', '#27ae60', '#3498db', '#9b59b6']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Water Intensity by Export Sectors',
                    font: { size: 16, weight: 'bold' }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Water Intensity Index'
                    }
                }
            }
        }
    });

    // Water Stress Indicator
    const ctx3 = document.getElementById('water-stress-indicator');
    if (charts.waterStress) charts.waterStress.destroy();
    
    const stressData = Array.from(selectedCountries).map(code => {
        const stress = code === 'IN' ? 75 : code === 'US' ? 45 : Math.random() * 80 + 20;
        return {
            country: COUNTRIES[code].name,
            stress: stress,
            color: stress > 60 ? '#e74c3c' : stress > 40 ? '#f39c12' : '#27ae60'
        };
    });

    charts.waterStress = new Chart(ctx3, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Water Stress Level',
                data: stressData.map((d, i) => ({ x: i, y: d.stress })),
                backgroundColor: stressData.map(d => d.color),
                borderColor: stressData.map(d => d.color),
                pointRadius: 8
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Water Stress Risk Assessment',
                    font: { size: 16, weight: 'bold' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Water Stress Index (%)'
                    }
                },
                x: {
                    type: 'linear',
                    position: 'bottom',
                    ticks: {
                        callback: function(value, index) {
                            return stressData[index]?.country || '';
                        }
                    }
                }
            }
        }
    });

    // Water Efficiency Trends
    const ctx4 = document.getElementById('water-efficiency-trends');
    if (charts.waterEfficiency) charts.waterEfficiency.destroy();
    
    const efficiencyData = Array.from(selectedCountries).map(code => ({
        label: `${COUNTRIES[code].flag} ${COUNTRIES[code].name}`,
        data: [
            Math.random() * 20 + 60,
            Math.random() * 20 + 65,
            Math.random() * 20 + 70,
            Math.random() * 20 + 75,
            Math.random() * 20 + 80
        ],
        borderColor: COUNTRIES[code].color,
        backgroundColor: COUNTRIES[code].color + '20',
        tension: 0.4
    }));

    charts.waterEfficiency = new Chart(ctx4, {
        type: 'line',
        data: {
            labels: ['2015', '2016', '2017', '2018', '2019'],
            datasets: efficiencyData
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Water Use Efficiency Trends',
                    font: { size: 16, weight: 'bold' }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    min: 50,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Efficiency Index (%)'
                    }
                }
            }
        }
    });
}

// Similar functions for other categories (land, energy, material, employment)
// ... (implementation would be similar to above patterns)

// Create placeholder charts for other categories
function createLandCharts() {
    console.log('Creating land use charts...');
    // Implementation similar to air and water charts
}

function createEnergyCharts() {
    console.log('Creating energy charts...');
    // Implementation similar to air and water charts
}

function createMaterialCharts() {
    console.log('Creating material charts...');
    // Implementation similar to air and water charts
}

function createEmploymentCharts() {
    // Employment Comparison
    const ctx1 = document.getElementById('employment-comparison');
    if (charts.employmentComparison) charts.employmentComparison.destroy();
    
    const selectedData = Array.from(selectedCountries).map(code => ({
        country: COUNTRIES[code].name,
        people: countryData[code].employment * 0.7,
        hours: countryData[code].employment * 0.3,
        color: COUNTRIES[code].color,
        flag: COUNTRIES[code].flag
    }));

    charts.employmentComparison = new Chart(ctx1, {
        type: 'bar',
        data: {
            labels: selectedData.map(d => `${d.flag} ${d.country}`),
            datasets: [
                {
                    label: 'Employment People',
                    data: selectedData.map(d => d.people),
                    backgroundColor: '#27ae6080',
                    borderColor: '#27ae60',
                    borderWidth: 2
                },
                {
                    label: 'Employment Hours',
                    data: selectedData.map(d => d.hours),
                    backgroundColor: '#2ecc7180',
                    borderColor: '#2ecc71',
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Employment Impact by Country',
                    font: { size: 16, weight: 'bold' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Employment Factor Relationships'
                    }
                }
            }
        }
    });
}

// Update all charts when countries change
function updateCharts() {
    const activeTab = document.querySelector('.tab-btn.active').dataset.category;
    updateChartsForCategory(activeTab);
}

// Update selection count
function updateSelectionCount() {
    document.getElementById('selected-count').textContent = selectedCountries.size;
}

// Apply Motion.dev animations
function applyAnimations() {
    // Animate hero section
    Motion.animate('.hero-title', 
        { opacity: [0, 1], y: [50, 0] },
        { duration: 1, delay: 0 }
    );
    
    Motion.animate('.hero-subtitle', 
        { opacity: [0, 1], y: [30, 0] },
        { duration: 0.8, delay: 0.2 }
    );
    
    Motion.animate('.sdg-badge', 
        { opacity: [0, 1], scale: [0.5, 1] },
        { duration: 0.6, delay: Motion.stagger(0.1, { start: 0.4 }) }
    );

    // Animate country panels
    Motion.animate('.country-panel', 
        { opacity: [0, 1], y: [30, 0] },
        { duration: 0.8, delay: Motion.stagger(0.1) }
    );

    // Animate summary cards
    Motion.animate('.summary-card', 
        { opacity: [0, 1], x: [-50, 0] },
        { duration: 0.8, delay: Motion.stagger(0.1, { start: 0.3 }) }
    );

    // Animate insight cards
    Motion.animate('.insight-card', 
        { opacity: [0, 1], scale: [0.8, 1] },
        { duration: 0.8, delay: Motion.stagger(0.2, { start: 0.5 }) }
    );
}

// Show notification
function showNotification(message) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #3498db;
        color: white;
        padding: 1rem 2rem;
        border-radius: 10px;
        z-index: 1000;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Utility function to format numbers
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}