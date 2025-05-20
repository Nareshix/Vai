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
    const leftSidebar = document.getElementById('leftSidebar'); // Used ID
    const pageOverlay = document.getElementById('pageOverlay');
    const mobileTocToggle = document.getElementById('mobileTocToggle'); // New ToC toggle

    // --- State Variables ---
    const THEME_KEY = 'user-preferred-theme';
    const sections = {};
    const scrollOffset = 20; // For scroll spy
    let isSearchActive = false;

    // --- Helper: Update Body Scroll & Page Overlay ---
    function updateBodyScrollAndOverlay() {
        const isSidebarOpen = document.body.classList.contains('mobile-sidebar-open');
        const isTocOpen = document.body.classList.contains('mobile-toc-open');
        const transitionDuration = 300; // ms, should match CSS transition for opacity

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
                const sectionElement = document.getElementById(href.substring(1));
                if (sectionElement) sections[href.substring(1)] = sectionElement;
            }
        });
    }
    function updateActiveLinkAndMarker() {
        if (!mainScroller || tocLinks.length === 0 || !tocActiveMarker) return;
        let currentSectionId = null;
        const contentScrollTop = mainScroller.scrollTop;
        const sectionIds = Object.keys(sections);

        for (let i = sectionIds.length - 1; i >= 0; i--) {
            const id = sectionIds[i];
            if (sections[id] && (sections[id].offsetTop - scrollOffset <= contentScrollTop)) {
                currentSectionId = id; break;
            }
        }
        if (currentSectionId === null && sectionIds.length > 0 && sections[sectionIds[0]] &&
            (contentScrollTop < scrollOffset || contentScrollTop < (sections[sectionIds[0]].offsetTop - scrollOffset))) {
            currentSectionId = sectionIds[0];
        }
        if (sectionIds.length > 0 && (mainScroller.scrollHeight - mainScroller.scrollTop <= mainScroller.clientHeight + 5)) {
            currentSectionId = sectionIds[sectionIds.length - 1];
        }

        let activeLinkElement = null;
        tocLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${currentSectionId}`) {
                link.classList.add('active'); activeLinkElement = link;
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
            const target = e.target.closest('a');
            if (target?.getAttribute('href')?.startsWith('#')) {
                e.preventDefault();
                const targetElement = document.getElementById(target.getAttribute('href').substring(1));
                if (targetElement && mainScroller) mainScroller.scrollTo({ top: targetElement.offsetTop, behavior: 'smooth' });
                // If mobile ToC is open, close it
                if (document.body.classList.contains('mobile-toc-open')) {
                    closeMobileToc();
                }
            }
        });
    }
    if (mainScroller && tocLinks.length > 0) {
        mainScroller.addEventListener('scroll', updateActiveLinkAndMarker);
        updateActiveLinkAndMarker(); // Initial call
    }

    // --- 3. Search Functionality ---
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
        document.body.style.overflow = 'hidden'; // Search also locks scroll
        isSearchActive = true;
    }
    function closeSearch() {
        if (!isSearchActive || !searchOverlayEl) return;
        searchOverlayEl.classList.remove('active');
        if(searchInput) searchInput.blur();
        if (searchTriggerButton) searchTriggerButton.focus({ preventScroll: true });
        isSearchActive = false;
        if (!document.body.classList.contains('mobile-sidebar-open') && !document.body.classList.contains('mobile-toc-open')) {
            document.body.style.overflow = ''; // Restore scroll if no other panel is open
        }
    }
    if (searchTriggerButton) searchTriggerButton.addEventListener('click', openSearch);
    if (searchCloseButton) searchCloseButton.addEventListener('click', closeSearch);
    if (searchOverlayEl) searchOverlayEl.addEventListener('click', (e) => { if (e.target === searchOverlayEl) closeSearch(); });

    // --- 4. Sidebar Accordion ---
    document.querySelectorAll('.sidebar-nav .sidebar-nav-section').forEach(section => {
        const toggleButton = section.querySelector('.sidebar-section-toggle');
        const content = section.querySelector('.sidebar-section-content');
        if (toggleButton && content) {
            if (section.classList.contains('is-open')) {
                const originalTransition = content.style.transition;
                content.style.transition = 'none'; // Disable transition for initial open
                content.style.maxHeight = content.scrollHeight + "px";
                requestAnimationFrame(() => { // Force reflow
                    requestAnimationFrame(() => { content.style.transition = originalTransition; }); // Restore transition
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
    function openMobileSidebar() {
        if (!leftSidebar || !mobileMenuToggle) return;
        if (document.body.classList.contains('mobile-toc-open')) closeMobileToc(); // Close ToC if open
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
    function openMobileToc() {
        if (!tocContainerElement || !mobileTocToggle) return;
        if (document.body.classList.contains('mobile-sidebar-open')) closeMobileSidebar(); // Close main sidebar if open
        document.body.classList.add('mobile-toc-open');
        mobileTocToggle.setAttribute('aria-expanded', 'true');
        tocContainerElement.scrollTo(0, 0); // Scroll to top of ToC panel
        updateActiveLinkAndMarker(); // Ensure active marker is correct on open
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
    // Note: ToC link clicks are handled in section 2 to close the panel.

    // --- 7. Global Event Listeners (Overlay, Keyboard) ---
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