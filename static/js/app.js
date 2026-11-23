const menuToggle = document.getElementById("menuToggle");
const navLinks = document.getElementById("navLinks");
const navBackdrop = document.getElementById("navBackdrop");
const backTab = document.getElementById("backTab");
if (backTab) {
  backTab.addEventListener("click", () => {
    if (window.history.length > 1) window.history.back();
    else window.location.href = "/";
  });
}
function closeNav() {
  if (navLinks && navLinks.classList.contains("open")) {
    navLinks.classList.remove("open");
    if (menuToggle) menuToggle.setAttribute("aria-expanded", "false");
    if (navBackdrop) navBackdrop.classList.remove("open");
  }
}
if (menuToggle && navLinks) {
  menuToggle.addEventListener("click", () => {
    const isOpen = navLinks.classList.toggle("open");
    menuToggle.setAttribute("aria-expanded", String(isOpen));
    if (navBackdrop) navBackdrop.classList.toggle("open", isOpen);
  });
}
if (navBackdrop) {
  navBackdrop.addEventListener("click", closeNav);
}
document.addEventListener("click", event => {
  if (
    navLinks &&
    navLinks.classList.contains("open") &&
    !navLinks.contains(event.target) &&
    menuToggle &&
    !menuToggle.contains(event.target)
  ) {
    closeNav();
  }
});

function showCartToast(message) {
  let toast = document.getElementById("cartToast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "cartToast";
    toast.className = "cart-toast";
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => {
    toast.classList.remove("show");
  }, 3500);
}

document.querySelectorAll(".add-cart-form").forEach(form => {
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const button = form.querySelector('button[type="submit"]');
    const originalText = button ? button.textContent : "";
    if (button) {
      button.disabled = true;
      button.textContent = "…";
    }
    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "Accept": "application/json",
        },
      });
      const data = await response.json();
      if (response.ok && data.status === "success") {
        if (button) {
          button.textContent = "✓ Added";
          setTimeout(() => {
            button.textContent = originalText;
            button.disabled = false;
          }, 1400);
        }
        document.querySelectorAll('a[href*="/shop/cart"]').forEach(link => {
          const match = link.textContent.match(/^[^\(]+/);
          const prefix = match ? match[0].trim() : "Cart";
          link.textContent = `${prefix} (${data.cart_count})`;
        });
        showCartToast(data.message || "Added to cart.");
      } else {
        if (button) {
          button.textContent = originalText;
          button.disabled = false;
        }
        form.submit();
      }
    } catch (err) {
      console.error("Cart AJAX error, submitting normally.", err);
      form.submit();
    }
  });
});

const assistantToggle = document.getElementById("assistantToggle");
const assistantPopover = document.getElementById("assistantPopover");
const assistantClose = document.getElementById("assistantClose");
if (assistantToggle && assistantPopover && assistantClose) {
  const assistantFrame = assistantPopover.querySelector("iframe");
  const setAssistantOpen = isOpen => {
    assistantPopover.hidden = !isOpen;
    assistantToggle.setAttribute("aria-expanded", String(isOpen));
    if (isOpen) {
      if (assistantFrame.dataset.src) {
        assistantFrame.src = assistantFrame.dataset.src;
        delete assistantFrame.dataset.src;
      }
      assistantClose.focus();
    }
    else assistantToggle.focus();
  };

  assistantToggle.addEventListener("click", () => {
    setAssistantOpen(assistantPopover.hidden);
  });
  document.querySelectorAll(".assistant-open-link").forEach(link => {
    link.addEventListener("click", event => {
      event.preventDefault();
      if (navLinks && menuToggle) {
        navLinks.classList.remove("open");
        menuToggle.setAttribute("aria-expanded", "false");
      }
      setAssistantOpen(true);
    });
  });
  assistantClose.addEventListener("click", () => setAssistantOpen(false));
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && !assistantPopover.hidden) setAssistantOpen(false);
  });
}

