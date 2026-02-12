// Category Page JavaScript - Filtering and Sorting

document.addEventListener('DOMContentLoaded', function() {
    const agentGrid = document.getElementById('agent-grid');
    const agentCards = Array.from(document.querySelectorAll('.agent-card'));
    
    // Filters
    const sortSelect = document.getElementById('sort-select');
    const priceRange = document.getElementById('price-range');
    const priceDisplay = document.getElementById('price-display');
    const ratingFilter = document.getElementById('rating-filter');
    const verifiedOnly = document.getElementById('verified-only');
    const protocolFilter = document.getElementById('protocol-filter');
    const clearFilters = document.getElementById('clear-filters');
    const resultsCount = document.getElementById('results-count');
    const agentSearch = document.getElementById('agent-search');
    
    // View toggle
    const viewButtons = document.querySelectorAll('.view-btn');
    
    // Price range display
    priceRange.addEventListener('input', function() {
        priceDisplay.textContent = `$${this.value}/mo`;
    });
    
    // Apply filters
    function applyFilters() {
        const maxPrice = parseInt(priceRange.value);
        const minRating = parseFloat(ratingFilter.value);
        const verifiedOnlyChecked = verifiedOnly.checked;
        const protocol = protocolFilter.value;
        const searchQuery = agentSearch.value.toLowerCase();
        
        let visibleCount = 0;
        
        agentCards.forEach(card => {
            const price = parseFloat(card.dataset.price) || 0;
            const rating = parseFloat(card.dataset.rating) || 0;
            const verified = card.dataset.verified === 'true';
            const cardText = card.textContent.toLowerCase();
            
            // Check all filters
            let show = true;
            
            // Price filter
            if (price > maxPrice && price > 0) show = false;
            
            // Rating filter
            if (rating < minRating) show = false;
            
            // Verified filter
            if (verifiedOnlyChecked && !verified) show = false;
            
            // Protocol filter
            if (protocol) {
                const badges = card.querySelectorAll('.protocol-badge');
                let hasProtocol = false;
                badges.forEach(badge => {
                    if (badge.classList.contains(protocol)) hasProtocol = true;
                });
                if (!hasProtocol) show = false;
            }
            
            // Search filter
            if (searchQuery && !cardText.includes(searchQuery)) show = false;
            
            // Show/hide card
            if (show) {
                card.style.display = 'block';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });
        
        // Update results count
        resultsCount.textContent = `Showing ${visibleCount} agent${visibleCount !== 1 ? 's' : ''}`;
        
        // Apply current sort
        applySorting();
    }
    
    // Apply sorting
    function applySorting() {
        const sortValue = sortSelect.value;
        
        const sortedCards = agentCards.slice().sort((a, b) => {
            switch(sortValue) {
                case 'rating':
                    return parseFloat(b.dataset.rating) - parseFloat(a.dataset.rating);
                    
                case 'popularity':
                    const aHires = parseInt(a.querySelector('.reviews').textContent.match(/\d+/)[0]) || 0;
                    const bHires = parseInt(b.querySelector('.reviews').textContent.match(/\d+/)[0]) || 0;
                    return bHires - aHires;
                    
                case 'price-low':
                    const aPrice = parseFloat(a.dataset.price) || 999999;
                    const bPrice = parseFloat(b.dataset.price) || 999999;
                    return aPrice - bPrice;
                    
                case 'price-high':
                    const aPriceHigh = parseFloat(a.dataset.price) || 0;
                    const bPriceHigh = parseFloat(b.dataset.price) || 0;
                    return bPriceHigh - aPriceHigh;
                    
                case 'newest':
                    // For now, keep original order (newest first assumed)
                    return 0;
                    
                default:
                    return 0;
            }
        });
        
        // Re-append in sorted order
        sortedCards.forEach(card => {
            if (card.style.display !== 'none') {
                agentGrid.appendChild(card);
            }
        });
    }
    
    // Clear filters
    clearFilters.addEventListener('click', function() {
        sortSelect.value = 'rating';
        priceRange.value = 500;
        priceDisplay.textContent = '$500/mo';
        ratingFilter.value = 0;
        verifiedOnly.checked = false;
        protocolFilter.value = '';
        agentSearch.value = '';
        applyFilters();
    });
    
    // Attach event listeners
    sortSelect.addEventListener('change', applySorting);
    priceRange.addEventListener('change', applyFilters);
    ratingFilter.addEventListener('change', applyFilters);
    verifiedOnly.addEventListener('change', applyFilters);
    protocolFilter.addEventListener('change', applyFilters);
    agentSearch.addEventListener('input', debounce(applyFilters, 300));
    
    // View toggle
    viewButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            viewButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            const view = this.dataset.view;
            if (view === 'list') {
                agentGrid.classList.add('list-view');
            } else {
                agentGrid.classList.remove('list-view');
            }
        });
    });
    
    // Debounce function for search
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Initial load
    applyFilters();
});

// Track analytics (placeholder)
function trackAgentView(agentId) {
    console.log('Agent viewed:', agentId);
    // Send to analytics service
}

function trackCategoryView(categorySlug) {
    console.log('Category viewed:', categorySlug);
    // Send to analytics service
}

// Auto-track on load
window.addEventListener('load', function() {
    const categorySlug = window.location.pathname.split('/').pop();
    trackCategoryView(categorySlug);
});
