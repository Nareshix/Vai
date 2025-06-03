document.addEventListener('DOMContentLoaded', () => {
    // --- Code Block Highlighting (Highlight.js) ---
if (typeof hljs !== 'undefined') {
    const codeHiliteDivs = document.querySelectorAll('div.codehilite');
    codeHiliteDivs.forEach(div => {
        const preElement = div.querySelector('pre');
        const codeElement = preElement ? preElement.querySelector('code') : null;

        if (codeElement) {
            let fullText = codeElement.textContent || codeElement.innerText || "";
            fullText = fullText.trim();
            const match = fullText.match(/^```(\S+)\s*\n([\s\S]*?)\n?```$/);

            if (match) {
                const language = match[1].toLowerCase();
                let actualCode = match[2];
                if (actualCode.endsWith('\n')) {
                    actualCode = actualCode.slice(0, -1);
                }
                codeElement.textContent = actualCode;
                codeElement.className = `language-${language}`; // Set class for hljs
                hljs.highlightElement(codeElement); // Apply highlighting markup
            } else {
                console.warn("Code block format not matched...");
            }
        }
    });
} else {
    console.warn('Highlight.js library (hljs) not loaded.');
}

// --- Highlight.js Theme Management ---
const highlightJsThemeLink = document.getElementById('highlight-js-theme'); // Make sure your <link> has this ID in HTML
const lightModeHighlightJsCdn = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css';
const darkModeHighlightJsCdn = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css';

function setHighlightJsTheme(currentThemeSetting) { // 'light' or 'dark'
    if (!highlightJsThemeLink) {
        console.warn('Highlight.js theme link element not found.');
        return;
    }
    if (currentThemeSetting === 'light') {
        highlightJsThemeLink.href = lightModeHighlightJsCdn;
    } else { // Assumes 'dark'
        highlightJsThemeLink.href = darkModeHighlightJsCdn;
    }
}
    // --- Initial Page Setup (Active Sidebar Link, Nav Buttons) ---
    const currentPath = window.location.pathname;
    const pathParts = currentPath.split('/').filter(Boolean);
    if (pathParts.length > 0) {
        const lastFolderSlug = pathParts[pathParts.length - 1];
        const lastFolderDisplayName = lastFolderSlug.replaceAll('-', ' ');
        const sidebarLinks = document.querySelectorAll('.sidebar-nav-links li a');
        for (const link of sidebarLinks) {
            if (link.textContent.trim().toLowerCase() === lastFolderDisplayName.toLowerCase()) {
                link.classList.add('active');
                const parentSection = link.closest('.sidebar-nav-section');
                if (parentSection && !parentSection.classList.contains('is-open')) {
                    parentSection.classList.add('is-open');
                    const content = parentSection.querySelector('.sidebar-section-content');
                    const toggleButton = parentSection.querySelector('.sidebar-section-toggle');
                    if (content) {
                        const calculatedHeight = content.scrollHeight + "px"; // Calculate once
                        content.style.maxHeight = calculatedHeight;
                        content.dataset.calculatedMaxHeight = calculatedHeight; // Store it
                    }
                    if (toggleButton) toggleButton.setAttribute('aria-expanded', 'true');
                }
                break;
            }
        }
    }

    const navButtons = document.querySelectorAll('.page-navigation-boxes .nav-box');
    navButtons.forEach(buttonElement => {
        if (buttonElement.tagName === 'BUTTON') {
            const linkElement = buttonElement.querySelector('a.nav-box-link');
            if (linkElement && linkElement.href) {
                buttonElement.addEventListener('click', (event) => {
                    if (!event.target.closest('a.nav-box-link')) {
                        window.location.href = linkElement.href;
                    }
                });
            }
        }
    });

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
    
    const searchResultsContainer = document.getElementById('searchResultsContainer');
    const searchHistoryContainer = document.createElement('div');
    searchHistoryContainer.id = 'searchHistoryContainer';
    searchHistoryContainer.className = 'search-history-container';
    if (searchResultsContainer && searchResultsContainer.parentNode) {
        searchResultsContainer.parentNode.insertBefore(searchHistoryContainer, searchResultsContainer);
    }

    // --- Sidebar Data ---
    let sidebarData = [];
    const sidebarDataElement = document.getElementById('sidebarDataJson');
    if (sidebarDataElement) {
        try {
            sidebarData = JSON.parse(sidebarDataElement.textContent);
        } catch (e) {
            console.error("Error parsing sidebar data:", e);
        }
    }

    // --- State Variables ---
    const THEME_KEY = 'user-preferred-theme';
    const tocSections = {};
    let isSearchModalActive = false;
    const SEARCH_HISTORY_KEY = 'docSearchHistory_v1';
    const MAX_HISTORY_ITEMS = 5;
    let searchHistory = JSON.parse(localStorage.getItem(SEARCH_HISTORY_KEY)) || [];
    let currentKeyboardFocusedIndex = -1;
    let searchIndexData = []; 

    // --- Configuration for Scroll Spy & Click Navigation ---
    const APP_HEADER_ELEMENT = document.querySelector('.app-header');
    let DYNAMIC_HEADER_OFFSET = APP_HEADER_ELEMENT ? APP_HEADER_ELEMENT.offsetHeight : 64;
    const DESIRED_TEXT_GAP_BELOW_HEADER = 16;
    const SCROLL_SPY_ACTIVATION_LEEWAY = 20;

    function updateDynamicHeaderOffset() {
        if (APP_HEADER_ELEMENT) {
            DYNAMIC_HEADER_OFFSET = APP_HEADER_ELEMENT.offsetHeight;
        }
    }
    window.addEventListener('resize', updateDynamicHeaderOffset);
    updateDynamicHeaderOffset();

    function updateBodyScrollAndOverlay() {
        const isMobileSidebarOpen = document.body.classList.contains('mobile-sidebar-open');
        const isMobileTocOpen = document.body.classList.contains('mobile-toc-open');
        const transitionDuration = 300;

        if (isMobileSidebarOpen || isMobileTocOpen || isSearchModalActive) {
            if (pageOverlay && (isMobileSidebarOpen || isMobileTocOpen)) {
                 if (pageOverlay.style.display !== 'block') {
                    pageOverlay.style.display = 'block';
                    requestAnimationFrame(() => { pageOverlay.style.opacity = '1'; });
                }
            }
            document.body.style.overflow = 'hidden';
        } else {
            if (pageOverlay) {
                pageOverlay.style.opacity = '0';
                setTimeout(() => {
                    if (!document.body.classList.contains('mobile-sidebar-open') &&
                        !document.body.classList.contains('mobile-toc-open') &&
                        !isSearchModalActive) {
                        pageOverlay.style.display = 'none';
                    }
                }, transitionDuration);
            }
            document.body.style.overflow = '';
        }
    }

    // --- 1. Theme Functionality ---
    function applyTheme(theme) {
        if (!htmlElement) return;
        htmlElement.classList.toggle('light-theme', theme === 'light');
        htmlElement.classList.toggle('dark-theme', theme === 'dark');
        if (themeToggleButton) themeToggleButton.setAttribute('aria-label', theme === 'light' ? 'Switch to Dark Theme' : 'Switch to Light Theme');
        setHighlightJsTheme(theme);
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
                    const paddingTop = parseFloat(getComputedStyle(sectionElement).paddingTop) || 0;
                    tocSections[sectionId] = { element: sectionElement, paddingTop: paddingTop };
                }
            }
        });
    }

    function updateActiveLinkAndMarker() {
        if (!mainScroller || !tocLinksContainer || !tocActiveMarker || tocLinks.length === 0) {
            if (tocActiveMarker) tocActiveMarker.style.opacity = '0';
            if (tocLinks) tocLinks.forEach(link => link.classList.remove('active'));
            return;
        }
        const sectionIds = Object.keys(tocSections);
        if (sectionIds.length === 0) {
            if (tocActiveMarker) tocActiveMarker.style.opacity = '0';
            tocLinks.forEach(link => link.classList.remove('active'));
            return;
        }
        const contentScrollTop = mainScroller.scrollTop;
        let currentSectionId = null;
        for (let i = sectionIds.length - 1; i >= 0; i--) {
            const id = sectionIds[i];
            const sectionData = tocSections[id];
            if (sectionData?.element) {
                const textVisibleStartingPoint = sectionData.element.offsetTop + sectionData.paddingTop;
                const targetScrollTopForSectionText = textVisibleStartingPoint - DYNAMIC_HEADER_OFFSET - DESIRED_TEXT_GAP_BELOW_HEADER;
                if (targetScrollTopForSectionText - SCROLL_SPY_ACTIVATION_LEEWAY <= contentScrollTop) {
                    currentSectionId = id;
                    break;
                }
            }
        }
        if (currentSectionId === null && sectionIds.length > 0) {
            const firstSectionData = tocSections[sectionIds[0]];
            if (firstSectionData?.element) {
               const textVisibleStartingPoint = firstSectionData.element.offsetTop + firstSectionData.paddingTop;
               const targetScrollTopForFirstSectionText = textVisibleStartingPoint - DYNAMIC_HEADER_OFFSET - DESIRED_TEXT_GAP_BELOW_HEADER;
               if (contentScrollTop < targetScrollTopForFirstSectionText + SCROLL_SPY_ACTIVATION_LEEWAY) {
                    currentSectionId = sectionIds[0];
               }
            }
            if (currentSectionId === null && contentScrollTop < (tocSections[sectionIds[0]]?.element.offsetTop || 0) ) { 
                currentSectionId = sectionIds[0]; 
            }
       }
        const epsilon = 5; 
        if ((mainScroller.scrollTop + mainScroller.clientHeight >= mainScroller.scrollHeight - epsilon) && sectionIds.length > 0) {
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
        if (activeLinkElement && tocContainerElement.scrollHeight > tocContainerElement.clientHeight) {
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
            const href = targetLink?.getAttribute('href');
            if (href?.startsWith('#')) {
                e.preventDefault();
                const targetId = href.substring(1);
                const sectionData = tocSections[targetId];
                if (sectionData?.element && mainScroller) {
                    const textVisibleStartingPoint = sectionData.element.offsetTop + sectionData.paddingTop;
                    const scrollToPosition = textVisibleStartingPoint - DYNAMIC_HEADER_OFFSET - DESIRED_TEXT_GAP_BELOW_HEADER;
                    mainScroller.scrollTo({ top: Math.max(0, scrollToPosition), behavior: 'smooth' });
                    if (history.pushState) {
                        history.pushState(null, null, href);
                    } else {
                        window.location.hash = href;
                    }
                }
                if (document.body.classList.contains('mobile-toc-open')) {
                    DMAN_closeMobileToc();
                }
            }
        });
    }
    if (mainScroller && tocLinks.length > 0) {
        mainScroller.addEventListener('scroll', updateActiveLinkAndMarker);
        setTimeout(updateActiveLinkAndMarker, 150); 
        window.addEventListener('resize', updateActiveLinkAndMarker);
        window.addEventListener('load', updateActiveLinkAndMarker);
    }

    // --- 3. Search Functionality ---
    function DMAN_saveSearchHistory(query) {
        if (!query || query.trim().length < 1) return;
        const cleanedQuery = query.trim();
        searchHistory = searchHistory.filter(item => item.toLowerCase() !== cleanedQuery.toLowerCase());
        searchHistory.unshift(cleanedQuery);
        if (searchHistory.length > MAX_HISTORY_ITEMS) {
            searchHistory = searchHistory.slice(0, MAX_HISTORY_ITEMS);
        }
        localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(searchHistory));
    }

    function DMAN_deleteSearchHistoryItem(queryToDelete, event) {
        event.stopPropagation();
        event.preventDefault();
        searchHistory = searchHistory.filter(item => item !== queryToDelete);
        localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(searchHistory));
        DMAN_displaySearchHistory();
        if (searchInput) searchInput.focus();
    }

    function DMAN_displaySearchHistory() {
        currentKeyboardFocusedIndex = -1;
        searchHistoryContainer.innerHTML = ''; 
        searchResultsContainer.innerHTML = '';
        if (searchHistory.length === 0) {
            searchHistoryContainer.style.display = 'none';
            searchResultsContainer.innerHTML = `<p class="search-results-placeholder">Start typing to see results.</p>`;
            return;
        }
        searchHistoryContainer.style.display = 'block';
        const historyTitle = document.createElement('p');
        historyTitle.className = 'search-history-title';
        historyTitle.textContent = 'Recent Searches';
        searchHistoryContainer.appendChild(historyTitle);
        const ul = document.createElement('ul');
        ul.className = 'search-history-list';
        searchHistory.forEach((query, index) => {
            const li = document.createElement('li');
            li.className = 'search-history-item';
            li.dataset.index = index;
            const querySpan = document.createElement('span');
            querySpan.className = 'search-history-query';
            querySpan.textContent = query;
            li.addEventListener('click', () => {
                if (searchInput) searchInput.value = query;
                DMAN_performSearch(query);
            });
            const deleteButton = document.createElement('button');
            deleteButton.className = 'search-history-delete';
            deleteButton.innerHTML = '×';
            deleteButton.setAttribute('aria-label', `Remove "${query}" from history`);
            deleteButton.addEventListener('click', (event) => DMAN_deleteSearchHistoryItem(query, event));
            li.appendChild(querySpan);
            li.appendChild(deleteButton);
            ul.appendChild(li);
        });
        searchHistoryContainer.appendChild(ul);
    }

    function DMAN_openSearchModal() {
        if (isSearchModalActive || !searchOverlayEl || !searchInput) return;
        isSearchModalActive = true;
        updateBodyScrollAndOverlay();
        requestAnimationFrame(() => {
            searchOverlayEl.classList.add('active');
            setTimeout(() => {
                searchInput.focus();
                if (searchInput.value.trim().length >= 1) {
                    DMAN_performSearch(searchInput.value);
                } else {
                    DMAN_displaySearchHistory();
                }
            }, 60);
        });
    }

    function DMAN_closeSearchModal() {
        if (!isSearchModalActive || !searchOverlayEl) return;
        isSearchModalActive = false; 
        if (searchOverlayEl) searchOverlayEl.classList.remove('active');
        if (searchInput) {
            searchInput.value = ''; 
            searchInput.blur();
        }
        if (searchTriggerButton) searchTriggerButton.focus({ preventScroll: true });
        searchResultsContainer.innerHTML = ''; 
        searchHistoryContainer.innerHTML = ''; 
        searchHistoryContainer.style.display = 'none';
        currentKeyboardFocusedIndex = -1; 
        updateBodyScrollAndOverlay();
    }
    
    async function DMAN_fetchSearchIndex() {
        try {
            const response = await fetch('/search_index.json');
            if (!response.ok) {
                console.error('Failed to load search index:', response.statusText);
                DMAN_clearSearchResultsDisplay("Search is currently unavailable.");
                return;
            }
            searchIndexData = await response.json();
            if (!searchInput || !searchInput.value.trim()) {
                 DMAN_clearSearchResultsDisplay("Start typing to see results.");
            }
        } catch (error) {
            console.error('Error fetching or parsing search index:', error);
            DMAN_clearSearchResultsDisplay("Error loading search. Please try again later.");
        }
    }
    
    function highlightText(text, query) {
        if (!text || !query || query.trim().length < 1) return String(text || ""); // Ensure text is string

        const trimmedQuery = query.trim();
        const originalText = String(text); // Work with original casing for output
        const lowerText = originalText.toLowerCase();
        const lowerQuery = trimmedQuery.toLowerCase();
        
        if (lowerQuery.length === 0) return originalText;

        const startIndex = lowerText.indexOf(lowerQuery);

        if (startIndex === -1) {
            return originalText; 
        }

        let resultHTML = originalText.substring(0, startIndex) +
                         "<mark>" + originalText.substring(startIndex, startIndex + trimmedQuery.length) + "</mark>" +
                         originalText.substring(startIndex + trimmedQuery.length);
        
        return resultHTML;
    }

    function generateSimpleSnippet(fullText, lowerQuery, originalQuery, maxLength = 150) {
        if (!fullText || !originalQuery) return "Preview not available.";
        const S_fullText = String(fullText); // Ensure it's a string
        const S_lowerQuery = String(lowerQuery || "").toLowerCase();

        if (S_lowerQuery.length === 0) {
             return highlightText(S_fullText.substring(0, maxLength) + (S_fullText.length > maxLength ? "..." : ""), originalQuery);
        }

        const lowerFullText = S_fullText.toLowerCase();
        let matchStartIndex = lowerFullText.indexOf(S_lowerQuery);

        if (matchStartIndex === -1) { 
            return highlightText(S_fullText.substring(0, maxLength) + (S_fullText.length > maxLength ? "..." : ""), originalQuery);
        }
        
        const queryActualLength = S_lowerQuery.length; // Use length of lowerQuery for calculations
        const snippetRadius = Math.floor((maxLength - queryActualLength) / 2);
        let snippetStart = Math.max(0, matchStartIndex - snippetRadius);
        let snippetEnd = Math.min(S_fullText.length, matchStartIndex + queryActualLength + snippetRadius);

        if (snippetStart > 0) {
            const spaceBefore = lowerFullText.lastIndexOf(" ", snippetStart -1);
            if (spaceBefore !== -1 && spaceBefore > snippetStart - 30) snippetStart = spaceBefore + 1;
        }
        if (snippetEnd < S_fullText.length) {
            const spaceAfter = lowerFullText.indexOf(" ", snippetEnd); 
            if (spaceAfter !== -1 && spaceAfter < snippetEnd + 30) snippetEnd = spaceAfter;
        }
        
        let snippetText = S_fullText.substring(snippetStart, snippetEnd);
        // Highlight using originalQuery to preserve its casing in the mark tag
        let highlightedSnippet = highlightText(snippetText, originalQuery); 

        return (snippetStart > 0 ? "..." : "") + highlightedSnippet + (snippetEnd < S_fullText.length ? "..." : "");
    }

    function DMAN_performSearch(query) {
        currentKeyboardFocusedIndex = -1;
        searchHistoryContainer.style.display = 'none';
    
        if (!searchIndexData || searchIndexData.length === 0 || !searchResultsContainer) {
            DMAN_clearSearchResultsDisplay("Search not ready or no data.");
            return;
        }
        const trimmedQuery = query.trim();
        const lowerQuery = trimmedQuery.toLowerCase();
    
        if (trimmedQuery.length === 0) {
            DMAN_displaySearchHistory();
            return;
        }
    
        let potentialResults = {}; 
    
        if (sidebarData && lowerQuery.length > 0) {
            sidebarData.forEach(section => {
                if (section.title.toLowerCase().startsWith(lowerQuery) && section.files && section.files.length > 0) {
                    const firstFile = section.files[0];
                    const url = `/${section.output_folder_name}/${firstFile.slug}/`;
                    if (!potentialResults[url] || 0.0001 < (potentialResults[url].score || 1)) {
                        potentialResults[url] = {
                            type: 'section', 
                            displayTitle: `Go to section: ${section.title}`,
                            url: url,
                            breadcrumbs: `Section: ${section.title}`,
                            snippet: `Access all content within the '${section.title}' section.`,
                            score: 0.0001,
                        };
                    }
                }
            });
        }
    
        searchIndexData.forEach(item => {
            if (item.searchable_text && item.searchable_text.includes(lowerQuery)) {
                let score;
                let isStartsWithMatch = false;
    
                if (item.type === 'heading') {
                    isStartsWithMatch = item.heading_text && String(item.heading_text).toLowerCase().startsWith(lowerQuery);
                    score = isStartsWithMatch ? 0.002 : 0.012; 
                } else if (item.type === 'page') {
                    isStartsWithMatch = item.page_title && String(item.page_title).toLowerCase().startsWith(lowerQuery);
                    if (isStartsWithMatch) {
                        score = 0.003;
                    } else {
                        isStartsWithMatch = item.breadcrumbs && String(item.breadcrumbs).toLowerCase().startsWith(lowerQuery);
                        score = isStartsWithMatch ? 0.004 : 0.014;
                    }
                } else {
                    score = 0.05; 
                }
                
                if (!potentialResults[item.url] || score < (potentialResults[item.url].score || 1)) {
                    let snippetSource = item.displayTitle; 
                    if (item.type === 'heading' && item.heading_text && String(item.heading_text).toLowerCase().includes(lowerQuery)) {
                        snippetSource = item.heading_text;
                    } else if (item.type === 'page' && item.page_title && String(item.page_title).toLowerCase().includes(lowerQuery)) {
                        snippetSource = item.page_title;
                    } else if (item.breadcrumbs && String(item.breadcrumbs).toLowerCase().includes(lowerQuery)) {
                         snippetSource = item.breadcrumbs;
                    }
    
                    potentialResults[item.url] = {
                        type: item.type,
                        displayTitle: item.displayTitle,
                        url: item.url,
                        breadcrumbs: item.breadcrumbs, // Store the raw breadcrumbs
                        snippet: generateSimpleSnippet(snippetSource, lowerQuery, trimmedQuery),
                        score: score,
                    };
                }
            }
        });
    
        let allDisplayItems = Object.values(potentialResults);
        allDisplayItems.sort((a, b) => (a.score || 1) - (b.score || 1));
                
        const resultsToDisplay = allDisplayItems.slice(0, 15);
        searchResultsContainer.innerHTML = '';
    
        if (resultsToDisplay.length === 0) {
            searchResultsContainer.innerHTML = `<p class="search-results-placeholder">No results found for "<strong></strong>"</p>`;
            searchResultsContainer.querySelector('strong').textContent = query;
            return;
        }
    
        const ul = document.createElement('ul');
        ul.className = 'search-results-list';
    
        resultsToDisplay.forEach((result, index) => {
            const li = document.createElement('li');
            li.className = 'search-result-item';
            if (result.type === 'section') li.classList.add('section-nav');
            else if (result.type === 'heading') li.classList.add('heading-nav');
            li.dataset.index = index;
    
            const a = document.createElement('a');
            a.href = result.url;
            a.addEventListener('click', (e) => {
                e.preventDefault();
                DMAN_saveSearchHistory(trimmedQuery);
                window.location.href = a.href;
                DMAN_closeSearchModal();
                if (searchInput) searchInput.value = '';
            });
    
            const titleDiv = document.createElement('div');
            titleDiv.className = 'search-result-title';
            titleDiv.innerHTML = highlightText(result.displayTitle, trimmedQuery); 
    
            const breadcrumbsDiv = document.createElement('div');
            breadcrumbsDiv.className = 'search-result-breadcrumbs';
            if (result.type === 'section') {
                breadcrumbsDiv.innerHTML = highlightText(result.breadcrumbs, trimmedQuery);
            } else {
                breadcrumbsDiv.textContent = result.breadcrumbs || ""; 
            }
            
            const snippetDiv = document.createElement('div');
            snippetDiv.className = 'search-result-snippet';
            snippetDiv.innerHTML = result.snippet; 
    
            a.appendChild(titleDiv);
            a.appendChild(breadcrumbsDiv);
            a.appendChild(snippetDiv);
            li.appendChild(a);
            ul.appendChild(li);
        });
    
        searchResultsContainer.appendChild(ul);
    } 
    
    function DMAN_clearSearchResultsDisplay(message = "Start typing to see results.") {
        if (searchResultsContainer) {
            if (searchHistoryContainer.style.display === 'block' && searchHistoryContainer.innerHTML !== '') {
                searchResultsContainer.innerHTML = '';
            } else {
                searchResultsContainer.innerHTML = `<p class="search-results-placeholder">${message}</p>`;
            }
        }
        if (message === "Start typing to see results." || message.startsWith("Enter at least")) {
             searchHistoryContainer.style.display = 'none';
        }
    }

    if (searchTriggerButton) searchTriggerButton.addEventListener('click', DMAN_openSearchModal);
    if (searchCloseButton) searchCloseButton.addEventListener('click', DMAN_closeSearchModal);
    if (searchOverlayEl) {
        searchOverlayEl.addEventListener('click', (e) => {
            if (e.target === searchOverlayEl) DMAN_closeSearchModal();
        });
    }

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value;
            if (query.trim().length > 0) {
                DMAN_performSearch(query);
            } else {
                DMAN_displaySearchHistory();
            }
        });

        searchInput.addEventListener('keydown', (e) => {
            const activeListContainer = searchHistoryContainer.style.display === 'block' ? searchHistoryContainer : searchResultsContainer;
            const itemsList = activeListContainer.querySelector('ul');
            const items = itemsList ? Array.from(itemsList.querySelectorAll('li[data-index]')) : [];

            if (e.key === 'ArrowDown') {
                if (items.length === 0) return; // If no items, do nothing
                e.preventDefault();
                currentKeyboardFocusedIndex = (currentKeyboardFocusedIndex + 1) % items.length;
                DMAN_updateKeyboardFocus(items, activeListContainer);

                // Optional: Update search input as user arrows through history
                if (activeListContainer === searchHistoryContainer && currentKeyboardFocusedIndex > -1) {
                    const focusedItemText = items[currentKeyboardFocusedIndex]?.querySelector('.search-history-query')?.textContent;
                    if (focusedItemText && searchInput) {
                        // searchInput.value = focusedItemText; // Uncomment if you want live input update
                    }
                }
            } else if (e.key === 'ArrowUp') {
                if (items.length === 0) return; // If no items, do nothing
                e.preventDefault();
                currentKeyboardFocusedIndex = (currentKeyboardFocusedIndex - 1 + items.length) % items.length;
                DMAN_updateKeyboardFocus(items, activeListContainer);

                // Optional: Update search input as user arrows through history
                if (activeListContainer === searchHistoryContainer && currentKeyboardFocusedIndex > -1) {
                    const focusedItemText = items[currentKeyboardFocusedIndex]?.querySelector('.search-history-query')?.textContent;
                    if (focusedItemText && searchInput) {
                        // searchInput.value = focusedItemText; // Uncomment if you want live input update
                    }
                }
            } 
            else if (e.key === 'Enter') {
                e.preventDefault();
                
                if (currentKeyboardFocusedIndex > -1 && items && items[currentKeyboardFocusedIndex]) {
                    const targetItem = items[currentKeyboardFocusedIndex];
                    
                    const linkElement = targetItem.querySelector('a');
                    if (linkElement && activeListContainer === searchResultsContainer) { 
                        linkElement.click(); 
                    } else if (activeListContainer === searchHistoryContainer) { 
                        const historyQuerySpan = targetItem.querySelector('.search-history-query');
                        if (historyQuerySpan && searchInput) {
                            const historyQueryText = historyQuerySpan.textContent;
                            searchInput.value = historyQueryText; 
                            DMAN_performSearch(historyQueryText); 
                        }
                    }
                } else {
                    const currentQuery = searchInput.value.trim();
                    if (currentQuery.length > 0) {
                        let tempPotentialResultsForEnter = {}; 
                        const lowerQueryForEnter = currentQuery.toLowerCase();
                        if (sidebarData && lowerQueryForEnter.length > 0) {
                            sidebarData.forEach(section => {
                                if (section.title.toLowerCase().startsWith(lowerQueryForEnter) && section.files && section.files.length > 0) {
                                    const url = `/${section.output_folder_name}/${section.files[0].slug}/`;
                                    if(!tempPotentialResultsForEnter[url] || 0.0001 < (tempPotentialResultsForEnter[url].score ||1)) {
                                        tempPotentialResultsForEnter[url] = { url: url, score: 0.0001 };
                                    }
                                }
                            });
                        }
                        searchIndexData.forEach(item => {
                            if (item.searchable_text && item.searchable_text.includes(lowerQueryForEnter)) { 
                                let score;
                                let itemUrl = item.url;
                                let isStartsWithMatch = false;

                                if (item.type === 'heading') {
                                    isStartsWithMatch = item.heading_text && String(item.heading_text).toLowerCase().startsWith(lowerQueryForEnter);
                                    score = isStartsWithMatch ? 0.002 : 0.012;
                                } else if (item.type === 'page') {
                                    isStartsWithMatch = item.page_title && String(item.page_title).toLowerCase().startsWith(lowerQueryForEnter);
                                    if (isStartsWithMatch) {
                                        score = 0.003;
                                    } else {
                                        isStartsWithMatch = item.breadcrumbs && String(item.breadcrumbs).toLowerCase().startsWith(lowerQueryForEnter);
                                        score = isStartsWithMatch ? 0.004 : 0.014;
                                    }
                                } else {
                                    score = 0.05; 
                                }
                                
                                if(!tempPotentialResultsForEnter[itemUrl] || score < (tempPotentialResultsForEnter[itemUrl].score || 1)) {
                                    tempPotentialResultsForEnter[itemUrl] = { url: itemUrl, score: score };
                                }
                            }
                        });
                        
                        let tempResultsArrayForEnter = Object.values(tempPotentialResultsForEnter);
                        tempResultsArrayForEnter.sort((a, b) => (a.score || 1) - (b.score || 1));
                        
                        if (tempResultsArrayForEnter.length === 1) {
                            const singleResultToNavigate = tempResultsArrayForEnter[0];
                            DMAN_saveSearchHistory(currentQuery);
                            window.location.href = singleResultToNavigate.url;
                            DMAN_closeSearchModal();
                            if (searchInput) searchInput.value = '';
                        } else {
                            DMAN_saveSearchHistory(currentQuery);
                            DMAN_performSearch(currentQuery); 
                            const firstDisplayedItem = searchResultsContainer.querySelector('li[data-index="0"]');
                            if (firstDisplayedItem && tempResultsArrayForEnter.length > 0) { // Check tempResultsArrayForEnter as well
                                 const displayedListItems = Array.from(searchResultsContainer.querySelectorAll('li[data-index]'));
                                currentKeyboardFocusedIndex = 0;
                                DMAN_updateKeyboardFocus(displayedListItems, searchResultsContainer);
                            }
                        }
                    }
                }
            }
        });
    } else {
        console.error('Search input element (#searchInput) not found!');
    }
     DMAN_fetchSearchIndex(); 

    function DMAN_updateKeyboardFocus(items, listContainer) {
        items.forEach((item, index) => {
            if (index === currentKeyboardFocusedIndex) {
                item.classList.add('focused');
                const itemRect = item.getBoundingClientRect();
                const containerRect = listContainer.getBoundingClientRect();
                if (itemRect.bottom > containerRect.bottom) {
                    item.scrollIntoView({ block: 'end', behavior: 'smooth' });
                } else if (itemRect.top < containerRect.top) {
                    item.scrollIntoView({ block: 'start', behavior: 'smooth' });
                }
            } else {
                item.classList.remove('focused');
            }
        });
    }

    // --- 4. Sidebar Accordion ---
    document.querySelectorAll('.sidebar-nav .sidebar-nav-section').forEach(section => {
        const toggleButton = section.querySelector('.sidebar-section-toggle');
        const content = section.querySelector('.sidebar-section-content');
        if (toggleButton && content) {
            // If section is already open on load (e.g. hardcoded class or set by initial setup)
            // and its height hasn't been calculated and stored yet.
            if (section.classList.contains('is-open')) {
                if (!content.dataset.calculatedMaxHeight) { // Check if not already set
                    const calculatedHeight = content.scrollHeight + "px";
                    content.style.maxHeight = calculatedHeight;
                    content.dataset.calculatedMaxHeight = calculatedHeight; // Store it
                } else {
                    // If already calculated (e.g., by the active link logic), ensure it's applied
                    content.style.maxHeight = content.dataset.calculatedMaxHeight;
                }
            }
    
            toggleButton.addEventListener('click', () => {
                const isOpen = section.classList.toggle('is-open');
                toggleButton.setAttribute('aria-expanded', isOpen.toString());
    
                if (isOpen) {
                    // If opening, check if we have a stored height
                    if (content.dataset.calculatedMaxHeight) {
                        content.style.maxHeight = content.dataset.calculatedMaxHeight; // Use stored height
                    } else {
                        // If no stored height (first time opening this section via click)
                        const calculatedHeight = content.scrollHeight + "px";
                        content.style.maxHeight = calculatedHeight;
                        content.dataset.calculatedMaxHeight = calculatedHeight; // Calculate and store
                    }
                } else {
                    content.style.maxHeight = "0px";
                }
            });
        }
    });

    // --- 5. Mobile Navigation (Main Sidebar) ---
    function DMAN_openMobileSidebar() {
        if (!leftSidebar || !mobileMenuToggle) return;
        if (document.body.classList.contains('mobile-toc-open')) DMAN_closeMobileToc();
        document.body.classList.add('mobile-sidebar-open');
        mobileMenuToggle.setAttribute('aria-expanded', 'true');
        leftSidebar.querySelector('.sidebar-nav')?.scrollTo(0, 0);
        updateBodyScrollAndOverlay();
    }
    function DMAN_closeMobileSidebar() {
        if (!leftSidebar || !mobileMenuToggle) return;
        document.body.classList.remove('mobile-sidebar-open');
        mobileMenuToggle.setAttribute('aria-expanded', 'false');
        updateBodyScrollAndOverlay();
    }
    if (mobileMenuToggle && leftSidebar) {
        mobileMenuToggle.addEventListener('click', () => {
            document.body.classList.contains('mobile-sidebar-open') ? DMAN_closeMobileSidebar() : DMAN_openMobileSidebar();
        });
    }
    if (leftSidebar) {
        leftSidebar.addEventListener('click', (event) => {
            if (event.target.closest('a') && document.body.classList.contains('mobile-sidebar-open')) {
                DMAN_closeMobileSidebar();
            }
        });
    }

    // --- 6. Mobile Table of Contents Panel ---
    function DMAN_openMobileToc() {
        if (!tocContainerElement || !mobileTocToggle) return;
        if (document.body.classList.contains('mobile-sidebar-open')) DMAN_closeMobileSidebar();
        document.body.classList.add('mobile-toc-open');
        mobileTocToggle.setAttribute('aria-expanded', 'true');
        tocContainerElement.scrollTo(0, 0);
        updateActiveLinkAndMarker(); 
        updateBodyScrollAndOverlay();
    }
    function DMAN_closeMobileToc() {
        if (!tocContainerElement || !mobileTocToggle) return;
        document.body.classList.remove('mobile-toc-open');
        mobileTocToggle.setAttribute('aria-expanded', 'false');
        updateBodyScrollAndOverlay();
    }
    if (mobileTocToggle && tocContainerElement) {
        mobileTocToggle.addEventListener('click', () => {
            document.body.classList.contains('mobile-toc-open') ? DMAN_closeMobileToc() : DMAN_openMobileToc();
        });
    }

    // --- 7. Global Event Listeners (Overlay, Keyboard) ---
    function isEditingContent(element) {
        const tagName = element?.tagName;
        return tagName === 'INPUT' || tagName === 'TEXTAREA' || element?.isContentEditable || element?.closest('input, textarea, [contenteditable="true"], [contenteditable=""]');
    }
    if (pageOverlay) {
        pageOverlay.addEventListener('click', () => {
            if (document.body.classList.contains('mobile-sidebar-open')) DMAN_closeMobileSidebar();
            if (document.body.classList.contains('mobile-toc-open')) DMAN_closeMobileToc();
        });
    }
    document.addEventListener('keydown', (e) => {
        if (e.key === '/' && !isSearchModalActive && !isEditingContent(document.activeElement)) {
            e.preventDefault(); DMAN_openSearchModal();
        }
        if (e.key === 'k' && (e.ctrlKey || e.metaKey) && !isEditingContent(document.activeElement)) {
            e.preventDefault(); isSearchModalActive ? DMAN_closeSearchModal() : DMAN_openSearchModal();
        }
        if (e.key === 'Escape') {
            if (isSearchModalActive) {
                e.preventDefault(); DMAN_closeSearchModal();
            } else if (document.body.classList.contains('mobile-sidebar-open')) {
                e.preventDefault(); DMAN_closeMobileSidebar();
            } else if (document.body.classList.contains('mobile-toc-open')) {
                e.preventDefault(); DMAN_closeMobileToc();
            }
        }
    });

    // --- Code Block Copy Button ---
    const codeBlocks = document.querySelectorAll('.codehilite');
    const copyIconSVG = `<svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>`;
    const copiedIconSVG = `<svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/></svg>`;

    codeBlocks.forEach(codeBlockContainer => {
        const preElement = codeBlockContainer.querySelector('pre');
        if (!preElement) return;
        const codeElement = preElement.querySelector('code');
        if (!codeElement) return;

        const copyButton = document.createElement('button');
        copyButton.className = 'copy-code-button';
        copyButton.innerHTML = copyIconSVG;
        copyButton.setAttribute('aria-label', 'Copy code to clipboard');
        copyButton.setAttribute('title', 'Copy code');
        codeBlockContainer.insertBefore(copyButton, preElement);

        copyButton.addEventListener('click', async () => {
            const codeToCopy = codeElement.innerText;
            try {
                await navigator.clipboard.writeText(codeToCopy);
                copyButton.innerHTML = copiedIconSVG;
                copyButton.setAttribute('title', 'Copied!');
                setTimeout(() => {
                    copyButton.innerHTML = copyIconSVG;
                    copyButton.setAttribute('title', 'Copy code');
                }, 2000);
            } catch (err) {
                console.error('Failed to copy code: ', err);
                copyButton.setAttribute('title', 'Error copying');
                 setTimeout(() => {
                    copyButton.innerHTML = copyIconSVG;
                    copyButton.setAttribute('title', 'Copy code');
                }, 2000);
            }
        });
    });
});