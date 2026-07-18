/* ============ ON THE RECORD — behaviour ============ */
(function () {
  /* cursor */
  if (!matchMedia("(hover:none)").matches) {
    var cur = document.createElement("div");
    cur.className = "cursor";
    cur.innerHTML = '<div class="ring"></div><div class="dot"></div>';
    document.body.appendChild(cur);
    var cx = 0, cy = 0, tx = 0, ty = 0;
    addEventListener("pointermove", function (e) { tx = e.clientX; ty = e.clientY; });
    (function loop() {
      cx += (tx - cx) * .16; cy += (ty - cy) * .16;
      cur.style.transform = "translate(" + cx + "px," + cy + "px)";
      requestAnimationFrame(loop);
    })();
    document.querySelectorAll("a,button,.parea,.wcard,.cite").forEach(function (el) {
      el.addEventListener("mouseenter", function () { cur.classList.add("big"); });
      el.addEventListener("mouseleave", function () { cur.classList.remove("big"); });
    });
  }

  /* theme toggle */
  var thm = document.querySelector(".thm");
  function icon() {
    var n = document.documentElement.classList.contains("night");
    thm.innerHTML = n
      ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v2.4M12 19.6V22M2 12h2.4M19.6 12H22M4.9 4.9l1.7 1.7M17.4 17.4l1.7 1.7M19.1 4.9l-1.7 1.7M6.6 17.4l-1.7 1.7"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>';
  }
  if (thm) {
    icon();
    thm.addEventListener("click", function () {
      var n = document.documentElement.classList.toggle("night");
      try { localStorage.setItem("otr-theme", n ? "night" : "day"); } catch (e) {}
      icon();
    });
  }

  /* mobile nav */
  var burger = document.querySelector(".burger");
  if (burger) burger.addEventListener("click", function () { document.body.classList.toggle("navopen"); });
  document.querySelectorAll(".mnav a").forEach(function (a) {
    a.addEventListener("click", function () { document.body.classList.remove("navopen"); });
  });

  /* hero intro */
  if (window.gsap && document.querySelector(".hero h1 .row span")) {
    var tl = gsap.timeline({ defaults: { ease: "expo.out" } });
    tl.to(".hero h1 .row span", { y: 0, duration: 1.15, stagger: .1, delay: .15 })
      .from(".hero .filed,.hero .sub,.hero .now,.hstats,.hero .stamp",
        { opacity: 0, y: 18, duration: .8, stagger: .08 }, "-=.7");
  }

  /* rotating status word */
  var rot = document.querySelector(".rot");
  if (rot) {
    var words = ["monitoring.", "investigating.", "documenting.", "drafting.", "pleading.", "teaching."];
    var i = 0;
    setInterval(function () {
      i = (i + 1) % words.length;
      if (window.gsap) {
        gsap.to(rot, { opacity: 0, y: -6, duration: .25, onComplete: function () {
          rot.textContent = words[i];
          gsap.fromTo(rot, { opacity: 0, y: 6 }, { opacity: 1, y: 0, duration: .3 });
        }});
      } else rot.textContent = words[i];
    }, 2200);
  }

  /* active nav link */
  var here = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll("nav.main a,.mnav a").forEach(function (a) {
    var h = a.getAttribute("href");
    if (h === here || (h && h.indexOf("#") < 0 && h.split("/").pop() === here)) a.classList.add("here");
  });

  /* reading progress bar (on pages that have one) */
  var pb = document.getElementById("progBar");
  if (pb) addEventListener("scroll", function () {
    var h = document.documentElement;
    var p = h.scrollTop / (h.scrollHeight - h.clientHeight || 1);
    pb.style.transform = "scaleX(" + p + ")";
  }, { passive: true });

  /* header scrolled state */
  var hd = document.querySelector("header");
  function onScr() { hd && hd.classList.toggle("scrolled", scrollY > 24); }
  addEventListener("scroll", onScr, { passive: true }); onScr();

  /* section rail scrollspy (index) */
  var rail = document.getElementById("rail");
  if (rail && "IntersectionObserver" in window) {
    var links = rail.querySelectorAll("a");
    var spy = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) {
          links.forEach(function (l) {
            l.classList.toggle("on", l.getAttribute("href") === "#" + e.target.id);
          });
        }
      });
    }, { rootMargin: "-40% 0px -55% 0px" });
    document.querySelectorAll("section[id]").forEach(function (s) { spy.observe(s); });
  }

  /* footer signature underline draws when visible */
  var sig = document.querySelector(".sig .name");
  if (sig && "IntersectionObserver" in window) {
    new IntersectionObserver(function (es, o) {
      es.forEach(function (e) { if (e.isIntersecting) { sig.classList.add("drawn"); o.disconnect(); } });
    }, { threshold: .6 }).observe(sig);
  }

  /* reveals */
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) {
          if (window.gsap) gsap.to(e.target, { opacity: 1, y: 0, duration: .95, ease: "expo.out" });
          else { e.target.style.opacity = 1; e.target.style.transform = "none"; }
          io.unobserve(e.target);
        }
      });
    }, { threshold: .12 });
    document.querySelectorAll("[data-rise]").forEach(function (el) { io.observe(el); });
  }
})();
