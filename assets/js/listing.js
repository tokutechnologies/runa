/* renders content/posts.json into listing pages */
(function () {
  var cfg = window.OTR_LIST || { kind: "blog" };
  var grid = document.getElementById("grid"), feat = document.getElementById("feat"),
      chips = document.getElementById("chips"), note = document.getElementById("lnote");
  function fmt(d) { try { return new Date(d + "T00:00:00").toLocaleDateString("en-GB", { month: "short", year: "numeric" }); } catch (e) { return d; } }

  fetch("content/posts.json", { cache: "no-store" })
    .then(function (r) { if (!r.ok) throw 0; return r.json(); })
    .then(function (all) {
      var posts = all.filter(function (p) { return String(p.kind||"").trim().toLowerCase() === cfg.kind; });
      if (!posts.length) { note.hidden = false; return; }

      /* filter chips from the type field */
      var types = []; posts.forEach(function (p) { if (p.type && types.indexOf(p.type) < 0) types.push(p.type); });
      chips.innerHTML = '<button class="chip on" data-f="all">All</button>' +
        types.map(function (t) { return '<button class="chip" data-f="' + t + '">' + t + 's</button>'; }).join("");

      function card(p) {
        var poem = (p.type || "").toLowerCase() === "poem";
        return '<a class="wcard' + (poem ? " poemcard" : "") + '" data-t="' + (p.type || "") + '" href="read.html?slug=' + p.slug + '">' +
          '<span class="k">' + (p.type || p.kind) + "</span>" +
          "<h3>" + (p.title || p.slug) + "</h3>" +
          "<p>" + (poem ? "<em>" + (p.excerpt || "") + "</em>" : (p.excerpt || "")) + "</p>" +
          '<span class="m"><span>' + fmt(p.date) + "</span><span>" + (p.minutes || "—") + " min</span></span></a>";
      }

      /* featured = newest */
      if (cfg.featured && posts.length) {
        var f = posts[0];
        feat.innerHTML = '<a class="bfeat" href="read.html?slug=' + f.slug + '" data-t="' + (f.type || "") + '">' +
          '<div class="tx"><span class="k">' + (f.type || f.kind) + " &#183; latest</span>" +
          "<h2>" + (f.title || f.slug) + "</h2><p>" + (f.excerpt || "") + "</p>" +
          '<span class="m">' + fmt(f.date) + " &#183; " + (f.minutes || "—") + ' min read</span></div>' +
          '<div class="side"><span class="st">' + (cfg.kind === "fiction" ? "Fresh ink" : "Exhibit A") + "</span></div></a>";
      }
      grid.innerHTML = posts.slice(cfg.featured ? 1 : 0).map(card).join("");

      chips.addEventListener("click", function (e) {
        var c = e.target.closest(".chip"); if (!c) return;
        chips.querySelectorAll(".chip").forEach(function (x) { x.classList.remove("on"); });
        c.classList.add("on");
        var f = c.getAttribute("data-f");
        document.querySelectorAll("[data-t]").forEach(function (el) {
          el.style.display = (f === "all" || el.getAttribute("data-t") === f) ? "" : "none";
        });
      });

      if (window.gsap) gsap.from(".bfeat,.wcard", { opacity: 0, y: 26, duration: .8, stagger: .06, ease: "expo.out" });
    })
    .catch(function () { note.hidden = false; });
})();
