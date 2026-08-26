/* ============================================================================
   Calcule une séquence d'images à partir de la page temps réel.

   C'est le pipeline d'Apple, et celui de velaarmon.com : au lieu de faire
   calculer la scène par le navigateur du visiteur soixante fois par seconde,
   on la calcule une fois, ici, et on lui livre des images.

   Le point qui rend l'opération rapide : la page n'est chargée qu'UNE fois.
   La cuisson de lumière — six secondes d'arbre d'englobants et de lancer de
   rayons — n'a lieu qu'au démarrage. Ensuite on ne fait que déplacer la barre
   de défilement et prendre une photo. Recharger à chaque image aurait
   multiplié ces six secondes par le nombre d'images.

   Le fragment #instant coupe l'interpolation de la caméra : sans lui, chaque
   capture serait prise en pleine transition et la séquence tremblerait.

     usage : node film_rendu.mjs [images] [largeur] [hauteur] [dossier] [page]
   ============================================================================ */
import pkg from '/opt/node22/lib/node_modules/playwright/index.js';
const { chromium } = pkg;
import { mkdirSync, writeFileSync } from 'node:fs';

const IMAGES  = Number(process.argv[2] || 240);
const LARGEUR = Number(process.argv[3] || 1280);
const HAUTEUR = Number(process.argv[4] || 720);
const DOSSIER = process.argv[5] || 'assets/film/large';
const PAGE    = process.argv[6] || 'voiture.html';
const SOURCE  = `http://localhost:8731/${PAGE}#film-instant`;

mkdirSync(DOSSIER, { recursive: true });

const nav = await chromium.launch();
const page = await nav.newPage({ viewport: { width: LARGEUR, height: HAUTEUR }, deviceScaleFactor: 1 });

const erreurs = [];
page.on('pageerror', (e) => erreurs.push(e.message));

const t0 = Date.now();
await page.goto(SOURCE, { waitUntil: 'load', timeout: 180000 });
/* Toutes les pages n'ont pas d'écran de chargement — vitrine.html n'en a
   aucun. Attendre « .charge.parti » sur celles-là n'échouait pas franchement :
   ça expirait au bout de cinq minutes, ce qui ressemblait à une page bloquée
   alors qu'elle était prête depuis dix secondes. On n'attend donc le voile que
   s'il existe. */
if (await page.$('.charge')) await page.waitForSelector('.charge.parti', { timeout: 300000 });
await page.waitForTimeout(4000);
console.log(`page prête et lumière cuite en ${((Date.now() - t0) / 1000).toFixed(1)} s`);

/* On MASQUE les textes, on ne les supprime pas. La nuance a coûté une série
   entière : le gestionnaire de défilement écrit dans la barre de progression,
   et la retirer du document le faisait lever une exception AVANT d'avoir mis
   à jour la caméra. Les vingt-quatre images étaient rigoureusement
   identiques. Masquer laisse le code intact.

   Ils seront de toute façon réécrits en HTML par-dessus la séquence, où ils
   restent sélectionnables et lisibles par un lecteur d'écran — ce qu'une
   image ne sera jamais. */
await page.addStyleTag({ content: '.mot,.bar,.rail,.charge{visibility:hidden!important}' });

const course = await page.evaluate(() => document.body.scrollHeight - innerHeight);
const t1 = Date.now();

for (let i = 0; i < IMAGES; i++) {
  const t = i / (IMAGES - 1);
  await page.evaluate((y) => scrollTo(0, y), course * t);
  /* Pas d'attente ici : la demande d'image ci-dessous attend déjà que la
     boucle ait rendu. Attendre deux fois coûtait quatre secondes par image. */
  /* On demande l'image à la boucle de rendu, puis on attend qu'elle la
     dépose. Une capture d'écran de Playwright coûtait ici douze à seize
     secondes — elle force une recomposition complète de la page — contre une
     seconde et demie par cette voie. */
  const donnees = await page.evaluate(async () => {
    window.__image = null; window.__demande = true;
    const t = Date.now();
    while (!window.__image && Date.now() - t < 30000)
      await new Promise((r) => requestAnimationFrame(r));
    return window.__image;
  });
  const nom = `${DOSSIER}/f${String(i + 1).padStart(4, '0')}.jpg`;
  writeFileSync(nom, Buffer.from(donnees.split(',')[1], 'base64'));
  if ((i + 1) % 40 === 0 || i === IMAGES - 1) {
    const par = (Date.now() - t1) / (i + 1);
    console.log(`  ${i + 1}/${IMAGES}  ${par.toFixed(0)} ms/image  ` +
                `reste ${((IMAGES - i - 1) * par / 1000).toFixed(0)} s`);
  }
}

console.log(erreurs.length ? `ERREURS : ${erreurs.slice(0, 3).join(' | ')}` : 'erreurs : aucune');
console.log(`${IMAGES} images en ${((Date.now() - t1) / 1000).toFixed(0)} s → ${DOSSIER}`);
await nav.close();
