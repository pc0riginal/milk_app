<script>
document.addEventListener('DOMContentLoaded', function() {
    const monthSelect = document.querySelector('select[name="month"]');
    if (monthSelect) {
        monthSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            const monthValue = selectedOption.value;
            const yearValue = selectedOption.text.split(' ')[1];
            
            // Update hidden year field
            const yearInput = document.querySelector('input[name="year"]');
            if (yearInput) {
                yearInput.value = yearValue;
            }
            
            // Submit form
            this.form.submit();
        });
    }
});
</script>