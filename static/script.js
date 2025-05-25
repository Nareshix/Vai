document.addEventListener('DOMContentLoaded', () => {
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
                    if (content) content.style.maxHeight = content.scrollHeight + "px";
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
    // Create searchHistoryContainer dynamically and insert it
    const searchHistoryContainer = document.createElement('div');
    searchHistoryContainer.id = 'searchHistoryContainer';
    searchHistoryContainer.className = 'search-history-container';
    if (searchResultsContainer && searchResultsContainer.parentNode) {
        searchResultsContainer.parentNode.insertBefore(searchHistoryContainer, searchResultsContainer);
    }


    // --- State Variables ---
    const THEME_KEY = 'user-preferred-theme';
    const tocSections = {};
    let isSearchModalActive = false;
    const SEARCH_HISTORY_KEY = 'docSearchHistory_v1'; // Added _v1 to potentially reset old history
    const MAX_HISTORY_ITEMS = 5;
    let searchHistory = JSON.parse(localStorage.getItem(SEARCH_HISTORY_KEY)) || [];
    let currentKeyboardFocusedIndex = -1;
    let searchIndexData = [];
    let fuseInstance = null;


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

        if (isMobileSidebarOpen || isMobileTocOpen || isSearchModalActive) { // Modified condition
            if (pageOverlay && (isMobileSidebarOpen || isMobileTocOpen)) { // Only show dark pageOverlay for mobile menus
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

    function updateActiveLinkAndMarker() { /* ... same as previous full script ... */
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


    if (tocLinksContainer) { /* ... same as previous full script ... */
        tocLinksContainer.addEventListener('click', (e) => {
            const targetLink = e.target.closest('a');
            if (targetLink?.getAttribute('href')?.startsWith('#')) {
                e.preventDefault(); 
                const targetId = targetLink.getAttribute('href').substring(1);
                const sectionData = tocSections[targetId];
                if (sectionData?.element && mainScroller) {
                    const textVisibleStartingPoint = sectionData.element.offsetTop + sectionData.paddingTop;
                    const scrollToPosition = textVisibleStartingPoint - DYNAMIC_HEADER_OFFSET - DESIRED_TEXT_GAP_BELOW_HEADER;
                    mainScroller.scrollTo({
                        top: Math.max(0, scrollToPosition),
                        behavior: 'smooth'
                    });
                }
                if (document.body.classList.contains('mobile-toc-open')) {
                    DMAN_closeMobileToc();
                }
            }
        });
    }

    if (mainScroller && tocLinks.length > 0) { /* ... same as previous full script ... */
        mainScroller.addEventListener('scroll', updateActiveLinkAndMarker);
        setTimeout(updateActiveLinkAndMarker, 150); 
        window.addEventListener('resize', updateActiveLinkAndMarker);
        window.addEventListener('load', updateActiveLinkAndMarker);
    }

    // --- 3. Search Functionality ---

    function DMAN_saveSearchHistory(query) {
        if (!query || query.trim().length < 1) return; // Don't save empty or too short queries
        const cleanedQuery = query.trim();
        
        // Remove existing instance of this query to move it to the top (case-insensitive check)
        searchHistory = searchHistory.filter(item => item.toLowerCase() !== cleanedQuery.toLowerCase());
        
        // Add the new query to the beginning of the array
        searchHistory.unshift(cleanedQuery);
        
        // Enforce the maximum number of history items
        if (searchHistory.length > MAX_HISTORY_ITEMS) {
            searchHistory = searchHistory.slice(0, MAX_HISTORY_ITEMS); // Keep only the first MAX_HISTORY_ITEMS
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
        searchResultsContainer.innerHTML = ''; // Clear results when showing history

        if (searchHistory.length === 0) {
            searchHistoryContainer.style.display = 'none';
            searchResultsContainer.innerHTML = `<p class="search-results-placeholder">Start typing to see results.</p>`;
            return;
        }
        
        searchHistoryContainer.style.display = 'block';
        // Add a title for the history section
        const historyTitle = document.createElement('p');
        historyTitle.className = 'search-history-title'; // For styling
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
            
            li.addEventListener('click', () => { // Make the whole li clickable
                if (searchInput) searchInput.value = query;
                DMAN_performSearch(query);
                DMAN_saveSearchHistory(query);
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
        updateBodyScrollAndOverlay(); // Handles body scroll and general overlay if needed

        requestAnimationFrame(() => {
            searchOverlayEl.classList.add('active'); // This is the (now transparent) search specific overlay
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
        isSearchModalActive = false; // Set this first
        if (searchOverlayEl) searchOverlayEl.classList.remove('active');
        if (searchInput) searchInput.blur();
        if (searchTriggerButton) searchTriggerButton.focus({ preventScroll: true });
        
        searchResultsContainer.innerHTML = '';
        searchHistoryContainer.style.display = 'none';
        updateBodyScrollAndOverlay();
    }
    
    async function DMAN_fetchSearchIndex() { /* ... same as previous full script ... */
        try {
            const response = await fetch('/search_index.json');
            if (!response.ok) {
                console.error('Failed to load search index:', response.statusText);
                DMAN_clearSearchResultsDisplay("Search is currently unavailable.");
                return;
            }
            searchIndexData = await response.json();
            const fuseOptions = {
                includeScore: true,
                includeMatches: true,
                shouldSort: true,
                threshold: 0.35, // Slightly more permissive
                location: 0,
                distance: 3000, // Increased distance
                maxPatternLength: 32,
                minMatchCharLength: 1, // Allow searching on 1 char with Fuse
                keys: [
                    { name: "title", weight: 0.4 },
                    { name: "headings.text", weight: 0.35 },
                    { name: "text_content", weight: 0.2 },
                    { name: "breadcrumbs", weight: 0.05 }
                ]
            };
            fuseInstance = new Fuse(searchIndexData, fuseOptions);
            if (!searchInput || !searchInput.value.trim()) { // If modal not open or input empty
                 DMAN_clearSearchResultsDisplay("Start typing to see results.");
            }
        } catch (error) {
            console.error('Error fetching or parsing search index:', error);
            DMAN_clearSearchResultsDisplay("Error loading search. Please try again later.");
        }
    }

    function highlightFuseMatch(text, indicesArray) { /* ... same as previous full script ... */
        if (!text || !indicesArray || indicesArray.length === 0) return text || "";
        let combinedIndices = [];
        indicesArray.forEach(matchIndices => {
            matchIndices.forEach(([start, end]) => combinedIndices.push({start, end}));
        });
        combinedIndices.sort((a, b) => a.start - b.start);
        let mergedIndices = [];
        if (combinedIndices.length > 0) {
            mergedIndices.push({...combinedIndices[0]});
            for (let i = 1; i < combinedIndices.length; i++) {
                let current = combinedIndices[i];
                let lastMerged = mergedIndices[mergedIndices.length - 1];
                if (current.start <= lastMerged.end + 1) {
                    lastMerged.end = Math.max(lastMerged.end, current.end);
                } else {
                    mergedIndices.push({...current});
                }
            }
        }
        let result = "";
        let lastIndex = 0;
        mergedIndices.forEach(({start, end}) => {
            result += text.substring(lastIndex, start);
            result += "<mark>" + text.substring(start, end + 1) + "</mark>";
            lastIndex = end + 1;
        });
        result += text.substring(lastIndex);
        return result;
    }
    
    function generateSnippet(fullText, matchIndices, query, maxLength = 150) { /* ... same as previous full script ... */
        if (!fullText) return "No preview available.";
        if (!matchIndices || matchIndices.length === 0 || !matchIndices[0] || matchIndices[0].length === 0) {
            return highlightText(fullText.substring(0, maxLength) + (fullText.length > maxLength ? "..." : ""), query);
        }
        const firstMatch = matchIndices[0][0]; // first [start, end] pair of the first matched region
        const matchStart = firstMatch[0];
        const matchEnd = firstMatch[1];
        const queryActualLength = (matchEnd - matchStart + 1); 
    
        const snippetRadius = Math.floor((maxLength - queryActualLength) / 2);
        let snippetStart = Math.max(0, matchStart - snippetRadius);
        let snippetEnd = Math.min(fullText.length, matchEnd + 1 + snippetRadius); // +1 because end is inclusive
    
        if (snippetStart > 0) {
            const spaceBefore = fullText.lastIndexOf(" ", snippetStart -1);
            if (spaceBefore !== -1 && spaceBefore > snippetStart - 30) snippetStart = spaceBefore + 1;
        }
        if (snippetEnd < fullText.length) {
            const spaceAfter = fullText.indexOf(" ", snippetEnd); 
            if (spaceAfter !== -1 && spaceAfter < snippetEnd + 30) snippetEnd = spaceAfter;
        }
        let snippetText = fullText.substring(snippetStart, snippetEnd);
        
        let highlightedSnippet = "";
        const relativeIndices = matchIndices.flatMap(region => 
            region.map(([start, end]) => [start - snippetStart, end - snippetStart])
                  .filter(([relStart, relEnd]) => relEnd >= 0 && relStart < snippetText.length) 
        );

        highlightedSnippet = highlightFuseMatch(snippetText, [relativeIndices.filter(arr => arr.length > 0 && arr[0] !== undefined && arr[1] !== undefined)]);

        return (snippetStart > 0 ? "..." : "") + highlightedSnippet + (snippetEnd < fullText.length ? "..." : "");
    }
    
    function highlightText(text, query) { /* ... same as previous full script ... */
        if (!text || !query || query.trim().length < 1) return text || ""; // Allow highlighting for 1 char
        const lowerText = text.toLowerCase();
        const lowerQuery = query.trim().toLowerCase(); // Trim query here too
        let startIndex = 0;
        let result = "";
        let pos = lowerText.indexOf(lowerQuery, startIndex);
        while (pos !== -1) {
            result += text.substring(startIndex, pos) + "<mark>" + text.substring(pos, pos + query.length) + "</mark>";
            startIndex = pos + query.length;
            pos = lowerText.indexOf(lowerQuery, startIndex);
        }
        result += text.substring(startIndex);
        return result;
    }

    function DMAN_performSearch(query) {
        currentKeyboardFocusedIndex = -1;
        searchHistoryContainer.style.display = 'none';

        if (!fuseInstance || !searchResultsContainer) {
            console.error('Fuse instance or results container not available!');
            return;
        }
        const trimmedQuery = query.trim(); // Use trimmed query for logic
        const lowerQuery = trimmedQuery.toLowerCase();

        if (trimmedQuery.length === 0) { // If input becomes empty (e.g. backspace all)
            DMAN_displaySearchHistory();
            return;
        }
        // No minimum length check here to allow searching on 1 char
        
        const fuseResults = fuseInstance.search(lowerQuery);
        searchResultsContainer.innerHTML = ''; 

        if (fuseResults.length === 0) {
            searchResultsContainer.innerHTML = `<p class="search-results-placeholder">No results found for "<strong></strong>"</p>`;
            searchResultsContainer.querySelector('strong').textContent = query; 
            return;
        }

        const ul = document.createElement('ul');
        ul.className = 'search-results-list';
        fuseResults.slice(0, 15).forEach((fuseResult, index) => {
            const item = fuseResult.item;
            let displayTitle = item.title;
            let displayUrl = item.url;
            let snippet = "No preview available.";
            let breadcrumbs = item.breadcrumbs || "";

            if (fuseResult.matches && fuseResult.matches.length > 0) {
                const bestMatch = fuseResult.matches[0]; 
                if (bestMatch.key === "headings.text" && item.headings && item.headings[bestMatch.refIndex]) {
                    const matchedHeading = item.headings[bestMatch.refIndex];
                    displayTitle = matchedHeading.text;
                    displayUrl = item.url + '#' + matchedHeading.slug;
                    snippet = highlightFuseMatch(matchedHeading.text, [bestMatch.indices]);
                    breadcrumbs = `${item.title} » ${highlightText(matchedHeading.text, trimmedQuery)}`;
                } else if (bestMatch.key === "title") {
                    displayTitle = item.title;
                    snippet = highlightFuseMatch(item.title, [bestMatch.indices]);
                } else if (bestMatch.key === "text_content" && item.text_content) {
                     snippet = generateSnippet(item.text_content, [bestMatch.indices], trimmedQuery);
                } else if (bestMatch.key === "breadcrumbs" && item.breadcrumbs) {
                    snippet = highlightFuseMatch(item.breadcrumbs, [bestMatch.indices]);
                }
            }
            
            if (snippet === "No preview available." && item.text_content) { 
                snippet = highlightText(item.text_content.substring(0, 120) + (item.text_content.length > 120 ? "..." : ""), trimmedQuery);
            }

            const li = document.createElement('li');
            li.className = 'search-result-item';
            li.dataset.index = index;
            const a = document.createElement('a');
            a.href = displayUrl;
            a.addEventListener('click', (e) => {
                e.preventDefault();
                DMAN_saveSearchHistory(trimmedQuery); // Save the performed search query
                window.location.href = a.href;
                DMAN_closeSearchModal(); 
                if (searchInput) searchInput.value = ''; 
            });

            const titleDiv = document.createElement('div');
            titleDiv.className = 'search-result-title';
            titleDiv.innerHTML = highlightText(displayTitle, trimmedQuery); 

            const breadcrumbsDiv = document.createElement('div');
            breadcrumbsDiv.className = 'search-result-breadcrumbs';
            if (!(fuseResult.matches && fuseResult.matches[0].key === "headings.text")) {
                breadcrumbsDiv.innerHTML = highlightText(breadcrumbs, trimmedQuery);
            } else {
                breadcrumbsDiv.innerHTML = breadcrumbs; 
            }

            const snippetDiv = document.createElement('div');
            snippetDiv.className = 'search-result-snippet';
            snippetDiv.innerHTML = snippet; 

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
            // Check if it's already showing history; if so, don't overwrite with this generic message
            if (searchHistoryContainer.style.display === 'block' && searchHistoryContainer.innerHTML !== '') {
                searchResultsContainer.innerHTML = ''; // Just clear results, history title is in its own container
            } else {
                searchResultsContainer.innerHTML = `<p class="search-results-placeholder">${message}</p>`;
            }
        }
        // Only hide history if we are truly clearing for a generic message, not when history itself IS the display
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
            const query = e.target.value; // Don't trim here, let performSearch handle it
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
                if (items.length === 0) return; // No items to navigate
                e.preventDefault();
                currentKeyboardFocusedIndex = (currentKeyboardFocusedIndex + 1) % items.length;
                DMAN_updateKeyboardFocus(items, activeListContainer);
            } else if (e.key === 'ArrowUp') {
                if (items.length === 0) return; // No items to navigate
                e.preventDefault();
                currentKeyboardFocusedIndex = (currentKeyboardFocusedIndex - 1 + items.length) % items.length;
                DMAN_updateKeyboardFocus(items, activeListContainer);
            } else if (e.key === 'Enter') {
                e.preventDefault(); // Prevent default form submission if any

                const currentQuery = searchInput.value.trim();

                // Case 1: A specific item is focused by keyboard navigation
                if (currentKeyboardFocusedIndex > -1 && items && items[currentKeyboardFocusedIndex]) {
                    const targetItem = items[currentKeyboardFocusedIndex];
                    if (targetItem.classList.contains('search-history-item')) {
                        targetItem.click(); // Simulate click on history item
                    } else if (targetItem.classList.contains('search-result-item')) {
                        const linkElement = targetItem.querySelector('a');
                        if (linkElement) linkElement.click(); // Simulate click on search result link
                    }
                }
                // Case 2: No item is focused, but user pressed Enter in the input
                else if (currentQuery.length > 0) {
                    // Perform the search again to get the latest results count for the current query
                    // This is important because 'items' might be from a previous render (e.g. history)
                    if (fuseInstance) {
                        const fuseResultsForEnter = fuseInstance.search(currentQuery.toLowerCase());
                        
                        if (fuseResultsForEnter.length === 1) {
                            // Only one result, navigate directly

                            const itemToNavigate = fuseResultsForEnter[0].item;
                            let navigateUrl = itemToNavigate.url;

                            // Check if the best match was a heading to append slug
                            const bestMatch = fuseResultsForEnter[0].matches && fuseResultsForEnter[0].matches[0];
                            if (bestMatch && bestMatch.key === "headings.text" && itemToNavigate.headings && itemToNavigate.headings[bestMatch.refIndex]) {
                                const heading = itemToNavigate.headings[bestMatch.refIndex];
                                navigateUrl += '#' + heading.slug;
                            }
                            
                            DMAN_saveSearchHistory(currentQuery); // Save this query to history
                            window.location.href = navigateUrl;  // Navigate
                            DMAN_closeSearchModal();
                            if (searchInput) searchInput.value = '';

                        } else if (fuseResultsForEnter.length > 1) {
                            // More than one result:
                            // Just save to history. The results are already displayed.
                            DMAN_saveSearchHistory(currentQuery);
                            // Optionally, focus the first actual search result item if results are shown
                            const searchResultListItems = searchResultsContainer.querySelectorAll('li.search-result-item[data-index]');
                            if (searchResultListItems.length > 0) {
                                currentKeyboardFocusedIndex = 0; // Focus the first search result
                                DMAN_updateKeyboardFocus(Array.from(searchResultListItems), searchResultsContainer);
                            }
                        } else { // Zero results
                             DMAN_saveSearchHistory(currentQuery);
                        }
                    }
                }
                // Case 3: Enter pressed with empty input (does nothing for now)
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
                // Smart scroll into view
                const itemRect = item.getBoundingClientRect();
                const containerRect = listContainer.getBoundingClientRect(); // Use the specific list container
                
                if (itemRect.bottom > containerRect.bottom) {
                    item.scrollIntoView({ block: 'end', behavior: 'smooth' });
                } else if (itemRect.top < containerRect.top) {
                    item.scrollIntoView({ block: 'start', behavior: 'smooth' });
                }
                // If already visible, no scroll, or use 'nearest' if preferred
                // item.scrollIntoView({ block: 'nearest', behavior: 'smooth' });


            } else {
                item.classList.remove('focused');
            }
        });
    }

    // --- 4. Sidebar Accordion ---
    document.querySelectorAll('.sidebar-nav .sidebar-nav-section').forEach(section => { /* ... same as previous full script ... */
        const toggleButton = section.querySelector('.sidebar-section-toggle');
        const content = section.querySelector('.sidebar-section-content');
        if (toggleButton && content) {
            if (section.classList.contains('is-open')) {
                 content.style.maxHeight = content.scrollHeight + "px";
            }
            toggleButton.addEventListener('click', () => {
                const isOpen = section.classList.toggle('is-open');
                toggleButton.setAttribute('aria-expanded', isOpen.toString());
                content.style.maxHeight = isOpen ? content.scrollHeight + "px" : "0px";
            });
        }
    });

    // --- 5. Mobile Navigation (Main Sidebar) ---
    function DMAN_openMobileSidebar() { /* ... same as previous full script ... */
        if (!leftSidebar || !mobileMenuToggle) return;
        if (document.body.classList.contains('mobile-toc-open')) DMAN_closeMobileToc();
        document.body.classList.add('mobile-sidebar-open');
        mobileMenuToggle.setAttribute('aria-expanded', 'true');
        leftSidebar.querySelector('.sidebar-nav')?.scrollTo(0, 0);
        updateBodyScrollAndOverlay();
    }
    function DMAN_closeMobileSidebar() { /* ... same as previous full script ... */
        if (!leftSidebar || !mobileMenuToggle) return;
        document.body.classList.remove('mobile-sidebar-open');
        mobileMenuToggle.setAttribute('aria-expanded', 'false');
        updateBodyScrollAndOverlay();
    }
    if (mobileMenuToggle && leftSidebar) { /* ... same as previous full script ... */
        mobileMenuToggle.addEventListener('click', () => {
            document.body.classList.contains('mobile-sidebar-open') ? DMAN_closeMobileSidebar() : DMAN_openMobileSidebar();
        });
    }
    if (leftSidebar) { /* ... same as previous full script ... */
        leftSidebar.addEventListener('click', (event) => {
            if (event.target.closest('a') && document.body.classList.contains('mobile-sidebar-open')) {
                DMAN_closeMobileSidebar();
            }
        });
    }

    // --- 6. Mobile Table of Contents Panel ---
    function DMAN_openMobileToc() { /* ... same as previous full script ... */
        if (!tocContainerElement || !mobileTocToggle) return;
        if (document.body.classList.contains('mobile-sidebar-open')) DMAN_closeMobileSidebar();
        document.body.classList.add('mobile-toc-open');
        mobileTocToggle.setAttribute('aria-expanded', 'true');
        tocContainerElement.scrollTo(0, 0);
        updateActiveLinkAndMarker(); 
        updateBodyScrollAndOverlay();
    }
    function DMAN_closeMobileToc() { /* ... same as previous full script ... */
        if (!tocContainerElement || !mobileTocToggle) return;
        document.body.classList.remove('mobile-toc-open');
        mobileTocToggle.setAttribute('aria-expanded', 'false');
        updateBodyScrollAndOverlay();
    }
    if (mobileTocToggle && tocContainerElement) { /* ... same as previous full script ... */
        mobileTocToggle.addEventListener('click', () => {
            document.body.classList.contains('mobile-toc-open') ? DMAN_closeMobileToc() : DMAN_openMobileToc();
        });
    }

    // --- 7. Global Event Listeners (Overlay, Keyboard) ---
    function isEditingContent(element) { /* ... same as previous full script ... */
        const tagName = element?.tagName;
        return tagName === 'INPUT' || tagName === 'TEXTAREA' || element?.isContentEditable || element?.closest('input, textarea, [contenteditable="true"], [contenteditable=""]');
    }
    if (pageOverlay) { /* ... same as previous full script ... */
        pageOverlay.addEventListener('click', () => {
            if (document.body.classList.contains('mobile-sidebar-open')) DMAN_closeMobileSidebar();
            if (document.body.classList.contains('mobile-toc-open')) DMAN_closeMobileToc();
            // Removed direct call to DMAN_closeSearchModal from pageOverlay click, 
            // as .search-overlay (which is transparent) handles its own click-outside.
        });
    }
    document.addEventListener('keydown', (e) => { /* ... same as previous full script, ensures DMAN_ functions are called ... */
        if (e.key === '/' && !isSearchModalActive && !isEditingContent(document.activeElement)) {
            e.preventDefault(); DMAN_openSearchModal();
        }
        if (e.key === 'k' && (e.ctrlKey || e.metaKey) && !isEditingContent(document.activeElement)) { // Added !isEditingContent
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
    const codeBlocks = document.querySelectorAll('.codehilite'); /* ... same as previous full script ... */
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