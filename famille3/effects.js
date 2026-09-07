/* 住まいのしおり 画面の動き
   POLのHP（main.js）と同じ考え方・同じ数値で揃えている。
   ・アコーディオン＝grid-template-rows 0fr→1fr（POLのFAQと同方式）
   ・スクロールで現れる＝IntersectionObserver + 段差 0.18s
   JavaScriptが動かない環境でも、内容はすべて読める（<details> がそのまま働く）。 */
(function () {
  'use strict';

  var reduce = window.matchMedia &&
               window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* JavaScriptが動いている印。これが無い環境では、閉じた見た目を作らず
     <details> の素の動作（中身がそのまま出る）に任せる。 */
  document.documentElement.classList.add('js');

  /* ---------- 1. アコーディオン（閉じた状態から下に伸びる） ---------- */
  document.querySelectorAll('details.sec').forEach(function (d) {
    var summary = d.querySelector('summary');
    var wrap = d.querySelector('.sec-wrap');
    if (!summary || !wrap) return;

    summary.addEventListener('click', function (e) {
      if (reduce) return;               // 動きを減らす設定なら既定の動作に任せる
      e.preventDefault();

      if (d.open) {
        // 閉じる：先に縮めてから open を外す
        d.classList.remove('is-expanded');
        var done = function () {
          wrap.removeEventListener('transitionend', done);
          d.open = false;
        };
        wrap.addEventListener('transitionend', done);
        setTimeout(done, 420);          // transitionend が来なかったときの保険
      } else {
        // 開く：先に open にして中身を出し、レイアウトを1回確定させてから伸ばす。
        // requestAnimationFrame に頼ると、描画が止まっている状況で開かないことがある
        // （POLのmain.js と同じ「リフローを挟む」書き方に揃えた）。
        d.open = true;
        void wrap.offsetHeight;   /* リフローを強制 */
        d.classList.add('is-expanded');
      }
    });

    if (d.open) d.classList.add('is-expanded');
  });

  /* ---------- 2. ナビゲーション（狭い画面は3本線の引き出し） ----------
     素のCSSではナビは帯として全部見えている。JSが動いている狭い画面でだけ
     引き出しに変える（`.js` クラスで切り替え）。JSが止まれば帯のまま読める。 */
  (function () {
    var btn = document.getElementById('navtoggle');
    var nav = document.getElementById('nav');
    var back = document.getElementById('navbackdrop');
    if (!btn || !nav || !back) return;

    var narrow = window.matchMedia('(max-width: 767px)');

    var setOpen = function (open) {
      nav.classList.toggle('is-open', open);
      btn.classList.toggle('is-open', open);
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      btn.setAttribute('aria-label', open ? 'メニューを閉じる' : 'メニューを開く');
      document.body.classList.toggle('nav-locked', open);
      if (open) { back.hidden = false; void back.offsetHeight; back.classList.add('is-open'); }
      else {
        back.classList.remove('is-open');
        setTimeout(function () { if (!nav.classList.contains('is-open')) back.hidden = true; }, 300);
      }
    };

    btn.addEventListener('click', function () {
      setOpen(!nav.classList.contains('is-open'));
    });
    back.addEventListener('click', function () { setOpen(false); });
    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') setOpen(false);     // 行き先を選んだら閉じる
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('is-open')) { setOpen(false); btn.focus(); }
    });

    // 画面が広がったら、開きっぱなしの状態を必ず解除する
    var sync = function () { if (!narrow.matches) setOpen(false); };
    if (narrow.addEventListener) narrow.addEventListener('change', sync);
    else if (narrow.addListener) narrow.addListener(sync);
  })();

  /* ---------- 3. スクロールで現れる ----------
     🔴 設計の要点：JavaScriptは「動きを足す」だけで、「隠す」ことは絶対にしない。
     素のCSSでは全部見えている状態にしておき、reveal クラスが付いた時だけ
     CSSアニメーション（animation-fill-mode: backwards）で出現を演出する。
     JSが止まっても・observerが動かなくても・アニメーションが無効でも、
     中身は必ず読める（入居者向けページなので演出より確実性を優先）。 */
  if (!reduce) {
    var inView = function (el) {
      var r = el.getBoundingClientRect();
      return r.top < (window.innerHeight || 0) && r.bottom > 0;
    };
    var play = function (el, delay) {
      el.style.animationDelay = delay + 's';
      el.classList.add('reveal');
    };

    var els = document.querySelectorAll('[data-scroll]');
    var groups = new Map();
    els.forEach(function (el) {
      var g = el.parentElement;
      if (!groups.has(g)) groups.set(g, []);
      groups.get(g).push(el);
    });

    var io = ('IntersectionObserver' in window) ? new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        play(en.target, parseFloat(en.target.dataset.delay) || 0);
        io.unobserve(en.target);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }) : null;

    groups.forEach(function (list) {
      list.forEach(function (el, i) {
        var delay = Math.min(i * 0.18, 0.72);   // 段差（POLと同じ 0.18s）。待たせ過ぎないよう上限を置く
        el.dataset.delay = delay;
        if (inView(el) || !io) {
          play(el, delay);       // 最初から見えている位置のものは、その場で演出して終わり
        } else {
          io.observe(el);
        }
      });
    });
  }

  /* ---------- 4. スクロールするとヘッダーに影 ---------- */
  (function () {
    var head = document.querySelector('.site-header');
    if (!head) return;
    var on = false;
    var tick = function () {
      var should = window.scrollY > 40;
      if (should !== on) { head.classList.toggle('is-scrolled', should); on = should; }
    };
    tick();
    window.addEventListener('scroll', tick, { passive: true });
  })();

  /* ---------- 5. ページ内リンクはヘッダーの高さぶん手前で止める ---------- */
  document.querySelectorAll('a[href^="#"]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      var id = a.getAttribute('href');
      if (id === '#' || id.length < 2) return;
      var target = document.querySelector(id);
      if (!target) return;
      e.preventDefault();
      var top = target.getBoundingClientRect().top + window.scrollY - 16;
      window.scrollTo({ top: top, behavior: reduce ? 'auto' : 'smooth' });
      history.replaceState(null, '', id);
    });
  });
})();
