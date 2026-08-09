# HOLA ENERGY — landing page

Page vitrine statique pour une boisson énergisante, dans l'esprit des sites DTC
type [ciaoenergy.com](https://www.ciaoenergy.com) : gamme de saveurs, bénéfices
produit, composition, FAQ, newsletter.

**La marque et le produit sont fictifs** — c'est une démo de design, pas le site
d'une entreprise existante. Le pied de page le mentionne explicitement.

## Aperçu

```bash
cd site && python3 -m http.server 8000
# http://localhost:8000
```

Il faut bien un serveur : la canette 3D est un module ES, que le navigateur
refuse de charger depuis `file://`. Sans lui, la page reste parfaitement
fonctionnelle et affiche les canettes SVG à la place.

## Contenu

```
site/
  index.html            la page, un seul fichier
  vendor/               three.js r185 (module + core)
  assets/labels/        étiquettes sources, pleine résolution
  assets/web/           mêmes étiquettes en 1280 px + carte d'environnement
```

Aucune requête vers un CDN : les polices **Anton** (titres) et **Archivo**
(texte) sont embarquées en base64, et three.js est vendorisé.

## Sections

| Ancre | Contenu |
| --- | --- |
| `#top` | Héro, bandeau défilant, canette |
| `#gamme` | 6 saveurs — cliquer sur une carte repeint toute la page |
| `#benefices` | 4 différences + comparatif des sucres en barres |
| `#composition` | Tableau nutritionnel et liste d'ingrédients |
| `#faq` | 9 questions en accordéon (`<details>`) |
| `#newsletter` | Inscription e-mail avec validation côté client |

## Détails d'implémentation

- **Thèmes** : palette complète en tokens sur `:root`, redéfinie sous
  `@media (prefers-color-scheme: dark)` et sous `:root[data-theme="dark"]`.
  Aucune couleur n'est déclarée uniquement dans un bloc de thème.
- **Saveur active** : le clic sur une carte écrit `--accent` / `--on-accent` sur
  `documentElement` ; héro, boutons, FAQ, tableau et newsletter suivent.
- **Canettes SVG** : un `<symbol>` unique réutilisé via `<use>`. Les styles sont
  écrits en inline dans le symbole — les sélecteurs de classe du document ne
  traversent pas le shadow tree créé par `<use>`, seules les variables CSS
  héritent.
- **Riso** : grain en `feTurbulence` sur `body::after`, plus un calque de
  canette décalé en `mix-blend-mode` (`multiply` en clair, `screen` en sombre)
  qui imite une erreur de repérage d'impression.
- **Accessibilité** : navigation au clavier avec `:focus-visible`, cartes de
  saveur en `<button aria-pressed>`, messages de formulaire en `aria-live`,
  animations désactivées sous `prefers-reduced-motion`.

## La canette 3D

Le héro affiche une canette en WebGL. Aucun modèle `.glb` n'est téléchargé :

- **Géométrie** générée en `LatheGeometry` à partir d'un profil de 12 points,
  plus un manchon `CylinderGeometry` pour l'étiquette et un tore pour la
  languette.
- **Étiquettes** composées à la volée dans un `<canvas>` : l'artwork généré,
  puis la typographie dessinée par-dessus, répétée à un demi-tour d'écart pour
  rester lisible de face comme de dos. La typo n'est donc jamais dans l'image
  source — changer un nom de saveur ne demande pas de regénérer une texture.
- **Reflets** : `assets/web/env-studio.jpg` passée en `PMREMGenerator`, plus
  deux directionnelles. `MeshPhysicalMaterial` métal pour le corps, avec
  vernis pour l'étiquette.
- **Position** : la canette est ancrée sur le `getBoundingClientRect()` du bloc
  `.hero-can` et mise à l'échelle pour occuper la même hauteur que le SVG
  qu'elle remplace. Elle suit donc la mise en page à tous les points de rupture,
  sans valeur codée en dur par breakpoint.

Le scroll ne pilote pas la canette directement : il déplace des valeurs
**cibles**, que la boucle de rendu rattrape par interpolation à taux constant
(`1 - exp(-k·dt)`, indépendant du framerate). C'est ce retard qui donne
l'inertie, et il permet d'additionner le parallaxe souris sans conflit. Même
principe que le site qui a servi de référence.

Le rendu est suspendu dès que le héro sort du champ, et la page retombe sur les
canettes SVG si le contexte WebGL n'est pas disponible.

### Points d'attention

- `#webgl` doit garder ses `width`/`height` explicites. Un `<canvas>` est un
  élément remplacé : avec `inset:0` seul, il prend la taille de son buffer de
  dessin, soit le double de la fenêtre sur un écran en DPR 2.
- Les raccords gauche/droite des étiquettes ne sont pas parfaitement continus.
  La couture est placée à l'arrière de la canette, hors du champ de la caméra.

## Version d'un seul fichier

```bash
cd site && python3 build_artifact.py   # -> site/dist/index.html
```

Produit une page unique, sans aucun fichier voisin ni requête réseau : three.js
et les textures y sont repliés. C'est la version à déposer sur un hébergeur
statique ou dans un contexte qui interdit les ressources externes.

Le repli de three.js n'est pas un simple `import` depuis une URL `data:` — une
CSP stricte refuse ce schéma pour les scripts. Les deux fichiers de la lib sont
donc enveloppés chacun dans une IIFE, sans quoi leurs noms minifiés de haut
niveau entreraient en collision ; leur `export {}` devient un `return {}`, et
l'`import` du coeur par le module devient une déstructuration. Attention au
`export {...} from "./three.core.min.js"` : c'est une ré-exportation, elle ne
crée pas de liaison locale et doit être reprise depuis l'objet du coeur.

## À brancher

Le formulaire newsletter valide l'adresse puis affiche une confirmation, sans
appel réseau. Pour le rendre réel, remplacer le corps du `submit` par un `fetch`
vers le service d'e-mailing choisi. Les liens `#mentions`, `#cgu` et
`#confidentialite` sont des ancres à remplacer par de vraies pages.
