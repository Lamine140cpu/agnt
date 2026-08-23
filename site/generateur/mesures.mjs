/* Les mesures, prises dans la page SERVIE.
 *
 * Rien ici n'est déduit du code source : tout est relevé sur la page telle
 * qu'un navigateur la calcule. C'est la seule façon d'attraper les défauts de
 * ce projet, qui étaient tous invisibles à la lecture — une constante périmée,
 * un dégradé qui laisse passer le texte du dessous, une règle CSS morte
 * écrasée par une autre déclarée plus bas.
 *
 *   usage :  node mesures.mjs <url> <taille,taille,...>   -> JSON sur la sortie
 */
import pkg from '/opt/node22/lib/node_modules/playwright/index.js';
const { chromium } = pkg;

const [url, tailles] = process.argv.slice(2);
if (!url) { console.error('usage : node mesures.mjs <url> <LxH,LxH>'); process.exit(2); }
/* Une taille s'écrit « LxH » ou « LxH@densité ». La densité compte : à 1
 * l'agrandissement de toile ne se produit pas, et le contrôle qui coûte le
 * plus cher — ne jamais dessiner plus grand que le film — ne mordrait sur
 * rien. Les téléphones sont à 2 ou 3. */
const ECRANS = (tailles || '1440x900,390x844@3').split(',').map(t => {
  const [taille, d] = t.split('@');
  const [w, h] = taille.split('x').map(Number);
  return [w, h, d ? Number(d) : 1];
});

const nav = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const out = { ecrans: {}, erreurs: [] };

