const menuToggle = document.getElementById("menuToggle");
const navLinks = document.getElementById("navLinks");
const backTab = document.getElementById("backTab");
if (backTab) {
  backTab.addEventListener("click", () => {
    if (window.history.length > 1) window.history.back();
    else window.location.href = "/";
  });
}
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

  const assistantForm = document.getElementById("assistantForm");
  const assistantTranscript = document.querySelector(".chat-transcript");
  const voiceInput = document.getElementById("voiceInput");
  const voiceStatus = document.getElementById("voiceStatus");
  const languageSelect = document.getElementById("assistantLang");
  const speechLocale = () => ({
    en: "en-IN",
    hi: "hi-IN",
    or: "or-IN",
  }[languageSelect.value] || "en-IN");

  function speakAnswer(text) {
    if (!window.speechSynthesis || !window.SpeechSynthesisUtterance) {
      voiceStatus.textContent = voiceStatus.dataset.speechUnsupported;
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new window.SpeechSynthesisUtterance(text);
    utterance.lang = speechLocale();
    window.speechSynthesis.speak(utterance);
  }

  function addChatMessage(text, kind) {
    const message = document.createElement("div");
    message.className = `chat-message ${kind}`;
    message.textContent = text;
    assistantTranscript.appendChild(message);
    return message;
  }

  function addAnswerAudioButton(answer) {
    const button = document.createElement("button");
    button.className = "btn btn-outline answer-audio";
    button.type = "button";
    button.textContent = voiceStatus.dataset.listenLabel;
    button.addEventListener("click", () => speakAnswer(answer));
    assistantTranscript.appendChild(button);
  }

  assistantForm.addEventListener("submit", async event => {
    event.preventDefault();
    const submitButton = assistantForm.querySelector('button[type="submit"]');
    const message = assistantInput.value.trim();
    if (!message) return;

    submitButton.disabled = true;
    voiceStatus.textContent = voiceStatus.dataset.preparing;
    try {
      const response = await fetch(assistantForm.action, {
        method: "POST",
        body: new FormData(assistantForm),
        headers: {
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
      });
      const result = await response.json();
      if (!response.ok) {
        voiceStatus.textContent = result.error || voiceStatus.dataset.service;
        return;
      }

      addChatMessage(result.message, "user");
      addChatMessage(result.answer, "bot");
      addAnswerAudioButton(result.answer);
      if (result.actions && result.actions.length) {
        const actions = document.createElement("nav");
        actions.className = "chat-actions";
        actions.setAttribute("aria-label", voiceStatus.dataset.suggestedLabel);
        result.actions.forEach(action => {
          const link = document.createElement("a");
          link.className = "btn btn-green";
          link.href = action.url;
          link.textContent = `${action.label} →`;
          actions.appendChild(link);
        });
        assistantTranscript.appendChild(actions);
      }
      assistantInput.value = "";
      voiceStatus.textContent = "";
      speakAnswer(result.answer);
      assistantTranscript.scrollTop = assistantTranscript.scrollHeight;
    } catch (error) {
      console.error("Could not send the guide message.", error);
      assistantForm.submit();
    } finally {
      submitButton.disabled = false;
    }
  });

  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) {
    voiceInput.disabled = true;
    voiceStatus.textContent = voiceStatus.dataset.unsupported;
  } else {
    voiceInput.addEventListener("click", () => {
      const recognition = new Recognition();
      recognition.lang = speechLocale();
      recognition.continuous = false;
      recognition.interimResults = false;
      voiceInput.disabled = true;
      voiceStatus.textContent = voiceStatus.dataset.listening;
      recognition.onresult = event => {
        const transcript = event.results[0][0].transcript.trim();
        if (transcript) {
          assistantInput.value = transcript;
          assistantForm.requestSubmit();
        } else {
          voiceStatus.textContent = voiceStatus.dataset.noSpeech;
        }
      };
      recognition.onerror = event => {
        if (event.error === "not-allowed" || event.error === "service-not-allowed") {
          voiceStatus.textContent = voiceStatus.dataset.denied;
        } else if (event.error === "no-speech") {
          voiceStatus.textContent = voiceStatus.dataset.noSpeech;
        } else {
          voiceStatus.textContent = voiceStatus.dataset.service;
        }
      };
      recognition.onend = () => {
        voiceInput.disabled = false;
      };
      try {
        recognition.start();
      } catch (error) {
        console.error("Could not start browser speech recognition.", error);
        voiceInput.disabled = false;
        voiceStatus.textContent = voiceStatus.dataset.service;
      }
    });
  }

  const existingAnswer = document.getElementById("chatAnswer");
  const listenAnswer = document.getElementById("listenAnswer");
  if (existingAnswer && listenAnswer) {
    listenAnswer.addEventListener("click", () => {
      speakAnswer(existingAnswer.textContent);
    });
  }
}