function showCartFeedback(message, kind) {
  let flashWrap = document.querySelector(".flash-wrap");
  if (!flashWrap) {
    flashWrap = document.createElement("div");
    flashWrap.className = "flash-wrap";
    document.body.appendChild(flashWrap);
  }
  const flash = document.createElement("div");
  flash.className = `flash ${kind}`;
  flash.setAttribute("role", "status");
  flash.textContent = message;
  flashWrap.appendChild(flash);
  setTimeout(() => {
    flash.style.opacity = "0";
    flash.style.transform = "translateY(-8px)";
  }, 4200);
  setTimeout(() => flash.remove(), 4800);
}

document.querySelectorAll(".add-cart-form").forEach(form => {
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const submitButton = form.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: {
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
      });
      const result = await response.json();
      if (!response.ok) {
        showCartFeedback(result.error, "error");
        return;
      }

      const cartCount = document.querySelector("[data-cart-count]");
      if (cartCount) cartCount.textContent = result.cart_count ? ` (${result.cart_count})` : "";
      showCartFeedback(result.message, "success");
    } catch (error) {
      console.error("Could not add the product to the cart.", error);
      showCartFeedback(form.dataset.requestError, "error");
    } finally {
      submitButton.disabled = false;
    }
  });
});

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
          link.target = "_top";
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
    let activeVoiceSession = null;

    function resetVoiceInput() {
      voiceInput.textContent = voiceInput.dataset.speakLabel;
      voiceInput.setAttribute("aria-pressed", "false");
    }

    function clearSilenceTimer(session) {
      if (session.silenceTimer) {
        window.clearTimeout(session.silenceTimer);
        session.silenceTimer = null;
      }
    }

    function completeVoiceSession(session, shouldSubmit) {
      if (session.completed) return;
      session.completed = true;
      clearSilenceTimer(session);
      if (activeVoiceSession === session) activeVoiceSession = null;
      resetVoiceInput();

      if (shouldSubmit && session.hasSpeech && assistantInput.value.trim()) {
        assistantForm.requestSubmit();
      } else if (!session.hasSpeech && !session.failed) {
        voiceStatus.textContent = voiceStatus.dataset.noSpeech;
      }
    }

    function stopVoiceSession(session, shouldSubmit) {
      if (session.completed) return;
      session.shouldSubmit = shouldSubmit;
      clearSilenceTimer(session);
      if (session.recognitionActive) {
        try {
          session.recognition.stop();
        } catch (error) {
          console.error("Could not stop browser speech recognition.", error);
          completeVoiceSession(session, shouldSubmit);
        }
      } else {
        completeVoiceSession(session, shouldSubmit);
      }
    }

    function cancelVoiceSession() {
      const session = activeVoiceSession;
      if (!session) return;
      session.completed = true;
      session.shouldSubmit = false;
      clearSilenceTimer(session);
      activeVoiceSession = null;
      resetVoiceInput();
      if (session.recognitionActive) {
        try {
          session.recognition.abort();
        } catch (error) {
          console.error("Could not cancel browser speech recognition.", error);
        }
      }
    }

    voiceInput.addEventListener("click", () => {
      if (activeVoiceSession) {
        stopVoiceSession(activeVoiceSession, true);
        return;
      }

      const recognition = new Recognition();
      const session = {
        recognition,
        recognitionActive: false,
        shouldSubmit: false,
        completed: false,
        failed: false,
        hasSpeech: false,
        silenceTimer: null,
        prefix: assistantInput.value.trim(),
      };
      activeVoiceSession = session;
      recognition.lang = speechLocale();
      recognition.continuous = true;
      recognition.interimResults = true;
      voiceInput.textContent = voiceInput.dataset.stopLabel;
      voiceInput.setAttribute("aria-pressed", "true");
      voiceStatus.textContent = `${voiceStatus.dataset.listening} ${voiceStatus.dataset.pauseHint}`;
      recognition.onresult = event => {
        const finalParts = [];
        const interimParts = [];
        for (let index = 0; index < event.results.length; index += 1) {
          const alternative = event.results[index][0];
          if (!alternative) continue;
          const part = alternative.transcript.trim();
          if (!part) continue;
          (event.results[index].isFinal ? finalParts : interimParts).push(part);
        }
        const transcript = [...finalParts, ...interimParts].join(" ");
        session.hasSpeech = Boolean(transcript);
        assistantInput.value = [session.prefix, transcript].filter(Boolean).join(" ");
        if (!session.hasSpeech) return;

        clearSilenceTimer(session);
        session.silenceTimer = window.setTimeout(() => {
          session.silenceTimer = null;
          stopVoiceSession(session, true);
        }, 3000);
      };
      recognition.onerror = event => {
        if (session.completed) return;
        session.failed = true;
        clearSilenceTimer(session);
        if (event.error === "not-allowed" || event.error === "service-not-allowed") {
          voiceStatus.textContent = voiceStatus.dataset.denied;
        } else if (event.error === "no-speech") {
          voiceStatus.textContent = voiceStatus.dataset.noSpeech;
        } else {
          voiceStatus.textContent = voiceStatus.dataset.service;
        }
        completeVoiceSession(session, false);
      };
      recognition.onend = () => {
        session.recognitionActive = false;
        if (session.completed) return;
        if (session.shouldSubmit) {
          completeVoiceSession(session, true);
        } else if (!session.silenceTimer) {
          completeVoiceSession(session, false);
        }
      };
      try {
        recognition.start();
        session.recognitionActive = true;
      } catch (error) {
        console.error("Could not start browser speech recognition.", error);
        session.failed = true;
        completeVoiceSession(session, false);
        voiceStatus.textContent = voiceStatus.dataset.service;
      }
    });

    assistantForm.addEventListener("submit", () => {
      cancelVoiceSession();
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

const sellerAnalyticsElement = document.getElementById("sellerAnalyticsData");
if (sellerAnalyticsElement && window.Chart) {
  try {
    const analytics = JSON.parse(sellerAnalyticsElement.textContent);
    const chart = document.getElementById("sellerProductChart");
    if (chart && analytics.labels && analytics.labels.length) {
      const datasets = [{
        label: chart.dataset.unitsLabel || "Items requested",
        data: analytics.units,
        backgroundColor: "#1d5b43",
        borderRadius: 6,
      }];
      if (analytics.views && analytics.views.length) {
        datasets.push({
          label: chart.dataset.viewsLabel || "Catalog views",
          data: analytics.views,
          backgroundColor: "#d96b32",
          borderRadius: 6,
        });
      }
      new window.Chart(chart, {
        type: "bar",
        data: {
          labels: analytics.labels,
          datasets,
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: datasets.length > 1, position: "top" },
          },
          scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
        },
      });
    }
  } catch (error) {
    console.error("Could not read seller dashboard analytics.", error);
  }
}

