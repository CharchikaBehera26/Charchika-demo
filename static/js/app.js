const menuToggle = document.getElementById("menuToggle");
const navLinks = document.getElementById("navLinks");
if (menuToggle && navLinks) {
  menuToggle.addEventListener("click", () => {
    const isOpen = navLinks.classList.toggle("open");
    menuToggle.setAttribute("aria-expanded", String(isOpen));
  });
}

document.querySelectorAll(".flash").forEach(el => {
  setTimeout(() => { el.style.opacity = "0"; el.style.transform = "translateY(-8px)"; }, 4200);
  setTimeout(() => el.remove(), 4800);
});

const assistantInput = document.getElementById("assistantMessage");
if (assistantInput) {
  document.querySelectorAll("[data-assistant-prompt]").forEach(button => {
    button.addEventListener("click", () => {
      assistantInput.value = button.dataset.assistantPrompt;
      assistantInput.focus();
    });
  });
}

const mapElement = document.getElementById("artisanMap");
if (mapElement) {
  const mapNotice = document.getElementById("mapLoadNotice");
  const dataElement = document.getElementById("artisanMapData");

  if (!window.L) {
    mapNotice.textContent = "The map library did not load. Check your internet connection and reload.";
  } else {
    let artisans;
    try {
      artisans = JSON.parse(dataElement.textContent);
    } catch (error) {
      console.error("Could not read the artisan map data.", error);
      mapNotice.textContent = "Map locations could not be loaded. Please reload the page.";
    }

    if (Array.isArray(artisans)) {
      const map = window.L.map(mapElement).setView([20.3, 85.8], 7);
      const tileLayer = window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(map);
      const markers = [];

      tileLayer.on("tileerror", () => {
        mapNotice.textContent = "Map tiles could not be loaded. Check your internet connection.";
      });

      artisans.forEach(artisan => {
        const marker = window.L.marker([artisan.latitude, artisan.longitude]).addTo(map);
        const popup = document.createElement("div");
        const name = document.createElement("strong");
        const details = document.createElement("p");
        const profileLink = document.createElement("a");

        name.textContent = artisan.name;
        details.textContent = [artisan.craft, artisan.district].filter(Boolean).join(" · ");
        profileLink.href = `/artisans?q=${encodeURIComponent(artisan.name)}`;
        profileLink.textContent = "View artisan profile";
        popup.append(name, details, profileLink);
        marker.bindPopup(popup);
        markers.push(marker);
      });

      if (markers.length > 1) {
        map.fitBounds(window.L.featureGroup(markers).getBounds().pad(0.15), { maxZoom: 12 });
      } else if (markers.length === 1) {
        map.setView(markers[0].getLatLng(), 12);
      }

      mapNotice.textContent = "";
    }
  }
}
