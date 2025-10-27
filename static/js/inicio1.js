        // Animación para los contadores de estadísticas
        document.addEventListener('DOMContentLoaded', function() {
            // Configuración para el Intersection Observer
            const observerOptions = {
                threshold: 0.5,
                rootMargin: '0px 0px -100px 0px'
            };

            // Observador para las tarjetas de estadísticas
            const statsObserver = new IntersectionObserver(function(entries) {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const statNumbers = entry.target.querySelectorAll('.stat-number');
                        statNumbers.forEach(stat => {
                            const target = parseInt(stat.getAttribute('data-count'));
                            const duration = 2000; // 2 segundos
                            const step = target / (duration / 16); // 60 FPS
                            let current = 0;
                            
                            const timer = setInterval(() => {
                                current += step;
                                if (current >= target) {
                                    clearInterval(timer);
                                    current = target;
                                }
                                stat.textContent = Math.floor(current);
                            }, 16);
                        });
                        
                        // Dejar de observar después de animar
                        statsObserver.unobserve(entry.target);
                    }
                });
            }, observerOptions);

            // Observar la sección de estadísticas
            const statsSection = document.querySelector('.stats-section');
            if (statsSection) {
                statsObserver.observe(statsSection);
            }

            // Animación para las tarjetas de pasos
            const stepCards = document.querySelectorAll('.step-card');
            const stepObserver = new IntersectionObserver(function(entries) {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }
                });
            }, observerOptions);

            stepCards.forEach(card => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(30px)';
                card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                stepObserver.observe(card);
            });

            // Smooth scroll para enlaces internos
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function(e) {
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {
                        target.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                });
            });
        });