const adminAnalyticsElement = document.getElementById("adminAnalyticsData");
if (adminAnalyticsElement && window.Chart) {
  try {
    const analytics = JSON.parse(adminAnalyticsElement.textContent);
    const sellerChart = document.getElementById("sellerOverviewChart");
    if (sellerChart && analytics.makers) {
      new window.Chart(sellerChart, {
        type: "bar",
        data: {
          labels: analytics.makers.labels,
          datasets: [
            {
              label: sellerChart.dataset.requestLabel || "Demo order requests",
              data: analytics.makers.requests,
              backgroundColor: "#1d5b43",
              borderRadius: 6,
              yAxisID: "y",
            },
            {
              label: sellerChart.dataset.valueLabel || "Demo request value (₹)",
              data: analytics.makers.request_value,
              backgroundColor: "#d96b32",
              borderRadius: 6,
              yAxisID: "y1",
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: true, position: "top" } },
          scales: {
            y: {
              type: "linear",
              display: true,
              position: "left",
              beginAtZero: true,
              ticks: { precision: 0 },
            },
            y1: {
              type: "linear",
              display: true,
              position: "right",
              beginAtZero: true,
              grid: { drawOnChartArea: false },
              ticks: {
                callback: value => "₹" + Number(value).toLocaleString("en-IN"),
              },
            },
          },
        },
      });
    }

    const trendChart = document.getElementById("marketplaceTrendChart");
    if (trendChart && analytics.monthly) {
      new window.Chart(trendChart, {
        type: "line",
        data: {
          labels: analytics.monthly.labels,
          datasets: [
            {
              label: trendChart.dataset.requestLabel || "Demo order requests",
              data: analytics.monthly.requests,
              borderColor: "#1d5b43",
              backgroundColor: "#1d5b4322",
              fill: true,
              tension: 0.35,
              yAxisID: "y",
            },
            {
              label: trendChart.dataset.valueLabel || "Demo request value (₹)",
              data: analytics.monthly.request_value,
              borderColor: "#d96b32",
              backgroundColor: "#d96b3222",
              fill: false,
              tension: 0.35,
              yAxisID: "y1",
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: true, position: "top" } },
          scales: {
            y: {
              type: "linear",
              display: true,
              position: "left",
              beginAtZero: true,
              ticks: { precision: 0 },
            },
            y1: {
              type: "linear",
              display: true,
              position: "right",
              beginAtZero: true,
              grid: { drawOnChartArea: false },
              ticks: {
                callback: value => "₹" + Number(value).toLocaleString("en-IN"),
              },
            },
          },
        },
      });
    }

    const typeChart = document.getElementById("sellerTypeChart");
    if (typeChart && analytics.types) {
      new window.Chart(typeChart, {
        type: "doughnut",
        data: {
          labels: analytics.types.labels,
          datasets: [
            {
              data: analytics.types.counts,
              backgroundColor: ["#1d5b43", "#e07a3f"],
              borderWidth: 2,
              borderColor: "#fffaf3",
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: true, position: "bottom" },
          },
        },
      });
    }

    const districtChart = document.getElementById("sellerDistrictChart");
    if (districtChart && analytics.districts) {
      new window.Chart(districtChart, {
        type: "bar",
        data: {
          labels: analytics.districts.labels,
          datasets: [
            {
              label: districtChart.dataset.makersLabel || "Makers",
              data: analytics.districts.makers,
              backgroundColor: "#2d6a4f",
              borderRadius: 6,
            },
            {
              label: districtChart.dataset.requestsLabel || "Order requests",
              data: analytics.districts.requests,
              backgroundColor: "#e76f51",
              borderRadius: 6,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: true, position: "top" } },
          scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
        },
      });
    }
  } catch (error) {
    console.error("Could not read admin dashboard analytics.", error);
  }
}

