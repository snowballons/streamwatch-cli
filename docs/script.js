document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll for internal links
    const links = document.querySelectorAll('nav ul li a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
            // Close mobile menu if open
            if (navUl.classList.contains('active')) {
                navUl.classList.remove('active');
                menuToggle.setAttribute('aria-expanded', 'false');
            }
        });
    });

    // Update current year in footer
    const currentYearSpan = document.getElementById('currentYear');
    if (currentYearSpan) {
        currentYearSpan.textContent = new Date().getFullYear();
    }

    // Mobile menu toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const navUl = document.querySelector('nav ul');
    const nav = document.querySelector('nav');
    if (menuToggle && navUl) {
        menuToggle.setAttribute('aria-controls', 'main-nav');
        menuToggle.setAttribute('aria-expanded', 'false');
        navUl.setAttribute('id', 'main-nav');
        nav.setAttribute('aria-label', 'Main navigation');
        menuToggle.addEventListener('click', () => {
            const expanded = navUl.classList.toggle('active');
            menuToggle.setAttribute('aria-expanded', expanded ? 'true' : 'false');
        });
        // Keyboard accessibility for menu toggle
        menuToggle.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                menuToggle.click();
            }
        });
    }
});

// Add an aria-live region for copy feedback
if (!document.getElementById('copy-feedback')) {
    const feedbackDiv = document.createElement('div');
    feedbackDiv.id = 'copy-feedback';
    feedbackDiv.setAttribute('aria-live', 'polite');
    feedbackDiv.style.position = 'absolute';
    feedbackDiv.style.left = '-9999px';
    document.body.appendChild(feedbackDiv);
}

// Copy to clipboard function
function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(function() {
        // Show feedback for the correct button
        if (button) {
            const originalText = button.textContent;
            button.textContent = 'Copied!';
            setTimeout(() => {
                button.textContent = originalText;
            }, 1500);
        }
        document.getElementById('copy-feedback').textContent = 'Copied to clipboard!';
    }, function(err) {
        // Fallback for older browsers (less common now)
        try {
            const textArea = document.createElement("textarea");
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            if (button) {
                const originalText = button.textContent;
                button.textContent = 'Copied!';
                setTimeout(() => {
                    button.textContent = originalText;
                }, 1500);
            }
            document.getElementById('copy-feedback').textContent = 'Copied to clipboard!';
        } catch (e) {
            alert('Failed to copy. Please copy manually.');
        }
    });
}

// Attach copyToClipboard to all copy buttons
window.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.copy-button').forEach(btn => {
        btn.addEventListener('click', function(event) {
            event.preventDefault();

            // Try to find the code content in various ways
            let textToCopy = '';

            // Method 1: Look for previous sibling with code element
            const prevElement = this.previousElementSibling;
            if (prevElement && prevElement.tagName === 'PRE') {
                const codeElement = prevElement.querySelector('code');
                if (codeElement) {
                    textToCopy = codeElement.textContent.trim();
                }
            }

            // Method 2: Look within the same parent for code element
            if (!textToCopy) {
                const parentCodeBlock = this.closest('.code-block');
                if (parentCodeBlock) {
                    const codeElement = parentCodeBlock.querySelector('code');
                    if (codeElement) {
                        textToCopy = codeElement.textContent.trim();
                    }
                }
            }

            // Method 3: Look in command-header for code element
            if (!textToCopy) {
                const commandHeader = this.closest('.command-header');
                if (commandHeader) {
                    const codeElement = commandHeader.querySelector('code');
                    if (codeElement) {
                        textToCopy = codeElement.textContent.trim();
                    }
                }
            }

            // Method 4: Check if there's a data attribute for the text
            if (!textToCopy && this.dataset.copyText) {
                textToCopy = this.dataset.copyText;
            }

            if (textToCopy) {
                copyToClipboard(textToCopy, this);
            } else {
                console.warn('Could not find text to copy for button:', this);
            }
        });
    });

    // Enhanced FAQ functionality
    document.querySelectorAll('.faq-item summary').forEach(summary => {
        summary.addEventListener('click', function(event) {
            // Close other open FAQ items for accordion behavior
            const currentDetails = this.parentElement;
            const allDetails = document.querySelectorAll('.faq-item');

            allDetails.forEach(details => {
                if (details !== currentDetails && details.open) {
                    details.open = false;
                }
            });
        });
    });
});
