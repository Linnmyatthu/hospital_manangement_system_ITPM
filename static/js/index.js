document.addEventListener('DOMContentLoaded', () => {
    console.log('Index.js loaded - page specific functionality only');
    
    // Any index page specific functionality can go here
    
    // Example: Initialize any charts or graphs on the dashboard
    // This is just a placeholder - add your actual dashboard functionality here
    
    // Example: Handle any interactive elements on the dashboard
    const heroBtn = document.querySelector('.hero-btn');
    if (heroBtn) {
        heroBtn.addEventListener('click', () => {
            console.log('Hero button clicked');
            // Add your hero button functionality here
        });
    }
    
    // Example: Handle card CTA buttons
    const cardCtas = document.querySelectorAll('.card-cta');
    cardCtas.forEach(cta => {
        cta.addEventListener('click', (e) => {
            console.log('Card CTA clicked:', e.target.href);
            // The link will work normally, but you can add tracking here
        });
    });
    
    // Log that the page is ready
    console.log('Index page ready - all functionality loaded');
});