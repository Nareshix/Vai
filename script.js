document.addEventListener('DOMContentLoaded', () => {
    // --- Element References ---
    const htmlElement = document.documentElement;
    const mainScroller = document.querySelector('.main-area-wrapper');
    const themeToggleButton = document.getElementById('themeToggle');
    const tocContainerElement = document.getElementById('toc-container');
    const tocLinksContainer = document.getElementById('toc-links');
    const tocActiveMarker = document.getElementById('toc-active-marker');
    let tocLinks = tocLinksContainer ? Array.from(tocLinksContainer.getElementsByTagName('a')) : [];
    const searchTriggerButton = document.getElementById('searchTrigger');
    const searchOverlayEl = document.getElementById('searchOverlay');
    const searchInput = document.getElementById('searchInput');
    const searchCloseButton = document.getElementById('searchCloseButton');
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const leftSidebar = document.getElementById('leftSidebar');
    const pageOverlay = document.getElementById('pageOverlay');
    const mobileTocToggle = document.getElementById('mobileTocToggle');

    // --- State Variables ---
    const THEME_KEY = 'user-preferred-theme';
    const sections = {}; // Object to store section elements and their paddingTop

    // --- Configuration for Scroll Spy & Click Navigation ---
    const APP_HEADER_ELEMENT = document.querySelector('.app-header');
    let DYNAMIC_HEADER_OFFSET = 64; // Fallback, typically 4rem * 16px/rem
    const DESIRED_TEXT_GAP_BELOW_HEADER = 16; // e.g., 1rem, desired space below header to heading text
    const SCROLL_SPY_ACTIVATION_LEEWAY = 20;  // Pixels "before" precise alignment to activate link

    function updateDynamicHeaderOffset() {
        if (APP_HEADER_ELEMENT) {
            DYNAMIC_HEADER_OFFSET = APP_HEADER_ELEMENT.offsetHeight;
        }
    }
    updateDynamicHeaderOffset(); // Initial calculation
    // Consider adding resize listener if header height can change and affect layout significantly
    // window.addEventListener('resize', () => {
    //     updateDynamicHeaderOffset();
    //     updateActiveLinkAndMarker(); // Re-evaluate active link if header height changes
    // });


    let isSearchActive = false;

    // --- Helper: Update Body Scroll & Page Overlay ---
    function updateBodyScrollAndOverlay() {
        const isSidebarOpen = document.body.classList.contains('mobile-sidebar-open');
        const isTocOpen = document.body.classList.contains('mobile-toc-open');
        const transitionDuration = 300; 

        if (isSidebarOpen || isTocOpen) {
            if (pageOverlay.style.display !== 'block') {
                pageOverlay.style.display = 'block';
                requestAnimationFrame(() => { pageOverlay.style.opacity = '1'; });
            }
            document.body.style.overflow = 'hidden';
        } else {
            pageOverlay.style.opacity = '0';
            setTimeout(() => {
                if (!document.body.classList.contains('mobile-sidebar-open') &&
                    !document.body.classList.contains('mobile-toc-open')) {
                    pageOverlay.style.display = 'none';
                }
            }, transitionDuration);
            document.body.style.overflow = '';
        }
    }

    // --- 1. Theme Functionality ---
    function applyTheme(theme) {
        htmlElement.classList.toggle('light-theme', theme === 'light');
        htmlElement.classList.toggle('dark-theme', theme === 'dark');
        if (themeToggleButton) themeToggleButton.setAttribute('aria-label', theme === 'light' ? 'Switch to Dark Theme' : 'Switch to Light Theme');
    }
    function saveThemePreference(theme) { localStorage.setItem(THEME_KEY, theme); }
    function getInitialTheme() {
        const savedTheme = localStorage.getItem(THEME_KEY);
        if (savedTheme) return savedTheme;
        return window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    }
    if (themeToggleButton) {
        themeToggleButton.addEventListener('click', () => {
            const newTheme = htmlElement.classList.contains('light-theme') ? 'dark' : 'light';
            applyTheme(newTheme);
            saveThemePreference(newTheme);
        });
    }
    applyTheme(getInitialTheme());

    // --- 2. Table of Contents (Scroll Spy & Active Marker) ---
    if (tocLinks.length > 0) {
        tocLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href?.startsWith('#')) {
                const sectionId = href.substring(1);
                const sectionElement = document.getElementById(sectionId);
                if (sectionElement) {
                    // Store element and its computed paddingTop
                    const paddingTop = parseFloat(getComputedStyle(sectionElement).paddingTop) || 0;
                    sections[sectionId] = { element: sectionElement, paddingTop: paddingTop };
                }
            }
        });
    }

    function updateActiveLinkAndMarker() {
        const sectionIds = Object.keys(sections); 

        if (!mainScroller || tocLinks.length === 0 || !tocActiveMarker || sectionIds.length === 0) {
            if (tocActiveMarker) tocActiveMarker.style.opacity = '0';
            if (tocLinksContainer) tocLinks.forEach(link => link.classList.remove('active'));
            return;
        }

        const contentScrollTop = mainScroller.scrollTop;
        let currentSectionId = null;

        for (let i = sectionIds.length - 1; i >= 0; i--) {
            const id = sectionIds[i];
            const sectionData = sections[id];
            if (sectionData && sectionData.element) {
                const sectionElement = sectionData.element;
                const elementPaddingTop = sectionData.paddingTop;

                // Calculate where the text of the section effectively starts
                const textVisibleStartingPoint = sectionElement.offsetTop + elementPaddingTop;
                
                // Calculate the scrollTop value at which this section's text would be perfectly positioned
                const targetScrollTopForSectionText = textVisibleStartingPoint - DYNAMIC_HEADER_OFFSET - DESIRED_TEXT_GAP_BELOW_HEADER;

                // Section is active if scrollTop is at or past this target position, minus a leeway
                if (targetScrollTopForSectionText - SCROLL_SPY_ACTIVATION_LEEWAY <= contentScrollTop) {
                    currentSectionId = id;
                    break; 
                }
            }
        }

        if (currentSectionId === null && sectionIds.length > 0) {
            // If scrolled above all sections' trigger points, default to the first section if its effective top is near or above current scroll.
            // Or simply default to the first section if no other logic caught it.
             const firstSectionData = sections[sectionIds[0]];
             if (firstSectionData && firstSectionData.element) {
                const textVisibleStartingPoint = firstSectionData.element.offsetTop + firstSectionData.paddingTop;
                const targetScrollTopForFirstSectionText = textVisibleStartingPoint - DYNAMIC_HEADER_OFFSET - DESIRED_TEXT_GAP_BELOW_HEADER;
                 // If contentScrollTop is above the first section's ideal position, make first active.
                if (contentScrollTop < targetScrollTopForFirstSectionText + SCROLL_SPY_ACTIVATION_LEEWAY) {
                     currentSectionId = sectionIds[0];
                }
             }
             if(currentSectionId === null) currentSectionId = sectionIds[0]; // Fallback to first if still null
        }
        
        const epsilon = 2; 
        const isAtScrollEnd = (mainScroller.scrollTop + mainScroller.clientHeight >= mainScroller.scrollHeight - epsilon);
        
        if (isAtScrollEnd && sectionIds.length > 0) {
            currentSectionId = sectionIds[sectionIds.length - 1];
        }

        let activeLinkElement = null;
        tocLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${currentSectionId}`) {
                link.classList.add('active');
                activeLinkElement = link;
            }
        });

        if (activeLinkElement && tocContainerElement && tocContainerElement.scrollHeight > tocContainerElement.clientHeight) {
            const linkTopInToc = activeLinkElement.offsetTop;
            const linkHeight = activeLinkElement.offsetHeight;
            const linkBottomInToc = linkTopInToc + linkHeight;
            const tocScrollTop = tocContainerElement.scrollTop;
            const tocClientHeight = tocContainerElement.clientHeight;
            const scrollPadding = 30; 

            if (linkTopInToc < tocScrollTop + scrollPadding) {
                tocContainerElement.scrollTo({ top: Math.max(0, linkTopInToc - scrollPadding), behavior: 'smooth' });
            } else if (linkBottomInToc > tocScrollTop + tocClientHeight - scrollPadding) {
                tocContainerElement.scrollTo({ top: Math.min(linkBottomInToc - tocClientHeight + scrollPadding, tocContainerElement.scrollHeight - tocClientHeight), behavior: 'smooth' });
            }
        }

        if (activeLinkElement) {
            tocActiveMarker.style.top = `${activeLinkElement.offsetTop}px`;
            tocActiveMarker.style.height = `${activeLinkElement.offsetHeight}px`;
            tocActiveMarker.style.opacity = '1';
        } else {
            tocActiveMarker.style.opacity = '0';
        }
    }

    if (tocLinksContainer) {
        tocLinksContainer.addEventListener('click', (e) => {
            const targetLink = e.target.closest('a');
            if (targetLink && targetLink.getAttribute('href')?.startsWith('#')) {
                e.preventDefault();
                const targetId = targetLink.getAttribute('href').substring(1);
                const sectionData = sections[targetId]; // Get section data (element + paddingTop)
                
                if (sectionData && sectionData.element && mainScroller) {
                    const targetElement = sectionData.element;
                    const elementPaddingTop = sectionData.paddingTop;

                    // Calculate where the text of the section effectively starts
                    const textVisibleStartingPoint = targetElement.offsetTop + elementPaddingTop;
                    
                    // Calculate the scrollTop value to position the text correctly below the header
                    const scrollToPosition = textVisibleStartingPoint - DYNAMIC_HEADER_OFFSET - DESIRED_TEXT_GAP_BELOW_HEADER;
                    
                    mainScroller.scrollTo({
                        top: Math.max(0, scrollToPosition), // Ensure not scrolling to negative values
                        behavior: 'smooth'
                    });
                }
                if (document.body.classList.contains('mobile-toc-open')) {
                    closeMobileToc(); 
                }
            }
        });
    }

    if (mainScroller && tocLinks.length > 0) {
        mainScroller.addEventListener('scroll', updateActiveLinkAndMarker);
        setTimeout(updateActiveLinkAndMarker, 100); 
    }

    // --- 3. Search Functionality ---
    // ... (rest of search functionality: isEditingContent, openSearch, closeSearch, event listeners) ...
    function isEditingContent(element) {
        const tagName = element?.tagName;
        return tagName === 'INPUT' || tagName === 'TEXTAREA' || element?.isContentEditable || element?.closest('input, textarea, [contenteditable="true"], [contenteditable=""]');
    }
    function openSearch() {
        if (isSearchActive || !searchOverlayEl || !searchInput) return;
        requestAnimationFrame(() => {
            searchOverlayEl.classList.add('active');
            setTimeout(() => { searchInput.value = ''; searchInput.focus(); }, 60);
        });
        document.body.style.overflow = 'hidden'; 
        isSearchActive = true;
    }
    function closeSearch() {
        if (!isSearchActive || !searchOverlayEl) return;
        searchOverlayEl.classList.remove('active');
        if(searchInput) searchInput.blur();
        if (searchTriggerButton) searchTriggerButton.focus({ preventScroll: true });
        isSearchActive = false;
        if (!document.body.classList.contains('mobile-sidebar-open') && !document.body.classList.contains('mobile-toc-open')) {
            document.body.style.overflow = ''; 
        }
    }
    if (searchTriggerButton) searchTriggerButton.addEventListener('click', openSearch);
    if (searchCloseButton) searchCloseButton.addEventListener('click', closeSearch);
    if (searchOverlayEl) searchOverlayEl.addEventListener('click', (e) => { if (e.target === searchOverlayEl) closeSearch(); });


    // --- 4. Sidebar Accordion ---
    // ... (rest of sidebar accordion functionality) ...
    document.querySelectorAll('.sidebar-nav .sidebar-nav-section').forEach(section => {
        const toggleButton = section.querySelector('.sidebar-section-toggle');
        const content = section.querySelector('.sidebar-section-content');
        if (toggleButton && content) {
            if (section.classList.contains('is-open')) {
                const originalTransition = content.style.transition;
                content.style.transition = 'none'; 
                content.style.maxHeight = content.scrollHeight + "px";
                requestAnimationFrame(() => { 
                    requestAnimationFrame(() => { content.style.transition = originalTransition; }); 
                });
            }
            toggleButton.addEventListener('click', () => {
                const isOpen = section.classList.toggle('is-open');
                toggleButton.setAttribute('aria-expanded', isOpen.toString());
                content.style.maxHeight = isOpen ? content.scrollHeight + "px" : "0px";
            });
        }
    });

    // --- 5. Mobile Navigation (Main Sidebar) ---
    // ... (rest of mobile nav: openMobileSidebar, closeMobileSidebar, event listeners) ...
    function openMobileSidebar() {
        if (!leftSidebar || !mobileMenuToggle) return;
        if (document.body.classList.contains('mobile-toc-open')) closeMobileToc(); 
        document.body.classList.add('mobile-sidebar-open');
        mobileMenuToggle.setAttribute('aria-expanded', 'true');
        leftSidebar.querySelector('.sidebar-nav')?.scrollTo(0, 0);
        updateBodyScrollAndOverlay();
    }
    function closeMobileSidebar() {
        if (!leftSidebar || !mobileMenuToggle) return;
        document.body.classList.remove('mobile-sidebar-open');
        mobileMenuToggle.setAttribute('aria-expanded', 'false');
        updateBodyScrollAndOverlay();
    }
    if (mobileMenuToggle && leftSidebar) {
        mobileMenuToggle.addEventListener('click', () => {
            document.body.classList.contains('mobile-sidebar-open') ? closeMobileSidebar() : openMobileSidebar();
        });
    }
    if (leftSidebar) {
        leftSidebar.addEventListener('click', (event) => {
            if (event.target.closest('a') && document.body.classList.contains('mobile-sidebar-open')) {
                closeMobileSidebar();
            }
        });
    }

    // --- 6. Mobile Table of Contents Panel ---
    // ... (rest of mobile ToC: openMobileToc, closeMobileToc, event listeners) ...
    function openMobileToc() {
        if (!tocContainerElement || !mobileTocToggle) return;
        if (document.body.classList.contains('mobile-sidebar-open')) closeMobileSidebar(); 
        document.body.classList.add('mobile-toc-open');
        mobileTocToggle.setAttribute('aria-expanded', 'true');
        tocContainerElement.scrollTo(0, 0); 
        updateActiveLinkAndMarker(); 
        updateBodyScrollAndOverlay();
    }
    function closeMobileToc() {
        if (!tocContainerElement || !mobileTocToggle) return;
        document.body.classList.remove('mobile-toc-open');
        mobileTocToggle.setAttribute('aria-expanded', 'false');
        updateBodyScrollAndOverlay();
    }
    if (mobileTocToggle && tocContainerElement) {
        mobileTocToggle.addEventListener('click', () => {
            document.body.classList.contains('mobile-toc-open') ? closeMobileToc() : openMobileToc();
        });
    }

    // --- 7. Global Event Listeners (Overlay, Keyboard) ---
    // ... (rest of global event listeners) ...
    if (pageOverlay) {
        pageOverlay.addEventListener('click', () => {
            if (document.body.classList.contains('mobile-sidebar-open')) closeMobileSidebar();
            if (document.body.classList.contains('mobile-toc-open')) closeMobileToc();
        });
    }
    document.addEventListener('keydown', (e) => {
        if (e.key === '/' && !isSearchActive && !isEditingContent(document.activeElement)) { e.preventDefault(); openSearch(); }
        if (e.key === 'k' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); isSearchActive ? closeSearch() : openSearch(); }
        if (e.key === 'Escape') {
            if (isSearchActive) { e.preventDefault(); closeSearch(); }
            else if (document.body.classList.contains('mobile-sidebar-open')) { e.preventDefault(); closeMobileSidebar(); }
            else if (document.body.classList.contains('mobile-toc-open')) { e.preventDefault(); closeMobileToc(); }
        }
    });
});