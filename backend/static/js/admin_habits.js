document.addEventListener('DOMContentLoaded', function() {
    const freqSelect = document.getElementById('id_frequency');
    // Django admin wraps fields in rows with classes like "form-row field-weekdays"
    const weekdaysField = document.querySelector('.field-weekdays');

    function toggleWeekdays() {
        if (!freqSelect || !weekdaysField) return;

        if (freqSelect.value === 'WEEKLY') {
            // Make it visible
            weekdaysField.style.visibility = 'visible';
        } else {
            // Hide it, but KEEP the space it occupies (prevents height jump)
            weekdaysField.style.visibility = 'hidden';
        }
    }

    if (freqSelect) {
        // Run on page load (to handle existing data)
        toggleWeekdays();
        // Run whenever the user changes the dropdown
        freqSelect.addEventListener('change', toggleWeekdays);
    }
});