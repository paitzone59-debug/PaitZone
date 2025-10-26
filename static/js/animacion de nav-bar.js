  window.addEventListener('scroll', function () {
    const navbar = document.getElementById('mainNavbar');
    if (window.scrollY > 50) {
      navbar.classList.add('navbar-shrink');
    } else {
      navbar.classList.remove('navbar-shrink');
    }
  });

  // Animación suave del subrayado activo (link actual)
  document.addEventListener("DOMContentLoaded", () => {
    const navLinks = document.querySelectorAll(".nav-link");
    const currentURL = window.location.pathname;

    navLinks.forEach(link => {
      if (link.getAttribute("href") === currentURL) {
        link.style.color = "#ca8205";
        link.style.fontWeight = "600";
        link.style.position = "relative";
      }
    });
  });