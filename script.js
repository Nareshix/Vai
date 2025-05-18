const sections = document.querySelectorAll('section');
const navLinks = document.querySelectorAll('nav a');

// This map will store visible ratio for each section
const visibleRatios = new Map();

// Options for Intersection Observer
const observerOptions = {
  root: null, // viewport
  rootMargin: '0px 0px -50% 0px', // Adjust for fixed header if you have one (here 50% offset from bottom)
  threshold: buildThresholdList()
};

// Helper to create threshold array from 0 to 1 with steps
function buildThresholdList() {
  let thresholds = [];
  for(let i=0; i<=100; i++) {
    thresholds.push(i/100);
  }
  return thresholds;
}

const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    visibleRatios.set(entry.target.id, entry.intersectionRatio);
  });

  // Find the section with the highest visible ratio
  let maxRatio = 0;
  let mostVisibleSectionId = null;
  for (const [id, ratio] of visibleRatios.entries()) {
    if (ratio > maxRatio) {
      maxRatio = ratio;
      mostVisibleSectionId = id;
    }
  }

  // Update nav links
  navLinks.forEach(link => {
    link.classList.toggle('active', link.getAttribute('href') === '#' + mostVisibleSectionId);
  });

}, observerOptions);

// Observe all sections
sections.forEach(section => {
  visibleRatios.set(section.id, 0);
  observer.observe(section);
});
