# Les scènes en splats gaussiens

Les fichiers `.ums` ne sont pas versionnés : ce sont des dérivés, et leur
source impose ses propres conditions.

## Refabriquer la scène de démonstration

```bash
curl -L -o /tmp/room.splat \
  https://huggingface.co/cakewalk/splat-data/resolve/main/room.splat
python3 splat_reduire.py /tmp/room.splat piece 400000 7
```

`room.splat` est la scène « room » du jeu de données Mip-NeRF 360, entraînée
par le projet 3D Gaussian Splatting de l'INRIA. **Elle est publiée pour la
recherche et l'enseignement, pas pour un usage commercial.** Elle sert ici à
mettre le moteur au point ; un site en production demande une capture faite
pour lui, ou une scène sous licence adaptée.

## Fabriquer la sienne

Filmer le lieu au téléphone, puis entraîner avec un outil libre — Nerfstudio,
gsplat, Postshot. La sortie est un `.ply`, converti en `.splat` puis passé à
`splat_reduire.py`. C'est de loin la meilleure qualité : les photographies
viennent du lieu réel, et la caméra s'y déplace librement.
