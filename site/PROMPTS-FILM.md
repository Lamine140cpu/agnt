# Fabriquer le film — le carnet de prompts

Pour commander à un modèle vidéo une pellicule qui tienne dans ce lecteur. Tout
ce qui suit vient de ce qui a été mesuré ou payé sur les deux films déjà faits.

Un modèle vidéo donne huit secondes. Il en faut **quarante à cinquante** :
six plans enchaînés par leur dernière image.

---

## 1. Ce qu'il faut produire, en chiffres

```
course du prologue      26 100 px   (mesurée dans la page, elle dépend de la mise en page)
densité visée               33 px de défilement par image
images nécessaires         791
images sources          1 000 à 1 200   pour garder de la marge au sous-échantillonnage
durée de film              40 à 50 s à 24 i/s
plans                       6 de 8 s, enchaînés
définition             1920×1080 minimum, 4K si le modèle sait le faire
format                      16:9 STRICT
```

Le format n'est pas négociable : tout le reste — recadrage téléphone, plafond
de densité de pixels, choix de série — est calculé à partir de lui.

---

## 2. Les six règles qui décident si le film marchera

Elles ne sont pas des préférences. Chacune vient d'un défaut constaté.

**1. Un seul mouvement, dans un seul sens.**
Le défilement mappe la position sur le temps. Une caméra qui revient en arrière
se lit comme un bug, pas comme un effet. Travelling, panoramique ou rapproché
continus — jamais d'aller-retour.

**2. Lent. Plus lent que ce qui paraît juste en lecture normale.**
Le visiteur scrube : il traverse en deux secondes ce que la vidéo montre en
huit. Tout mouvement est amplifié. Un plan qui semble mou en lecture est
généralement le bon.

**3. Aucune coupe à l'intérieur d'un plan.**
Une coupe dans un plan devient un saut à mi-défilement, impossible à distinguer
d'une image manquante.

**4. Aucun texte, aucun logo demandé au modèle.**
Mesuré sur le film Trans Gold : les inscriptions générées sortent en charabia —
« PANLLETENTIAR EEPTEHINOISOG E ALL » sur le flanc d'un camion. Le logo se pose
après, en HTML, à partir du fichier du client. Ne jamais l'écrire dans le
prompt.

**5. Le sujet au centre, et de la marge autour.**
Sur téléphone, si la série étroite est un recadrage, l'écran ne montre que
**26 % de la largeur** du cadre. Un sujet excentré en sort. Composer comme si
le tiers central devait suffire.

**6. Aucun visage en gros plan.**
D'un plan à l'autre, un modèle ne redonne pas le même visage. Mains, silhouettes,
dos, gestes de métier : oui. Portraits : non.

---

## 3. La structure d'une chorégraphie

Celle qui a marché deux fois : **du large vers le détail, puis vers le lieu où
ça sert**. Six plans, un par acte de la page.

```
1  L'OBJET EN MOUVEMENT      ce que le client fait, en action, vu de loin
2  LE RAPPROCHÉ              la matière, la marque, la mécanique
3  LE GESTE                  les mains au travail, l'outil qui mord
4  L'INTÉRIEUR               l'atelier, la remorque, le fournil — où ça se fabrique
5  LE LIEU DE TRAVAIL        vue d'ensemble de l'outil de production
6  LA DESTINATION            le client, la rue, la table, le chantier
```

---

## 4. Le gabarit de prompt

À recopier tel quel, en remplaçant ce qui est entre crochets.

```
[SUJET ET ACTION], filmé en plan continu de 8 secondes.
Mouvement de caméra : [travelling latéral lent / avancée lente / panoramique
lent], vitesse constante, une seule direction, aucun arrêt, aucune coupe.
Lumière : [heure et qualité], constante pendant tout le plan.
Cadre : 16:9, sujet centré, marge autour du sujet.
Rendu photographique réaliste, profondeur de champ modérée.
Aucun texte, aucune inscription, aucun logo, aucun visage en gros plan.
```

Les trois lignes de fin ne sautent jamais : ce sont elles qui évitent les
défauts du § 2.

**Pour les plans 2 à 6**, fournir en image de départ la dernière image du plan
précédent :

```bash
python3 film_raccord.py plan1.mp4 amorce2.png
```

Sans cette amorce, chaque plan repart d'un sujet légèrement différent — autre
teinte, autre position d'ombre — et les jointures sautent aux yeux.

---

## 5. Trois séries prêtes à l'emploi

### Menuiserie / ébénisterie