for (const [w, h, dpr] of ECRANS) {
  const p = await nav.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: dpr });
  p.on('pageerror', e => out.erreurs.push(`${w}x${h} ${e}`));

  // La série réellement demandée : on écoute le réseau, on ne devine pas.
  let servie = null;
  const absentes = [];
  p.on('request', r => {
    const m = /\/assets\/film\/([^/]+)\/f\d+\.\w+$/.exec(r.url());
    if (m && !servie) servie = m[1];
  });
  /* Les images RÉCLAMÉES ET ABSENTES. C'est la signature du compte faux : le
   * lecteur répartit le défilement sur un nombre d'images qu'il croit, et
   * demande celles qui n'ont jamais été encodées. Le film se fige, et rien
   * dans la page ne le dit. */
  p.on('response', r => {
    if (r.status() >= 400 && !/favicon/.test(r.url())) {
      absentes.push(`${r.status()} ${r.url().split('/').slice(-2).join('/')}`);
    }
  });

  await p.goto(url, { waitUntil: 'load' });
  await p.waitForTimeout(3000);
  // Parcourir TOUT le prologue : un compte faux ne se voit qu'au-delà du
  // point où les images cessent d'exister — ici au milieu de la descente.
  for (const f of [0.15, 0.35, 0.55, 0.75, 0.95]) {
    await p.evaluate(v => scrollTo({ top: document.documentElement.scrollHeight * v,
                                     behavior: 'instant' }), f);
    await p.waitForTimeout(900);
  }
  await p.evaluate(() => scrollTo({ top: 0, behavior: 'instant' }));
  /* ATTENDRE L'IMAGE, ne pas la supposer redessinée. Après un parcours
   * jusqu'au bas de la page, le retour en haut ne remet pas une image sur la
   * toile dans la trame suivante : le décodeur a du retard. Mesurer trop tôt
   * relevait « image 0x0 » et faisait crier le contrôleur sur une page
   * parfaitement saine. Un contrôle qui alerte à tort ne sera plus lu. */
  await p.waitForFunction(() => window.__IMAGE && window.__IMAGE.width > 0,
                          null, { timeout: 15000 })
         .catch(() => out.erreurs.push(`${w}x${h} aucune image dessinée après 15 s`));
  await p.waitForTimeout(400);

  const base = await p.evaluate(() => {
    const d = document.documentElement;
    const toile = document.getElementById('toile');
    const pr = document.getElementById('prologue');
    const tete = document.querySelector('header');
    const im = window.__IMAGE;
    const b = toile ? toile.getBoundingClientRect() : null;

    // Le fond effectif d'un élément : on remonte jusqu'au premier ancêtre
    // peint. Une couleur transparente ne dit rien du contraste réel.
    const fond = (el) => {
      for (let n = el; n; n = n.parentElement) {
        const c = getComputedStyle(n).backgroundColor;
        if (c && !/rgba\(0, 0, 0, 0\)|transparent/.test(c)) return c;
      }
      return getComputedStyle(document.body).backgroundColor;
    };
    const rgb = (s) => (s.match(/[\d.]+/g) || [0, 0, 0]).slice(0, 3).map(Number);
    const lum = (c) => {
      const v = rgb(c).map(x => x / 255)
        .map(x => x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4));
      return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2];
    };
    const contraste = (sel) => {
      const el = document.querySelector(sel);
      if (!el) return null;
      const a = lum(getComputedStyle(el).color), z = lum(fond(el));
      return +(((Math.max(a, z) + .05) / (Math.min(a, z) + .05)).toFixed(2));
    };

    return {
      course: pr ? Math.max(pr.offsetHeight - innerHeight, 1) : null,
      toile_css: b ? `${Math.round(b.width)}x${Math.round(b.height)}` : null,
      toile_px: toile ? `${toile.width}x${toile.height}` : null,
      // `window.__IMAGE` ne sert PAS à mesurer la définition du film : c'est
      // un ImageBitmap, et le lecteur le ferme quand il quitte la fenêtre de
      // préchargement. Un bitmap fermé rapporte 0x0 — de quoi faire crier le
      // contrôleur sur une page saine. La définition se relève sur une image
      // réellement téléchargée, plus bas.
      image: null,
      rapport_toile: b && b.height ? +(b.width / b.height).toFixed(3) : null,
      rapport_image: im ? +(im.width / im.height).toFixed(3) : null,
      // La part de la largeur du film que le visiteur voit vraiment.
      part_visible: (b && im)
        ? +Math.min(1, (b.width / b.height) / (im.width / im.height)).toFixed(3) : null,
      deborde: d.scrollWidth > d.clientWidth,
      tete_hauteur: tete ? Math.round(tete.getBoundingClientRect().height) : null,
      menu_tronques: [...document.querySelectorAll('nav a')]
        .filter(a => a.scrollWidth > a.clientWidth + 1).map(a => a.textContent.trim()),
      liens_bleus: [...document.querySelectorAll('a')]
        .filter(a => /rgb\(0, 0, (238|255)\)/.test(getComputedStyle(a).color)).length,
      contrastes: {
        corps: contraste('#suite .corps'),
        second_plan: contraste('#suite .eti'),
        pied: contraste('.pied-txt'),
      },
    };
  });

  // Les ancres : aucune section ne doit se ranger sous la barre fixe.
  const ancres = {};
  for (const id of await p.evaluate(() =>
    [...document.querySelectorAll('#suite [id]')].map(e => e.id))) {
    await p.evaluate(i => document.getElementById(i).scrollIntoView(), id);
    await p.waitForTimeout(220);
    ancres[id] = await p.evaluate(i =>
      Math.round(document.getElementById(i).getBoundingClientRect().top), id);
  }

  // La définition du film, mesurée sur une image du dossier réellement servi.
  if (servie) {
    const d = await p.evaluate(async (s) => {
      const r = await fetch(`assets/film/${s}/f0001.jpg`);
      const b = await createImageBitmap(await r.blob());
      const t = `${b.width}x${b.height}`;
      b.close();
      return t;
    }, servie).catch(() => null);
    base.image = d;
    if (d) {
      const [il, ih] = d.split('x').map(Number);
      const bb = base.toile_css ? base.toile_css.split('x').map(Number) : null;
      base.rapport_image = +(il / ih).toFixed(3);
      base.part_visible = bb
        ? +Math.min(1, (bb[0] / bb[1]) / (il / ih)).toFixed(3) : null;
    }
  }
  base.serie_servie = servie;
  base.absentes = absentes.slice(0, 8);
  base.absentes_total = absentes.length;
  base.ancres = ancres;
  base.sous_la_barre = Object.entries(ancres)
    .filter(([, y]) => y < base.tete_hauteur).map(([id]) => id);
  out.ecrans[dpr === 1 ? `${w}x${h}` : `${w}x${h}@${dpr}`] = base;
  await p.close();
}

/* Le débit d'images : MÉDIANE DE TROIS PASSAGES.
   Une lecture isolée varie de 45 à 60 sur la même page sans rien changer.
   Deux fausses alertes ont été levées dans ce projet sur une lecture unique. */
{
  const p = await nav.newPage({ viewport: { width: ECRANS[0][0], height: ECRANS[0][1] },
                               deviceScaleFactor: ECRANS[0][2] });
  await p.goto(url, { waitUntil: 'load' });
  await p.waitForTimeout(3000);
  const un = () => p.evaluate(() => new Promise(res => {
    scrollTo({ top: 0, behavior: 'instant' });
    let n = 0; const t0 = performance.now();
    const tour = () => {
      n++; scrollBy(0, 17);
      if (performance.now() - t0 < 2500) requestAnimationFrame(tour);
      else res(Math.round(n / ((performance.now() - t0) / 1000)));
    };
    requestAnimationFrame(tour);
  }));
  const trois = [await un(), await un(), await un()].sort((a, b) => a - b);
  out.images_par_seconde = { passages: trois, mediane: trois[1] };
  await p.close();
}

await nav.close();
console.log(JSON.stringify(out, null, 2));
