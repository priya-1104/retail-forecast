// JavaScript for Authentication screens (login, register, reset-password)

document.addEventListener('DOMContentLoaded', function() {
    // ----------------------------------------------------
    // Password Strength Meter (Register screen)
    // ----------------------------------------------------
    const passwordInput = document.getElementById('password');
    const strengthBar = document.getElementById('password-strength-bar');
    const strengthText = document.getElementById('password-strength-text');

    if (passwordInput && strengthBar && strengthText) {
        passwordInput.addEventListener('input', function() {
            const val = passwordInput.value;
            let score = 0;

            if (val.length >= 8) score++;
            if (/[A-Z]/.test(val)) score++;
            if (/[0-9]/.test(val)) score++;
            if (/[^A-Za-z0-9]/.test(val)) score++;

            // Update strength bar color and text
            let colorClass = 'bg-danger';
            let label = 'Weak';
            let width = '25%';

            if (score === 2) {
                colorClass = 'bg-warning';
                label = 'Medium';
                width = '50%';
            } else if (score === 3) {
                colorClass = 'bg-info';
                label = 'Strong';
                width = '75%';
            } else if (score === 4) {
                colorClass = 'bg-success';
                label = 'Very Secure';
                width = '100%';
            }

            if (val.length === 0) {
                width = '0%';
                label = '';
            }

            strengthBar.className = `progress-bar ${colorClass}`;
            strengthBar.style.width = width;
            strengthText.textContent = label;
        });
    }

    // ----------------------------------------------------
    // Toggle Password Visibility
    // ----------------------------------------------------
    const togglePasswordIcons = document.querySelectorAll('.toggle-password-visibility');
    togglePasswordIcons.forEach(function(icon) {
        icon.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const targetInput = document.getElementById(targetId);
            
            if (targetInput) {
                const isPassword = targetInput.getAttribute('type') === 'password';
                targetInput.setAttribute('type', isPassword ? 'text' : 'password');
                this.classList.toggle('bi-eye');
                this.classList.toggle('bi-eye-slash');
            }
        });
    });
});
