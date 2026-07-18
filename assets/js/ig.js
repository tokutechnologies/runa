/* Renders Instagram dispatches from Behold (live) or content/instagram.json (static). */
(function () {
  var cfg = window.OTR_IG || {};
  var grid = document.querySelector(".iggrid");
  if (!grid) return;
  function render(posts) {
    if (!posts || !posts.length) return;
    grid.innerHTML = posts.slice(0, 6).map(function (p) {
      var cap = (p.caption || "").replace(/</g, "&lt;");
      return '<a class="igtile igimg" href="' + (p.permalink || "https://instagram.com/" + (cfg.handle || "")) +
        '" target="_blank" rel="noopener">' +
        (p.image ? '<img loading="lazy" src="' + p.image + '" alt="Instagram post"/>' : "") +
        '<span class="igcap"><span class="q">' + cap + '</span>' +
        '<span class="im">@' + (cfg.handle || "instagram") + (p.date ? " &#183; " + p.date : "") + "</span></span></a>";
    }).join("");
    if (window.gsap) gsap.from(".igtile", { opacity: 0, y: 20, duration: .7, stagger: .07, ease: "expo.out" });
  }
  function fromBehold(url) {
    fetch(url).then(function (r) { return r.json(); }).then(function (d) {
      var posts = (d.posts || d).map(function (p) {
        return { image: p.mediaUrl || p.thumbnailUrl, caption: p.caption,
                 permalink: p.permalink, date: (p.timestamp || "").slice(0, 10) };
      });
      render(posts);
    }).catch(function () { fromJSON(); });
  }
  function fromJSON() {
    fetch("content/instagram.json", { cache: "no-store" })
      .then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(render).catch(function () {/* keep placeholders */});
  }
  cfg.behold ? fromBehold(cfg.behold) : fromJSON();
})();
