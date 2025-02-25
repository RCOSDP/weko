
document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM loaded');
    const buttons = document.querySelectorAll('.relatedButton');
    console.log('Found buttons:', buttons.length);
    buttons.forEach(button => {
        button.addEventListener('click', function () {
            console.log('Button clicked:', this);
            const content = this.closest('td').querySelector('.relatedInfo');
            console.log('Found content:', content);
            if (content) {
                if (content.classList.contains('expanded')) {
                    content.classList.remove('expanded');
                    content.style.display = 'none';
                } else {
                    content.classList.add('expanded');
                    content.style.display = 'block';
                }
            }
        });
    });
});