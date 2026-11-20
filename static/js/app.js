const menuToggle = document.getElementById("menuToggle");
const navLinks = document.getElementById("navLinks");
if (menuToggle && navLinks) menuToggle.addEventListener("click", () => navLinks.classList.toggle("open"));

document.querySelectorAll(".flash").forEach(el => {
  setTimeout(() => { el.style.opacity = "0"; el.style.transform = "translateY(-8px)"; }, 4200);
  setTimeout(() => el.remove(), 4800);
});
