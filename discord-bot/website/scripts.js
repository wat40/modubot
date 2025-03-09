document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');

    if (hamburger) {
        hamburger.addEventListener('click', function() {
            navLinks.classList.toggle('active');
            // Animate hamburger to X
            const bars = document.querySelectorAll('.bar');
            bars.forEach(bar => bar.classList.toggle('active'));
            
            if (navLinks.classList.contains('active')) {
                hamburger.querySelector('.bar:nth-child(1)').style.transform = 'rotate(-45deg) translate(-5px, 6px)';
                hamburger.querySelector('.bar:nth-child(2)').style.opacity = '0';
                hamburger.querySelector('.bar:nth-child(3)').style.transform = 'rotate(45deg) translate(-5px, -6px)';
            } else {
                hamburger.querySelector('.bar:nth-child(1)').style.transform = 'none';
                hamburger.querySelector('.bar:nth-child(2)').style.opacity = '1';
                hamburger.querySelector('.bar:nth-child(3)').style.transform = 'none';
            }
        });
    }

    // Tab functionality for commands section
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all buttons and contents
            tabBtns.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Show corresponding content
            const tabId = this.getAttribute('data-tab');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });

    // FAQ accordion
    const faqItems = document.querySelectorAll('.faq-item');
    
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        
        question.addEventListener('click', function() {
            // Toggle active class on clicked item
            item.classList.toggle('active');
            
            // Close other items
            faqItems.forEach(otherItem => {
                if (otherItem !== item) {
                    otherItem.classList.remove('active');
                }
            });
        });
    });

    // Scroll reveal animations
    const animateOnScroll = function() {
        const elements = document.querySelectorAll('[data-aos]');
        
        elements.forEach(element => {
            const elementPosition = element.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;
            
            if (elementPosition < windowHeight * 0.85) {
                element.classList.add('aos-animate');
            }
        });
    };

    // Add AOS (Animate On Scroll) class to elements that should animate when in view
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach((card, index) => {
        card.classList.add('aos-init');
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        card.style.transitionDelay = `${index * 0.1}s`;
    });

    // Run once on initial load
    animateOnScroll();
    
    // Run on scroll
    window.addEventListener('scroll', animateOnScroll);
    
    // Command copy functionality
    const commandNames = document.querySelectorAll('.command-name');
    
    commandNames.forEach(cmd => {
        cmd.addEventListener('click', function() {
            const textToCopy = this.textContent;
            navigator.clipboard.writeText(textToCopy).then(() => {
                // Visual feedback
                const originalText = this.textContent;
                this.textContent = 'Copied!';
                this.style.color = '#43b581';
                
                setTimeout(() => {
                    this.textContent = originalText;
                    this.style.color = '';
                }, 1000);
            }).catch(err => {
                console.error('Could not copy text: ', err);
            });
        });
    });

    // Animate elements when they come into view
    function reveal() {
        var reveals = document.querySelectorAll('.feature-card, .step, .faq-item');
        
        for (var i = 0; i < reveals.length; i++) {
            var windowHeight = window.innerHeight;
            var elementTop = reveals[i].getBoundingClientRect().top;
            var elementVisible = 150;
            
            if (elementTop < windowHeight - elementVisible) {
                reveals[i].classList.add('aos-animate');
                reveals[i].style.opacity = '1';
                reveals[i].style.transform = 'translateY(0)';
            }
        }
    }
    
    window.addEventListener('scroll', reveal);
    
    // Initial run of reveal for elements in view on page load
    reveal();

    // Smooth scroll for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                // Close mobile menu if open
                if (navLinks.classList.contains('active')) {
                    navLinks.classList.remove('active');
                    hamburger.querySelector('.bar:nth-child(1)').style.transform = 'none';
                    hamburger.querySelector('.bar:nth-child(2)').style.opacity = '1';
                    hamburger.querySelector('.bar:nth-child(3)').style.transform = 'none';
                }
                
                window.scrollTo({
                    top: targetElement.offsetTop - 70, // Adjust for fixed header
                    behavior: 'smooth'
                });
            }
        });
    });

    // Animate hero image on hover with mouse movement
    const heroImage = document.querySelector('.hero-image img');
    if (heroImage) {
        const container = document.querySelector('.hero');
        
        container.addEventListener('mousemove', (e) => {
            const xAxis = (window.innerWidth / 2 - e.pageX) / 25;
            const yAxis = (window.innerHeight / 2 - e.pageY) / 25;
            
            heroImage.style.transform = `perspective(1000px) rotateY(${xAxis}deg) rotateX(${yAxis}deg)`;
        });
        
        container.addEventListener('mouseenter', () => {
            heroImage.style.transition = 'none';
        });
        
        container.addEventListener('mouseleave', () => {
            heroImage.style.transition = 'transform 0.5s ease';
            heroImage.style.transform = 'perspective(1000px) rotateY(0) rotateX(0)';
        });
    }

    // Add pulse animation to invite button
    const inviteBtn = document.querySelector('.invite-btn');
    if (inviteBtn) {
        setInterval(() => {
            inviteBtn.classList.add('pulse');
            setTimeout(() => {
                inviteBtn.classList.remove('pulse');
            }, 1000);
        }, 5000);
    }

    // Add CSS for the pulse animation if it's not already in the CSS file
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0% {
                transform: scale(1);
            }
            50% {
                transform: scale(1.1);
            }
            100% {
                transform: scale(1);
            }
        }
        
        .pulse {
            animation: pulse 1s ease;
        }
        
        .aos-animate {
            opacity: 1 !important;
            transform: translateY(0) !important;
        }
    `;
    document.head.appendChild(style);
}); 