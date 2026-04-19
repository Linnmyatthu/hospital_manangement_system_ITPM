document.addEventListener('DOMContentLoaded', () => {
    const heroBtn = document.querySelector('.hero-btn');
    if (heroBtn) {
        heroBtn.addEventListener('click', () => {});
    }

    const cardCtas = document.querySelectorAll('.card-cta');
    cardCtas.forEach(cta => {
        cta.addEventListener('click', (e) => {});
    });
});