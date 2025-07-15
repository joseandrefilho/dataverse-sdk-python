// Custom JavaScript for jaf-dataverse-2025 Documentation Site

document.addEventListener('DOMContentLoaded', function() {
    
    // Add copy buttons to code blocks
    addCopyButtonsToCodeBlocks();
    
    // Initialize search functionality
    initializeSearch();
    
    // Add smooth scrolling
    initializeSmoothScrolling();
    
    // Add table of contents for long pages
    generateTableOfContents();
    
    // Initialize code syntax highlighting
    initializeCodeHighlighting();
    
    // Add external link indicators
    addExternalLinkIndicators();
    
    // Initialize mobile menu toggle
    initializeMobileMenu();
});

// Add copy buttons to all code blocks
function addCopyButtonsToCodeBlocks() {
    const codeBlocks = document.querySelectorAll('pre code');
    
    codeBlocks.forEach(function(codeBlock) {
        const pre = codeBlock.parentElement;
        
        // Skip if already has a copy button
        if (pre.querySelector('.copy-code-btn')) return;
        
        // Create copy button
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-code-btn';
        copyButton.innerHTML = '<i class="fas fa-copy"></i>';
        copyButton.title = 'Copy code';
        
        // Style the button
        copyButton.style.cssText = `
            position: absolute;
            top: 8px;
            right: 8px;
            background: rgba(0, 0, 0, 0.1);
            border: none;
            border-radius: 4px;
            padding: 6px 8px;
            cursor: pointer;
            color: #586069;
            font-size: 12px;
            transition: all 0.2s ease;
            z-index: 1;
        `;
        
        // Position the pre element relatively
        pre.style.position = 'relative';
        
        // Add click handler
        copyButton.addEventListener('click', function() {
            const code = codeBlock.textContent;
            copyToClipboard(code, copyButton);
        });
        
        // Add hover effects
        copyButton.addEventListener('mouseenter', function() {
            this.style.background = 'rgba(0, 0, 0, 0.2)';
            this.style.color = '#24292e';
        });
        
        copyButton.addEventListener('mouseleave', function() {
            this.style.background = 'rgba(0, 0, 0, 0.1)';
            this.style.color = '#586069';
        });
        
        pre.appendChild(copyButton);
    });
}

// Copy text to clipboard with visual feedback
function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(function() {
        // Show success feedback
        const originalContent = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check"></i>';
        button.style.color = '#28a745';
        button.title = 'Copied!';
        
        setTimeout(function() {
            button.innerHTML = originalContent;
            button.style.color = '#586069';
            button.title = 'Copy code';
        }, 2000);
    }).catch(function(err) {
        console.error('Failed to copy text: ', err);
        
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        
        try {
            document.execCommand('copy');
            button.innerHTML = '<i class="fas fa-check"></i>';
            button.style.color = '#28a745';
            
            setTimeout(function() {
                button.innerHTML = '<i class="fas fa-copy"></i>';
                button.style.color = '#586069';
            }, 2000);
        } catch (err) {
            console.error('Fallback copy failed: ', err);
        }
        
        document.body.removeChild(textArea);
    });
}

// Initialize search functionality
function initializeSearch() {
    // This would integrate with a search service like Algolia or implement local search
    const searchInput = document.querySelector('.search-box input');
    
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase();
            
            if (query.length > 2) {
                // Implement search logic here
                performSearch(query);
            }
        });
    }
}

// Perform search (placeholder implementation)
function performSearch(query) {
    // This would be replaced with actual search implementation
    console.log('Searching for:', query);
}

// Add smooth scrolling to anchor links
function initializeSmoothScrolling() {
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    
    anchorLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                
                // Update URL without jumping
                history.pushState(null, null, '#' + targetId);
            }
        });
    });
}

