// static/js/main.js

class ConsultantApp {
    constructor() {
        this.map = null;
        this.userMarker = null;
        this.consultantMarkers = [];
        this.consultants = [];
        this.userLocation = JSON.parse(localStorage.getItem('userLocation')) || { lat: 23.0225, lng: 72.5714 }; // Default Ahmedabad
        this.markerCluster = null;

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeUserLocation();
    }

    setupEventListeners() {
        const debounce = (func, wait) => {
            let timeout;
            return (...args) => {
                clearTimeout(timeout);
                timeout = setTimeout(() => func.apply(this, args), wait);
            };
        };

        document.getElementById('searchInput').addEventListener('input', debounce(() => this.fetchConsultants(), 300));
        document.getElementById('specialtyFilter').addEventListener('change', () => this.fetchConsultants());
        document.getElementById('availabilityFilter').addEventListener('change', () => this.fetchConsultants());
        document.getElementById('ratingFilter').addEventListener('change', () => this.fetchConsultants());
        document.getElementById('clearFilters').addEventListener('click', () => this.clearFilters());
        document.getElementById('locateBtn').addEventListener('click', () => this.getCurrentLocation());
        document.getElementById('manualLocation').addEventListener('change', () => this.setManualLocation());
        // Remove closeModal and bookingForm event listeners here since they are dynamic
    }

