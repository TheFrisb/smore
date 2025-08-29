/**
 * Stake Modal functionality
 * Handles opening, closing, and populating the stake modal with calculated values
 */

function initStakeButtons() {
    // Get all stake buttons
    const stakeButtons = document.querySelectorAll('.stakeButton');
    
    // Get modal elements
    const modal = document.getElementById('stakeModal');
    const backdrop = document.getElementById('stakeModalBackdrop');
    const modalContainer = document.getElementById('stakeModalContainer');
    const modalContent = document.getElementById('stakeModalContent');
    const closeButton = document.getElementById('stakeModalClose');
    
    if (!modal || !backdrop || !modalContainer || !modalContent || !closeButton) {
        console.warn('Stake modal elements not found');
        return;
    }
    
    // Add click event listeners to all stake buttons
    stakeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const stakeValue = parseFloat(this.getAttribute('data-stake'));
            if (isNaN(stakeValue)) {
                console.warn('Invalid stake value:', this.getAttribute('data-stake'));
                return;
            }
            
            openStakeModal(stakeValue);
        });
    });
    
    // Close modal when clicking backdrop
    backdrop.addEventListener('click', closeStakeModal);
    
    // Close modal when clicking close button
    closeButton.addEventListener('click', closeStakeModal);
    
    // Close modal when pressing Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            closeStakeModal();
        }
    });
    
    // Close modal when clicking on the modal container (outside the content)
    modalContainer.addEventListener('click', function(e) {
        if (e.target === modalContainer) {
            closeStakeModal();
        }
    });
    
    // Prevent modal content clicks from closing the modal
    modalContent.addEventListener('click', function(e) {
        e.stopPropagation();
    });
}

function openStakeModal(stakeValue) {
    const modal = document.getElementById('stakeModal');
    
    if (!modal) return;
    
    // Calculate values based on stake percentage
    const conservativeBankroll = 1000; // €1,000
    const aggressiveBankroll = 5000;   // €5,000
    
    const conservativeAmount = (conservativeBankroll * stakeValue / 100).toFixed(0);
    const aggressiveAmount = (aggressiveBankroll * stakeValue / 100).toFixed(0);
    
    // Update modal content with calculated values
    document.getElementById('stakePercent1').textContent = `${stakeValue}%`;
    document.getElementById('stakePercent2').textContent = `${stakeValue}%`;
    document.getElementById('stakePercent3').textContent = `${stakeValue}%`;
    document.getElementById('stakeAmount1').textContent = `€${conservativeAmount}`;
    document.getElementById('stakeAmount2').textContent = `€${aggressiveAmount}`;
    
    // Show modal
    modal.classList.remove('hidden');
    
    // Add animation classes
    setTimeout(() => {
        modal.classList.add('opacity-100');
        modal.querySelector('.relative').classList.add('scale-100');
    }, 10);
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
}

function closeStakeModal() {
    const modal = document.getElementById('stakeModal');
    
    if (!modal) return;
    
    // Animate out
    modal.classList.remove('opacity-100');
    modal.querySelector('.relative').classList.remove('scale-100');
    
    // Hide modal after animation
    setTimeout(() => {
        modal.classList.add('hidden');
    }, 300);
    
    // Restore body scroll
    document.body.style.overflow = '';
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { initStakeButtons, openStakeModal, closeStakeModal };
} 