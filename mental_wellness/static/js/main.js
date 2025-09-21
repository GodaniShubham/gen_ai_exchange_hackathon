document.addEventListener('DOMContentLoaded', () => {
    const map = L.map('map').setView([23.0225, 72.5714], 12); // Ahmedabad coordinates
    const markers = L.markerClusterGroup();
    let consultantsData = [];

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    const loadingMap = document.getElementById('loadingMap');
    loadingMap.style.display = 'none';

    const consultantsList = document.getElementById('consultantsList');
    const resultsCount = document.getElementById('resultsCount');
    const searchInput = document.getElementById('searchInput');
    const manualLocation = document.getElementById('manualLocation');
    const specialtyFilter = document.getElementById('specialtyFilter');
    const availabilityFilter = document.getElementById('availabilityFilter');
    const ratingFilter = document.getElementById('ratingFilter');
    const clearFilters = document.getElementById('clearFilters');
    const locateBtn = document.getElementById('locateBtn');

    // Add modal HTML dynamically
    const modal = document.createElement('div');
    modal.id = 'bookingModal';
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center hidden z-50';
    modal.innerHTML = `
        <div class="bg-card p-6 rounded-lg w-full max-w-md">
            <h2 class="text-xl font-bold mb-4">Book Consultation</h2>
            <form id="bookingForm">
                <input type="hidden" id="consultantId" name="consultant_id">
                <div class="mb-4">
                    <label class="block text-sm text-muted-foreground mb-1">Session Type</label>
                    <select name="session_type" class="select-custom w-full rounded-lg px-3 py-2">
                        <option value="virtual">Virtual</option>
                        <option value="in-person">In-Person</option>
                        <option value="hybrid">Hybrid</option>
                    </select>
                </div>
                <div class="mb-4">
                    <label class="block text-sm text-muted-foreground mb-1">Date & Time</label>
                    <input type="datetime-local" name="date_time" class="select-custom w-full rounded-lg px-3 py-2" required>
                </div>
                <div class="mb-4">
                    <label class="block text-sm text-muted-foreground mb-1">Email</label>
                    <input type="email" name="email" class="select-custom w-full rounded-lg px-3 py-2" placeholder="your@email.com" required>
                </div>
                <div class="mb-4">
                    <label class="block text-sm text-muted-foreground mb-1">Phone</label>
                    <input type="tel" name="phone" class="select-custom w-full rounded-lg px-3 py-2" placeholder="+919876543210" required>
                </div>
                <div class="flex justify-end gap-2">
                    <button type="button" id="closeModal" class="px-4 py-2 rounded-lg bg-transparent border border-border text-muted-foreground hover:bg-muted">Cancel</button>
                    <button type="submit" class="btn-primary px-4 py-2 rounded-lg">Confirm Booking</button>
                </div>
            </form>
        </div>
    `;
    document.body.appendChild(modal);

    function fetchConsultants(lat = 23.0225, lng = 72.5714) {
        loadingMap.style.display = 'flex';
        markers.clearLayers();
        consultantsList.innerHTML = '';

        fetch(`/consultants/?lat=${lat}&lng=${lng}&search=${searchInput.value}&specialty=${specialtyFilter.value}&availability=${availabilityFilter.value}&rating=${ratingFilter.value}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    consultantsData = data.consultants;
                    resultsCount.textContent = consultantsData.length;
                    displayConsultants();
                    addMarkers();
                } else {
                    consultantsList.innerHTML = '<p class="text-muted-foreground">No consultants found.</p>';
                }
            })
            .catch(error => {
                console.error('Error fetching consultants:', error);
                consultantsList.innerHTML = '<p class="text-muted-foreground">Error loading consultants.</p>';
            })
            .finally(() => {
                loadingMap.style.display = 'none';
            });
    }

    function displayConsultants() {
        consultantsList.innerHTML = '';
        consultantsData.forEach(consultant => {
            const card = document.createElement('div');
            card.className = 'consultant-card p-4 rounded-lg mb-4';
            card.innerHTML = `
                <h4 class="font-semibold text-foreground">${consultant.name}</h4>
                <p class="text-sm text-muted-foreground">Specialty: ${consultant.specialty}</p>
                <p class="text-sm text-muted-foreground">Availability: ${consultant.availability}</p>
                <p class="text-sm text-muted-foreground">Rating: ${consultant.rating.toFixed(1)} / 5</p>
                <p class="text-sm text-muted-foreground">Distance: ${consultant.distance}</p>
                <p class="text-sm text-muted-foreground">${consultant.bio}</p>
                <button class="btn-primary mt-2 px-4 py-2 rounded-lg book-btn" data-id="${consultant.id}">
                    <i class="fas fa-calendar-check"></i> Book
                </button>
            `;
            consultantsList.appendChild(card);
        });

        document.querySelectorAll('.book-btn').forEach(button => {
            button.addEventListener('click', () => openBookingModal(button.getAttribute('data-id')));
        });
    }

    function addMarkers() {
        consultantsData.forEach(consultant => {
            const marker = L.marker([consultant.latitude, consultant.longitude]).bindPopup(`
                <b>${consultant.name}</b><br>
                Specialty: ${consultant.specialty}<br>
                Rating: ${consultant.rating.toFixed(1)} / 5<br>
                Distance: ${consultant.distance}<br>
                <button class="btn-primary mt-2 px-4 py-2 rounded-lg book-btn" data-id="${consultant.id}">
                    <i class="fas fa-calendar-check"></i> Book
                </button>
            `);
            markers.addLayer(marker);

            marker.on('popupopen', () => {
                document.querySelectorAll('.book-btn').forEach(btn => {
                    btn.addEventListener('click', () => openBookingModal(btn.getAttribute('data-id')));
                });
            });
        });
        map.addLayer(markers);
    }

    function openBookingModal(consultantId) {
        const modal = document.getElementById('bookingModal');
        const form = document.getElementById('bookingForm');
        const consultantIdInput = document.getElementById('consultantId');

        consultantIdInput.value = consultantId;
        modal.classList.remove('hidden');

        document.getElementById('closeModal').addEventListener('click', () => modal.classList.add('hidden'));
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            const data = {
                consultant_id: consultantIdInput.value,
                session_type: formData.get('session_type'),
                date_time: formData.get('date_time'),
                email: formData.get('email'),
                phone: formData.get('phone')
            };

            fetch('/book/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                if (data.success) modal.classList.add('hidden');
            })
            .catch(error => {
                console.error('Booking error:', error);
                alert('Failed to book consultation.');
            });
        });
    }

    // Helper function to get CSRF token (for Django)
    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]') ? document.querySelector('[name=csrfmiddlewaretoken]').value : '';
    }

    // Event listeners
    [searchInput, manualLocation, specialtyFilter, availabilityFilter, ratingFilter].forEach(element => {
        element.addEventListener('change', () => fetchConsultants(23.0225, 72.5714));
    });

    clearFilters.addEventListener('click', () => {
        searchInput.value = '';
        manualLocation.value = '';
        specialtyFilter.value = 'All';
        availabilityFilter.value = 'All';
        ratingFilter.value = 'All';
        fetchConsultants(23.0225, 72.5714);
    });

    locateBtn.addEventListener('click', () => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                position => fetchConsultants(position.coords.latitude, position.coords.longitude),
                () => fetchConsultants(23.0225, 72.5714)
            );
        } else {
            fetchConsultants(23.0225, 72.5714);
        }
    });

    // Initial fetch
    fetchConsultants(23.0225, 72.5714);
});