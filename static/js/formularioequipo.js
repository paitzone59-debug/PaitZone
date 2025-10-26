
    const checkboxes = document.querySelectorAll('.carrera-checkbox');
    const maxCarreras = 6;

    checkboxes.forEach(cb => {
        cb.addEventListener('change', () => {
            const checked = document.querySelectorAll('.carrera-checkbox:checked');
            if (checked.length > maxCarreras) {
                cb.checked = false; // desmarca el último
                alert(`Solo puedes seleccionar máximo ${maxCarreras} carreras.`);
            }
        });
    });





    //ventana flotante



    // Cerrar automáticamente los flashes después de 5 segundos
  document.addEventListener("DOMContentLoaded", () => {
    const alerts = document.querySelectorAll(".auto-dismiss");
    alerts.forEach(alert => {
      setTimeout(() => {
        let bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
      }, 2000); // 3 segundos
    });
  });



// nav-bar comienzo 
document.addEventListener("DOMContentLoaded", () => {
  const navbar = document.getElementById("mainNavbar");
  const logo = document.getElementById("logoBrand");

  // Si está logueado, no animamos nada
  if (navbar.classList.contains("logged-in")) {
    logo.classList.add("logo-small");
    return;
  }

  // Animación solo cuando NO hay usuario
  window.addEventListener("scroll", () => {
    if (window.scrollY > 50) {
      navbar.classList.add("shrink");
      logo.classList.add("logo-small");
    } else {
      navbar.classList.remove("shrink");
      logo.classList.remove("logo-small");
    }
  });
});