    async setManualLocation() {
        const input = document.getElementById('manualLocation').value;
        if (!input) return;

        try {
            const response = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(input)}&format=json&limit=1`);
            const data = await response.json();
            if (data.length === 0) {
                this.showNotification('Location not found. Please try again.', 'error');
                return;
            }

            this.userLocation = {
                lat: parseFloat(data[0].lat),
                lng: parseFloat(data[0].lon)
            };
            localStorage.setItem('userLocation', JSON.stringify(this.userLocation));
            this.updateMap();
            this.fetchConsultants();
        } catch (error) {
            console.error('Manual location error:', error);
            this.showNotification('Failed to fetch location. Please try again.', 'error');
        }
    }

    initializeUserLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                position => {
                    this.userLocation = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    };
                    localStorage.setItem('userLocation', JSON.stringify(this.userLocation));
                    this.initMap();
                    this.fetchConsultants();
                },
                error => {
                    console.error('Geolocation error:', error);
                    this.showNotification('Unable to get your location. Using default location (Ahmedabad).', 'warning');
                    this.initMap();
                    this.fetchConsultants();
                },
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
            );
        } else {
            console.error('Geolocation not supported');
            this.showNotification('Geolocation not supported. Using default location (Ahmedabad).', 'warning');
            this.initMap();
            this.fetchConsultants();
        }
    }

    initMap() {
        document.getElementById('loadingMap').style.display = 'flex';
        
        this.map = L.map('map').setView([this.userLocation.lat, this.userLocation.lng], 12);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(this.map);
        
        // Custom user marker
        const userIcon = this.createUserIcon();
        this.userMarker = L.marker([this.userLocation.lat, this.userLocation.lng], { icon: userIcon })
            .addTo(this.map)
            .bindPopup('<div class="p-2"><h3 class="font-semibold text-gray-800">📍 You are here</h3><p class="text-sm text-gray-600">Your current location</p></div>')
            .openPopup();
        
        // Initialize marker cluster
        this.markerCluster = L.markerClusterGroup();
        this.map.addLayer(this.markerCluster);
        
        document.getElementById('loadingMap').style.display = 'none';
    }

    createUserIcon() {
        return L.divIcon({
            className: 'custom-user-marker',
            html: `
                <div style="
                    width: 40px; 
                    height: 40px; 
                    background: linear-gradient(135deg, #3b82f6, #1d4ed8);
                    border: 3px solid white;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
                    animation: pulse 2s infinite;
                ">
                    <div style="color: white; font-size: 16px;">📍</div>
                </div>
            `,
            iconSize: [40, 40],
            iconAnchor: [20, 40],
        });
    }

    createConsultantIcon(is_online = false) {
        const color = is_online ? '#10b981' : '#6366f1';
        const bgColor = is_online ? '#dcfce7' : '#e0e7ff';
        
        return L.divIcon({
            className: 'custom-consultant-marker',
            html: `
                <div style="
                    width: 36px; 
                    height: 36px; 
                    background: ${bgColor};
                    border: 2px solid ${color};
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
                    position: relative;
                ">
                    <div style="color: ${color}; font-size: 14px;">👨‍⚕️</div>
                    ${is_online ? `
                        <div style="
                            position: absolute;
                            top: -2px;
                            right: -2px;
                            width: 12px;
                            height: 12px;
                            background: #10b981;
                            border: 2px solid white;
                            border-radius: 50%;
                        "></div>
                    ` : ''}
                </div>
            `,
            iconSize: [36, 36],
            iconAnchor: [18, 36],
        });
    }

    async fetchConsultants() {
        try {
            const params = new URLSearchParams({
                search: document.getElementById('searchInput').value,
                specialty: document.getElementById('specialtyFilter').value,
                availability: document.getElementById('availabilityFilter').value,
                rating: document.getElementById('ratingFilter').value,
                lat: this.userLocation.lat,
                lng: this.userLocation.lng
            });
            
            const response = await fetch(`/consultants/api/consultants/?${params}`);
            const data = await response.json();
            
            this.consultants = data.consultants;
            this.updateMapMarkers();
            this.updateConsultantsList();
        } catch (error) {
            console.error('Error fetching consultants:', error);
            this.showNotification('Failed to fetch consultants. Showing cached results.', 'error');
            
            // Client-side filtering fallback
            this.updateConsultantsList(true);
        }
    }

    updateMapMarkers() {
        // Clear existing markers
        this.markerCluster.clearLayers();
        this.consultantMarkers = [];
        
        this.consultants.forEach(consultant => {
            const marker = L.marker([consultant.lat, consultant.lng], {
                icon: this.createConsultantIcon(consultant.is_online)
            });
            
            marker.bindPopup(this.createPopupContent(consultant));
            marker.consultant = consultant;
            
            this.markerCluster.addLayer(marker);
            this.consultantMarkers.push(marker);
        });
    }

    createPopupContent(consultant) {
        return `
            <div class="p-4 bg-white text-gray-800 rounded-lg max-w-xs">
                <div class="flex items-start gap-3 mb-3">
                    <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                        <i class="fas fa-user-md text-white text-lg"></i>
                    </div>
                    <div class="flex-1">
                        <h4 class="font-bold text-lg text-gray-800">${consultant.name}</h4>
                        <p class="text-blue-600 font-medium flex items-center gap-1">
                            <i class="fas fa-stethoscope text-sm"></i>
                            ${consultant.specialty}
                        </p>
                    </div>
                    ${consultant.is_online ? `
                        <div class="flex items-center gap-1 text-green-600 text-xs">
                            <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                            Online
                        </div>
                    ` : ''}
                </div>
                
                <div class="space-y-2 mb-4">
                    <div class="flex items-center justify-between text-sm">
                        <span class="flex items-center gap-1 text-yellow-600">
                            <i class="fas fa-star"></i>
                            ${consultant.rating} ⭐
                        </span>
                        <span class="flex items-center gap-1 text-green-600">
                            <i class="fas fa-calendar-check"></i>
                            ${consultant.availability}
                        </span>
                    </div>
                    <p class="text-sm text-gray-600 flex items-center gap-1">
                        <i class="fas fa-map-marker-alt text-gray-400"></i>
                        ${consultant.distance}
                    </p>
                    <p class="text-xs text-gray-500 italic leading-relaxed">
                        ${consultant.bio}
                    </p>
                </div>
                
                <div class="flex gap-2">
                    <button onclick="app.openBookingModal(${consultant.id})" 
                        class="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg font-medium transition-colors text-sm">
                        Book Session
                    </button>
                    <button class="px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors">
                        <i class="fas fa-video"></i>
                    </button>
                </div>
            </div>
        `;
    }

    updateConsultantsList(fallback = false) {
        const list = document.getElementById('consultantsList');
        const countEl = document.getElementById('resultsCount');
        
        if (this.consultants.length === 0) {
            list.innerHTML = '<p class="text-muted-foreground text-center py-4">No consultants found. Try adjusting filters.</p>';
            countEl.textContent = '0';
            return;
        }
        
        countEl.textContent = this.consultants.length;
        
        list.innerHTML = this.consultants.map((consultant, index) => `
            <div class="consultant-card p-3 rounded-lg cursor-pointer transition-all duration-200 animate-slide-up" 
                 style="animation-delay: ${index * 0.05}s;" 
                 onclick="app.zoomToConsultant(${consultant.lat}, ${consultant.lng})">
                <div class="flex items-center gap-3 mb-2">
                    <div class="w-10 h-10 bg-gradient-to-br from-primary to-blue-500 rounded-full flex items-center justify-center">
                        <i class="fas fa-user-md text-white"></i>
                    </div>
                    <div>
                        <h4 class="font-semibold text-foreground">${consultant.name}</h4>
                        <p class="text-sm text-primary">${consultant.specialty}</p>
                    </div>
                </div>
                <div class="flex justify-between items-center text-sm">
                    <span class="text-yellow-400"><i class="fas fa-star mr-1"></i>${consultant.rating}</span>
                    <span class="text-green-400"><i class="fas fa-calendar-check mr-1"></i>${consultant.availability}</span>
                </div>
                <p class="text-xs text-muted-foreground mt-1"><i class="fas fa-map-marker-alt mr-1"></i>${consultant.distance}</p>
            </div>
        `).join('');
    }

    zoomToConsultant(lat, lng) {
        this.map.setView([lat, lng], 15);
        const marker = this.consultantMarkers.find(m => 
            m.consultant.lat === lat && m.consultant.lng === lng
        );
        if (marker) {
            marker.openPopup();
        }
    }

    getCurrentLocation() {
        const btn = document.getElementById('locateBtn');
        btn.innerHTML = '<div class="loading mr-2"></div> Locating...';
        btn.disabled = true;
        
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                position => {
                    this.userLocation.lat = position.coords.latitude;
                    this.userLocation.lng = position.coords.longitude;
                    
                    this.map.setView([this.userLocation.lat, this.userLocation.lng], 13);
                    
                    if (this.userMarker) {
                        this.map.removeLayer(this.userMarker);
                    }
                    
                    const userIcon = this.createUserIcon();
                    this.userMarker = L.marker([this.userLocation.lat, this.userLocation.lng], { icon: userIcon })
                        .addTo(this.map)
                        .bindPopup('<div class="p-2"><h3 class="font-semibold text-gray-800">📍 You are here</h3><p class="text-sm text-gray-600">Your current location</p></div>')
                        .openPopup();
                    
                    this.fetchConsultants();
                    btn.innerHTML = '<i class="fas fa-location-arrow"></i> Find Nearby Experts';
                    btn.disabled = false;
                },
                error => {
                    console.error('Geolocation error:', error);
                    this.showNotification('Unable to get location. Using current location.', 'warning');
                    btn.innerHTML = '<i class="fas fa-location-arrow"></i> Find Nearby Experts';
                    btn.disabled = false;
                },
                { timeout: 10000 }
            );
        } else {
            this.showNotification('Geolocation not supported.', 'error');
            btn.innerHTML = '<i class="fas fa-location-arrow"></i> Find Nearby Experts';
            btn.disabled = false;
        }
    }

    clearFilters() {
        document.getElementById('searchInput').value = '';
        document.getElementById('specialtyFilter').value = 'All';
        document.getElementById('availabilityFilter').value = 'All';
        document.getElementById('ratingFilter').value = 'All';
        this.fetchConsultants();
    }

    openBookingModal(consultantId) {
        const consultant = this.consultants.find(c => c.id === consultantId);
        if (!consultant) return;
        
        const modal = document.createElement('div');
        modal.id = 'bookingModal';
        modal.className = 'fixed inset-0 bg-black/50 flex items-center justify-center z-50';
        modal.onclick = (e) => {
            if (e.target === modal) {
                this.closeBookingModal();
            }
        };
        
        modal.innerHTML = `
            <div class="bg-card border border-border p-6 rounded-xl max-w-md w-full m-4 animate-scale-in" onclick="event.stopPropagation()">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-xl font-bold text-foreground">Book Session with ${consultant.name}</h3>
                    <button id="closeModal" class="text-muted-foreground hover:text-foreground">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <p class="text-muted-foreground mb-4">Specialty: ${consultant.specialty}</p>
                
                <form id="bookingForm" class="space-y-4 mb-6">
                    <div>
                        <label class="block text-sm font-medium text-foreground mb-1">Session Type</label>
                        <select name="sessionType" class="select-custom w-full rounded-lg px-3 py-2" required>
                            <option value="Virtual">Virtual Session</option>
                            <option value="In-Person">In-Person</option>
                            <option value="Hybrid">Hybrid</option>
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-foreground mb-1">Date & Time</label>
                        <input type="datetime-local" name="dateTime" class="select-custom w-full rounded-lg px-3 py-2" required />
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-foreground mb-1">Email</label>
                        <input type="email" name="email" placeholder="your@email.com" class="select-custom w-full rounded-lg px-3 py-2" required />
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-foreground mb-1">Phone</label>
                        <input type="tel" name="phone" placeholder="+1 (555) 123-4567" class="select-custom w-full rounded-lg px-3 py-2" required />
                    </div>
                </form>
                
                <button onclick="app.submitBooking(${consultant.id})" class="btn-primary w-full py-3 rounded-lg font-semibold">
                    Confirm Booking
                </button>
            </div>
        `;
        
        document.body.appendChild(modal);

        // Attach event listener to closeModal after it's created
        document.getElementById('closeModal').addEventListener('click', () => this.closeBookingModal());
        // Attach event listener to bookingForm after it's created
        document.getElementById('bookingForm').addEventListener('submit', (e) => this.submitBooking(e));
    }

    closeBookingModal() {
        const modal = document.getElementById('bookingModal');
        if (modal) modal.remove();
    }
    
    async submitBooking(e) {
        e.preventDefault(); // Prevent form submission if not handled by fetch
        const form = document.getElementById('bookingForm');
        const formData = new FormData(form);
        
        const bookingData = {
            consultant_id: e.target.dataset.consultantId || form.closest('[data-consultant-id]').dataset.consultantId,
            session_type: formData.get('sessionType'),
            date_time: formData.get('dateTime'),
            email: formData.get('email'),
            phone: formData.get('phone')
        };
        
        try {
            const response = await fetch('/consultants/api/book/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(bookingData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification(result.message, 'success');
                this.closeBookingModal();
            } else {
                this.showNotification(result.message, 'error');
            }
        } catch (error) {
            console.error('Booking error:', error);
            this.showNotification('Booking failed. Please try again.', 'error');
        }
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `
            fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm animate-slide-in-right
            ${type === 'success' ? 'bg-green-600 text-white' : 
              type === 'error' ? 'bg-red-600 text-white' : 
              type === 'warning' ? 'bg-yellow-600 text-white' : 
              'bg-blue-600 text-white'}
        `;
        
        notification.innerHTML = `
            <div class="flex items-center gap-2">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 
                                   type === 'error' ? 'exclamation-circle' : 
                                   type === 'warning' ? 'exclamation-triangle' : 
                                   'info-circle'}"></i>
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-auto">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
}

// Initialize the app when DOM is loaded
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new ConsultantApp();
});