// Generate table of contents for long pages
function generateTableOfContents() {
    const headings = document.querySelectorAll('h2, h3, h4');
    
    if (headings.length > 3) {
        const tocContainer = document.createElement('div');
        tocContainer.className = 'table-of-contents';
        tocContainer.innerHTML = '<h3><i class="fas fa-list"></i> Table of Contents</h3>';
        
        const tocList = document.createElement('ul');
        
        headings.forEach(function(heading, index) {
            // Add ID to heading if it doesn't have one
            if (!heading.id) {
                heading.id = 'heading-' + index;
            }
            
            const listItem = document.createElement('li');
            listItem.className = 'toc-' + heading.tagName.toLowerCase();
            
            const link = document.createElement('a');
            link.href = '#' + heading.id;
            link.textContent = heading.textContent;
            
            listItem.appendChild(link);
            tocList.appendChild(listItem);
        });
        
        tocContainer.appendChild(tocList);
        
        // Insert TOC after the first paragraph or at the beginning of content
        const firstParagraph = document.querySelector('section p');
        if (firstParagraph) {
            firstParagraph.parentNode.insertBefore(tocContainer, firstParagraph.nextSibling);
        } else {
            const section = document.querySelector('section');
            if (section) {
                section.insertBefore(tocContainer, section.firstChild);
            }
        }
        
        // Style the TOC
        tocContainer.style.cssText = `
            background-color: #f6f8fa;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 16px;
            margin: 20px 0;
        `;
        
        tocList.style.cssText = `
            list-style: none;
            padding-left: 0;
            margin: 10px 0 0 0;
        `;
        
        // Style TOC items
        const tocItems = tocContainer.querySelectorAll('li');
        tocItems.forEach(function(item) {
            if (item.className === 'toc-h2') {
                item.style.marginLeft = '0';
                item.style.fontWeight = '600';
            } else if (item.className === 'toc-h3') {
                item.style.marginLeft = '20px';
            } else if (item.className === 'toc-h4') {
                item.style.marginLeft = '40px';
                item.style.fontSize = '13px';
            }
            
            item.style.margin = '4px 0';
            
            const link = item.querySelector('a');
            link.style.cssText = `
                color: #0366d6;
                text-decoration: none;
                display: block;
                padding: 2px 0;
            `;
            
            link.addEventListener('mouseenter', function() {
                this.style.textDecoration = 'underline';
            });
            
            link.addEventListener('mouseleave', function() {
                this.style.textDecoration = 'none';
            });
        });
    }
}

// Initialize code syntax highlighting
function initializeCodeHighlighting() {
    // Add language labels to code blocks
    const codeBlocks = document.querySelectorAll('pre code');
    
    codeBlocks.forEach(function(codeBlock) {
        const className = codeBlock.className;
        const languageMatch = className.match(/language-(\w+)/);
        
        if (languageMatch) {
            const language = languageMatch[1];
            const pre = codeBlock.parentElement;
            
            // Create language label
            const languageLabel = document.createElement('div');
            languageLabel.className = 'code-language-label';
            languageLabel.textContent = language.toUpperCase();
            
            languageLabel.style.cssText = `
                position: absolute;
                top: 8px;
                left: 8px;
                background-color: rgba(0, 0, 0, 0.1);
                color: #586069;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 10px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            `;
            
            pre.style.position = 'relative';
            pre.appendChild(languageLabel);
        }
    });
}

// Add indicators for external links
function addExternalLinkIndicators() {
    const links = document.querySelectorAll('a[href^="http"]');
    
    links.forEach(function(link) {
        // Skip if it's an internal link
        if (link.hostname === window.location.hostname) return;
        
        // Add external link icon
        const icon = document.createElement('i');
        icon.className = 'fas fa-external-link-alt';
        icon.style.cssText = `
            margin-left: 4px;
            font-size: 0.8em;
            opacity: 0.7;
        `;
        
        link.appendChild(icon);
        
        // Add target="_blank" if not already present
        if (!link.hasAttribute('target')) {
            link.setAttribute('target', '_blank');
            link.setAttribute('rel', 'noopener noreferrer');
        }
    });
}

// Initialize mobile menu toggle
function initializeMobileMenu() {
    // This would be implemented if there's a mobile menu
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const mainNav = document.querySelector('.main-nav');
    
    if (mobileMenuToggle && mainNav) {
        mobileMenuToggle.addEventListener('click', function() {
            mainNav.classList.toggle('mobile-open');
        });
    }
}