const mapElement = document.getElementById("artisanMap");
if (mapElement) {
  const mapNotice = document.getElementById("mapLoadNotice");
  const locationStatus = document.getElementById("locationStatus");
  const locateButton = document.getElementById("locateMe");
  const dataElement = document.getElementById("artisanMapData");
  const mapMessages = document.getElementById("mapMessages");

  if (!window.L) {
    mapNotice.textContent = mapMessages.dataset.mapLibraryError;
    locateButton.disabled = true;
  } else {
    let artisans;
    try {
      artisans = JSON.parse(dataElement.textContent);
    } catch (error) {
      console.error("Could not read the artisan map data.", error);
      mapNotice.textContent = mapMessages.dataset.mapDataError;
    }

    if (Array.isArray(artisans)) {
      const map = window.L.map(mapElement).setView([20.3, 85.8], 7);
      const tileLayer = window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(map);
      const markers = [];
      let currentLocationMarker;

      tileLayer.on("tileerror", () => {
        mapNotice.textContent = mapMessages.dataset.tileError;
      });

      artisans.forEach(artisan => {
        const marker = window.L.marker([artisan.latitude, artisan.longitude]).addTo(map);
        const popup = document.createElement("div");
        const name = document.createElement("strong");
        const details = document.createElement("p");
        const profileLink = document.createElement("a");
        const distanceText = document.createElement("p");

        name.textContent = artisan.name;
        details.textContent = [artisan.craft, artisan.district].filter(Boolean).join(" · ");
        distanceText.className = "artisan-distance-popup";
        profileLink.href = `/artisans?q=${encodeURIComponent(artisan.name)}`;
        profileLink.textContent = "View artisan profile";
        popup.append(name, details, distanceText, profileLink);
        marker.bindPopup(popup);
        markers.push({ marker, artisan, distanceText });
      });

      if (markers.length > 1) {
        map.fitBounds(
          window.L.featureGroup(markers.map(item => item.marker)).getBounds().pad(0.15),
          { maxZoom: 12 }
        );
      } else if (markers.length === 1) {
        map.setView(markers[0].marker.getLatLng(), 12);
      }

      mapNotice.textContent = "";

      function distanceInKilometers(fromLatitude, fromLongitude, toLatitude, toLongitude) {
        const radians = value => value * Math.PI / 180;
        const latitudeDifference = radians(toLatitude - fromLatitude);
        const longitudeDifference = radians(toLongitude - fromLongitude);
        const arc = Math.sin(latitudeDifference / 2) ** 2
          + Math.cos(radians(fromLatitude))
          * Math.cos(radians(toLatitude))
          * Math.sin(longitudeDifference / 2) ** 2;
        return 6371 * 2 * Math.atan2(Math.sqrt(arc), Math.sqrt(1 - arc));
      }

      locateButton.addEventListener("click", () => {
        if (!navigator.geolocation) {
          locationStatus.textContent = mapMessages.dataset.locationUnavailable;
          return;
        }

        locateButton.disabled = true;
        locationStatus.textContent = mapMessages.dataset.locationFinding;
        navigator.geolocation.getCurrentPosition(
          position => {
            const latitude = position.coords.latitude;
            const longitude = position.coords.longitude;
            if (currentLocationMarker) map.removeLayer(currentLocationMarker);
            currentLocationMarker = window.L.circleMarker([latitude, longitude], {
              radius: 9,
              color: "#175fbb",
              weight: 3,
              fillColor: "#4b9bff",
              fillOpacity: 0.9,
            }).addTo(map).bindPopup("Your current location");
            map.setView([latitude, longitude], 12);

            markers.forEach(({ artisan, distanceText }) => {
              const distance = distanceInKilometers(
                latitude,
                longitude,
                artisan.latitude,
                artisan.longitude
              );
              distanceText.textContent = `${distance.toFixed(1)} km from your location`;
            });

            const resultList = document.querySelector(".map-results ul");
            if (resultList) {
              const nearbyPins = Array.from(resultList.children).map(item => {
                const distance = distanceInKilometers(
                  latitude,
                  longitude,
                  Number(item.dataset.lat),
                  Number(item.dataset.lng)
                );
                item.querySelector(".artisan-distance").textContent =
                  `${distance.toFixed(1)} km away`;
                return { item, distance };
              });
              nearbyPins
                .sort((left, right) => left.distance - right.distance)
                .forEach(({ item }) => resultList.appendChild(item));
            }

            locationStatus.textContent = mapMessages.dataset.locationFound;
            locateButton.disabled = false;
          },
          error => {
            if (error.code === error.PERMISSION_DENIED) {
              locationStatus.textContent = mapMessages.dataset.locationDenied;
            } else if (error.code === error.POSITION_UNAVAILABLE) {
              locationStatus.textContent = mapMessages.dataset.locationFailed;
            } else {
              locationStatus.textContent = mapMessages.dataset.locationTimeout;
            }
            locateButton.disabled = false;
          },
          { enableHighAccuracy: false, maximumAge: 60000, timeout: 10000 }
        );
      });
    }
  }
}
