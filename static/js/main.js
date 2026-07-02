// ========== DATE VALIDATION ==========
document.addEventListener('DOMContentLoaded', function() {
    // Set minimum date for event_date input
    const eventDateInput = document.querySelector('input[type="date"]');
    if (eventDateInput) {
        const today = new Date().toISOString().split('T')[0];
        eventDateInput.setAttribute('min', today);
    }
    
    // Booking form validation
    const bookingForm = document.getElementById('bookingForm');
    if (bookingForm) {
        bookingForm.addEventListener('submit', function(e) {
            let isValid = true;
            let errorMessage = '';
            
            const startTime = bookingForm.querySelector('[name="start_time"]').value;
            const endTime = bookingForm.querySelector('[name="end_time"]').value;
            const eventDate = bookingForm.querySelector('[name="event_date"]').value;
            const guests = bookingForm.querySelector('[name="guests"]').value;
            
            // Validate start time < end time
            if (startTime && endTime && startTime >= endTime) {
                isValid = false;
                errorMessage += '❌ End time must be after start time.\n';
            }
            
            // Validate date is not in past
            if (eventDate) {
                const selectedDate = new Date(eventDate);
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                if (selectedDate < today) {
                    isValid = false;
                    errorMessage += '❌ Cannot book a past date.\n';
                }
            }
            
            // Validate guests
            if (guests && guests < 1) {
                isValid = false;
                errorMessage += '❌ Number of guests must be at least 1.\n';
            }
            
            if (!isValid) {
                e.preventDefault();
                alert(errorMessage);
            }
        });
    }
    
    // Registration form validation
    const registerForm = document.querySelector('form[method="post"]');
    if (registerForm && window.location.pathname.includes('register')) {
        registerForm.addEventListener('submit', function(e) {
            const password = registerForm.querySelector('[name="password"]').value;
            const confirmPassword = registerForm.querySelector('[name="confirm_password"]').value;
            
            if (password && confirmPassword && password !== confirmPassword) {
                e.preventDefault();
                alert('❌ Passwords do not match!');
            }
            
            if (password && password.length < 8) {
                e.preventDefault();
                alert('❌ Password must be at least 8 characters long!');
            }
        });
    }
    
    // Fade-in animation for cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in-up');
    });
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
    
    // Booking confirmation
    const confirmButtons = document.querySelectorAll('.confirm-booking');
    confirmButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to confirm this booking?')) {
                e.preventDefault();
            }
        });
    });
    
    // Cancel booking confirmation
    const cancelButtons = document.querySelectorAll('.cancel-booking');
    cancelButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to cancel this booking? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
});