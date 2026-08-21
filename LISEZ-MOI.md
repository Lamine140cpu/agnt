# Ultra Motion — la vitrine

Une page qui ne défile pas : elle **avance**. Le visiteur traverse une villa,
longe une piscine, fait le tour d'une voiture, entre dans un restaurant, puis
en cuisine, et voit un produit se démonter — d'un seul mouvement continu,
sans une seule coupe, au rythme de son propre défilement.

Techniquement, ce n'est pas une vidéo. C'est une suite de 1 440 images fixes
posées sur une toile, dont l'index suit la position de défilement. La
différence se voit dès qu'on s'arrête : on s'arrête *sur* une image, nette,
et non sur une trame de vidéo compressée en mouvement. Et on peut revenir en
arrière aussi vite qu'on est allé en avant.

## Ce que ce dépôt contient

Le **résultat construit**, et rien d'autre : `index.html` et les images. Les
scripts de construction, la continuité des plans et les notes de travail
vivent ailleurs, dans un dépôt privé.

```
index.html                       la page — 50 Ko
assets/film/accueil/             1 440 images, 1280 px, cadrées 16:9
assets/film/accueil-etroit/      1 440 images,  720 px, cadrées 9:16
assets/fonts/ultra.css           les polices, embarquées
```

Deux séries et non une : les plans 3 à 6 ont été tournés **nativement à la
verticale**. La série portrait n'est pas la paysage rognée — la recadrer
depuis l'autre couperait le pain du burger et les trois quarts de la voiture.
La page choisit d'elle-même selon la forme de l'écran.

## Le poids ne se télécharge pas

Les 55 Mo d'images ne partent jamais d'un bloc. Le lecteur ne demande que
celles dont sa fenêtre glissante a besoin, le navigateur les met en cache, et
une seconde visite ne retélécharge rien. Mesuré au chargement : **une
trentaine de kilo-octets avant que la page se dévoile.**

## Pourquoi 1280 px et pas 1920

Ce n'est pas le poids qui l'interdit, c'est le temps de décodage. Mesuré dans
un navigateur, sur soixante images décodées en parallèle :

| définition | par image | images par seconde |
|---|---|---|
| 640 px | 1,89 ms | 529 |
| **1280 px** | **12,39 ms** | **81** |
| 1600 px | 26,66 ms | 38 |
| 1920 px | 29,76 ms | 34 |

Un défilement ordinaire consomme 70 à 100 images par seconde. À 1920 px le
navigateur en fournit 34 : il resterait bloqué sur la même image un tiers du
temps. Le mode de défaillance n'est pas une erreur — quand l'image demandée
n'est pas encore décodée, le lecteur repose la voisine. Ça se voit comme un
à-coup, jamais comme une panne.

## Le lancer chez soi

Il faut un serveur. **Double-cliquer `index.html` ne marche pas** : le
protocole `file://` interdit à la page d'aller chercher ses images voisines.

```
python3 -m http.server 8000
```

puis `http://localhost:8000`. Pour l'ouvrir depuis un téléphone sur le même
Wi-Fi, ajouter `--bind 0.0.0.0` et viser l'adresse de l'ordinateur.

## Licences

Voir [`LICENCES.md`](LICENCES.md). En résumé : les polices sont sous SIL Open
Font License, et les images sont une démonstration du procédé — aucun des
lieux ni des produits montrés n'existe. Une vitrine livrée à un client montre
**son** bien, filmé.
