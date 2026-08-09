# HOLA ENERGY — landing page

Page vitrine statique pour une boisson énergisante, dans l'esprit des sites DTC
type [ciaoenergy.com](https://www.ciaoenergy.com) : gamme de saveurs, bénéfices
produit, composition, FAQ, newsletter.

**La marque et le produit sont fictifs** — c'est une démo de design, pas le site
d'une entreprise existante. Le pied de page le mentionne explicitement.

## Aperçu

```bash
python3 -m http.server 8000 --directory site
# http://localhost:8000
```

Un simple double-clic sur `site/index.html` marche aussi : la page est
entièrement autonome.

## Contenu

`site/index.html` — un seul fichier, aucune dépendance réseau :

- polices **Anton** (titres) et **Archivo** (texte) embarquées en base64 ;
- canettes dessinées en SVG, colorées par variables CSS ;
- pas de framework, ~350 lignes de CSS et ~60 lignes de JS.

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
- **Canettes** : un `<symbol>` unique réutilisé via `<use>`. Les styles sont
  écrits en inline dans le symbole — les sélecteurs de classe du document ne
  traversent pas le shadow tree créé par `<use>`, seules les variables CSS
  héritent.
- **Riso** : grain en `feTurbulence` sur `body::after`, plus un calque de
  canette décalé en `mix-blend-mode` (`multiply` en clair, `screen` en sombre)
  qui imite une erreur de repérage d'impression.
- **Accessibilité** : navigation au clavier avec `:focus-visible`, cartes de
  saveur en `<button aria-pressed>`, messages de formulaire en `aria-live`,
  animations désactivées sous `prefers-reduced-motion`.

## À brancher

Le formulaire newsletter valide l'adresse puis affiche une confirmation, sans
appel réseau. Pour le rendre réel, remplacer le corps du `submit` par un `fetch`
vers le service d'e-mailing choisi. Les liens `#mentions`, `#cgu` et
`#confidentialite` sont des ancres à remplacer par de vraies pages.
