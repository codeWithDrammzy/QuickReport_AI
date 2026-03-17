// static/js/app.js

document.addEventListener("DOMContentLoaded", () => {
  // --- SPLASH SCREEN LOGIC ---
  const splash = document.getElementById("splash");
  const main = document.getElementById("main");

  if (splash && main) {
    // Show splash screen first
    splash.style.display = "flex";
    main.classList.add("hidden");

    // Wait 2.5 seconds, then fade out splash and show main
    setTimeout(() => {
      splash.classList.add("opacity-0", "transition-opacity", "duration-1000");

      setTimeout(() => {
        splash.style.display = "none";
        main.classList.remove("hidden");
        main.classList.add("animate-fade-in");
      }, 1000);
    }, 2500);
  }

  // --- PROFILE DROPDOWN LOGIC ---
  const profileBtn = document.getElementById("profileBtn");
  const dropdownMenu = document.getElementById("dropdownMenu");

  if (profileBtn && dropdownMenu) {
    profileBtn.addEventListener("click", (e) => {
      e.stopPropagation(); // Prevent click from bubbling up
      dropdownMenu.classList.toggle("hidden");
    });

    // Close dropdown when clicking outside
    document.addEventListener("click", (e) => {
      if (!profileBtn.contains(e.target) && !dropdownMenu.contains(e.target)) {
        dropdownMenu.classList.add("hidden");
      }
    });
  }
});