```
1  Un établi de menuisier dans un atelier, planches de chêne empilées, copeaux
   au sol, filmé en travelling latéral lent qui longe l'établi. Lumière de fin
   d'après-midi entrant par une verrière, constante. 16:9, sujet centré.
   Photographique. Aucun texte, aucune inscription, aucun visage en gros plan.

2  Avancée lente vers le fil du bois d'un plateau de chêne brut, les veines
   nettes, la poussière en suspension dans un rai de lumière. Mouvement continu,
   vitesse constante. 16:9. Aucun texte, aucun visage.

3  Les mains d'un artisan passant un rabot sur une planche, le copeau qui se
   lève et s'enroule, en plan rapproché continu. Caméra qui suit le geste
   latéralement, lentement. 16:9. Aucun visage, aucune inscription.

4  Travelling lent dans un atelier de menuiserie : scie à format, serre-joints
   au mur, panneaux debout contre une cloison. Lumière d'atelier constante.
   16:9, profondeur de champ modérée. Aucun texte.

5  Panoramique lent sur un escalier en bois massif en cours d'assemblage,
   posé sur tréteaux, dans l'atelier. Un seul sens, sans arrêt. 16:9.
   Aucun texte, aucun logo.

6  Avancée lente dans une pièce d'habitation où une bibliothèque sur mesure
   vient d'être posée, lumière du jour par une fenêtre à gauche. Mouvement
   continu. 16:9. Aucun visage, aucune inscription.
```

### Boulangerie artisanale

```
1  Travelling latéral lent le long d'un fournil, four à sole en arrière-plan,
   pâtons alignés sur une toile de lin. Lumière chaude et constante. 16:9,
   sujet centré. Photographique. Aucun texte, aucun visage en gros plan.

2  Avancée lente vers la croûte d'un pain de campagne fendu, la mie visible,
   la farine en surface. Mouvement continu, vitesse constante. 16:9.
   Aucune inscription.

3  Les mains d'un boulanger façonnant un pâton sur un plan fariné, en plan
   rapproché, caméra qui suit le geste latéralement et lentement. 16:9.
   Aucun visage, aucun texte.

4  Travelling lent devant l'ouverture d'un four à sole, les braises rougeoyantes
   au fond, la chaleur qui trouble l'air. Un seul sens, sans arrêt. 16:9.
   Aucun texte, aucun logo.

5  Panoramique lent sur un pétrin en inox tournant, la pâte qui s'enroule au
   crochet. Vitesse constante. 16:9. Aucune inscription.

6  Avancée lente dans une boutique de boulangerie au petit matin, corbeilles
   de pains sur des étagères en bois, lumière du jour par la vitrine.
   Mouvement continu. 16:9. Aucun visage en gros plan, aucun texte.
```

### Garage / carrosserie

```
1  Travelling latéral lent le long d'une rangée de voitures dans un atelier de
   mécanique, pont élévateur en arrière-plan. Lumière d'atelier constante.
   16:9, sujet centré. Photographique. Aucun texte, aucune plaque
   d'immatriculation lisible, aucun visage en gros plan.

2  Avancée lente vers un moteur ouvert, culasse et durites visibles, reflets
   sur le métal. Mouvement continu, vitesse constante. 16:9. Aucune inscription.

3  Les mains d'un mécanicien serrant un écrou à la clé dynamométrique, plan
   rapproché, caméra qui accompagne le geste lentement. 16:9. Aucun visage,
   aucun texte.

4  Travelling lent sous une voiture levée sur un pont élévateur, le châssis et
   les suspensions vus de dessous, lumière rasante. Un seul sens. 16:9.
   Aucun texte, aucun logo de marque.

5  Panoramique lent sur un mur d'outils dans un atelier — clés, servantes,
   compresseur. Vitesse constante. 16:9. Aucune inscription lisible.

6  Avancée lente dans une cour de garage au petit matin, une voiture propre
   prête à être rendue, lumière douce. Mouvement continu. 16:9.
   Aucun visage en gros plan, aucun texte.
```

---

## 6. Ce qu'il faut faire des plans, une fois générés

**Profiler AVANT d'extraire.** Les modèles finissent presque toujours sur un gel
d'une à deux secondes. Gardé tel quel, ce gel occupe le même espace de
défilement que le reste : **un cinquième de la page où plus rien ne bouge**.

```bash
python3 film_video.py plan1.mp4 profil
```

Le profil mesure l'écart entre images consécutives, signale les coupes, et dit
où le mouvement s'arrête. On rogne ensuite dans le temps :

```bash
python3 film_video.py plan1.mp4@0-180 plan2.mp4@6-190 … 1152 1920 large
```

Puis, si la densité reste au-dessus de 40 px par image, fabriquer des images
intermédiaires par flot optique plutôt que de regénérer :

```bash
python3 film_interpole.py
```

Enfin la construction et le contrôle :

```bash
python3 build_flux.py client=<nom> manifeste=generateur/manifeste-<nom>.json
python3 generateur/controleur.py generateur/manifeste-<nom>.json dist/<nom>
```

---

## 7. Les trois façons de rater un film, par ordre de fréquence

1. **Le gel de fin de plan**, gardé. Un cinquième du défilement immobile.
   → profiler, rogner.
2. **Les plans non enchaînés.** Chaque plan repart d'un sujet légèrement
   différent, et les jointures sautent au défilement.
   → `film_raccord.py`, systématiquement.
3. **Le mouvement trop rapide.** Correct en lecture, illisible au scrub.
   → toujours plus lent que ce qui paraît juste.