// Utility function to debounce events
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        
        if (callNow) func.apply(context, args);
    };
}

// Add scroll-to-top button
function addScrollToTopButton() {
    const scrollButton = document.createElement('button');
    scrollButton.innerHTML = '<i class="fas fa-chevron-up"></i>';
    scrollButton.className = 'scroll-to-top';
    scrollButton.title = 'Scroll to top';
    
    scrollButton.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #0366d6;
        color: white;
        border: none;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        cursor: pointer;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
        z-index: 1000;
    `;
    
    document.body.appendChild(scrollButton);
    
    // Show/hide button based on scroll position
    const toggleScrollButton = debounce(function() {
        if (window.pageYOffset > 300) {
            scrollButton.style.opacity = '1';
            scrollButton.style.visibility = 'visible';
        } else {
            scrollButton.style.opacity = '0';
            scrollButton.style.visibility = 'hidden';
        }
    }, 100);
    
    window.addEventListener('scroll', toggleScrollButton);
    
    // Scroll to top when clicked
    scrollButton.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
    
    // Hover effects
    scrollButton.addEventListener('mouseenter', function() {
        this.style.backgroundColor = '#0256cc';
        this.style.transform = 'scale(1.1)';
    });
    
    scrollButton.addEventListener('mouseleave', function() {
        this.style.backgroundColor = '#0366d6';
        this.style.transform = 'scale(1)';
    });
}

// Initialize scroll-to-top button
addScrollToTopButton();

// Add keyboard navigation
document.addEventListener('keydown', function(e) {
    // Alt + Left Arrow: Previous page
    if (e.altKey && e.key === 'ArrowLeft') {
        const prevLink = document.querySelector('.nav-link.prev');
        if (prevLink) {
            window.location.href = prevLink.href;
        }
    }
    
    // Alt + Right Arrow: Next page
    if (e.altKey && e.key === 'ArrowRight') {
        const nextLink = document.querySelector('.nav-link.next');
        if (nextLink) {
            window.location.href = nextLink.href;
        }
    }
    
    // Escape: Close any open modals or menus
    if (e.key === 'Escape') {
        const mobileNav = document.querySelector('.main-nav.mobile-open');
        if (mobileNav) {
            mobileNav.classList.remove('mobile-open');
        }
    }
});

// Add print functionality
function addPrintButton() {
    const printButton = document.createElement('button');
    printButton.innerHTML = '<i class="fas fa-print"></i> Print';
    printButton.className = 'print-button';
    printButton.title = 'Print this page';
    
    printButton.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: #6c757d;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 12px;
        cursor: pointer;
        font-size: 12px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        z-index: 999;
        transition: all 0.2s ease;
    `;
    
    printButton.addEventListener('click', function() {
        window.print();
    });
    
    printButton.addEventListener('mouseenter', function() {
        this.style.backgroundColor = '#5a6268';
    });
    
    printButton.addEventListener('mouseleave', function() {
        this.style.backgroundColor = '#6c757d';
    });
    
    document.body.appendChild(printButton);
}

// Initialize print button
addPrintButton();

// Analytics tracking (if Google Analytics is configured)
function trackEvent(category, action, label) {
    if (typeof gtag !== 'undefined') {
        gtag('event', action, {
            event_category: category,
            event_label: label
        });
    }
}

// Track documentation usage
document.addEventListener('click', function(e) {
    const target = e.target.closest('a');
    
    if (target) {
        // Track external links
        if (target.hostname !== window.location.hostname) {
            trackEvent('External Link', 'Click', target.href);
        }
        
        // Track navigation
        if (target.classList.contains('nav-link')) {
            trackEvent('Navigation', 'Page Navigation', target.textContent.trim());
        }
        
        // Track copy button usage
        if (target.classList.contains('copy-btn') || target.classList.contains('copy-code-btn')) {
            trackEvent('Code', 'Copy', 'Code Block');
        }
    }
});

