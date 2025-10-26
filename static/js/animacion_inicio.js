  // Revisar si ya se mostró el splash antes
  const splashShown = sessionStorage.getItem("splashShown");

  window.addEventListener("load", () => {
    if (!splashShown) {
      // Mostrar splash solo la primera vez
      setTimeout(() => {
        const splash = document.getElementById("splash-screen");
        splash.classList.add("fade-out");
        setTimeout(() => {
          splash.style.display = "none";
          document.getElementById("main-content").style.display = "block";
          // Guardar que ya se mostró
          sessionStorage.setItem("splashShown", "true");
        }, 1000);
      }, 2000); // 5 segundos
    } else {
      // Si ya se mostró antes, saltarlo
      document.getElementById("splash-screen").style.display = "none";
      document.getElementById("main-content").style.display = "block";
    }
  });