if ((sellerAnalyticsElement || adminAnalyticsElement) && !window.Chart) {
  document.querySelectorAll("[data-chart-unavailable]").forEach(message => {
    message.hidden = false;
  });
  console.error("Chart.js is unavailable; dashboard analytics tables remain available.");
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
        const isShg = artisan.maker_type === "SHG";
        const marker = window.L.circleMarker([artisan.latitude, artisan.longitude], {
          radius: 9,
          color: isShg ? "#a54b25" : "#1d5b43",
          weight: 2,
          fillColor: isShg ? "#e9894d" : "#4b9b70",
          fillOpacity: 0.9,
        }).addTo(map);
        const popup = document.createElement("div");
        const name = document.createElement("strong");
        const type = document.createElement("p");
        const details = document.createElement("p");
        const summary = document.createElement("p");
        const profileLink = document.createElement("a");
        const distanceText = document.createElement("p");

        name.textContent = artisan.name;
        type.textContent = [
          artisan.maker_type || "Artisan",
          artisan.approximate_location ? "Approximate sample area" : "Public maker location",
        ].join(" · ");
        details.textContent = [artisan.craft, artisan.district].filter(Boolean).join(" · ");
        summary.textContent = artisan.summary || "";
        distanceText.className = "artisan-distance-popup";
        profileLink.href = `/artisans?q=${encodeURIComponent(artisan.name)}`;
        profileLink.textContent = "View maker profile";
        popup.append(name, type, details);
        if (summary.textContent) popup.appendChild(summary);
        popup.append(distanceText, profileLink);
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
