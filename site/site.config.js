/**
 * Configuration d'un site Ultra Motion.
 *
 * Ce fichier décrit entièrement un site : la marque, l'objet en 3D, les
 * variantes présentées, les arguments, la FAQ. Le moteur — index.html — ne
 * contient aucun contenu propre à une marque et n'a pas besoin d'être modifié.
 *
 * Concevoir un nouveau site revient donc à écrire ce seul fichier, plus les
 * images correspondantes dans assets/web/.
 */

export const CONFIG = {

  /* ---------------------------------------------------------------- marque */
  brand: {
    name: 'HOLA',
    // dernière lettre colorée dans le bandeau, mettre '' pour l'ignorer
    accent: 'A',
    baseline: 'On · 6 saveurs',
    // mention imprimée sous le logotype quand l'artwork n'en porte pas
    mention: '25 CL  |  ZÉRO TAURINE',
    menu: 'Menu',
  },

  meta: {
    lang: 'fr',
    title: 'HOLA ENERGY — Le peps, sans le crash',
    description: "HOLA ENERGY : l'energy drink à 11 g de sucres, arômes 100 % naturels, " +
                 'caféine issue de grains de café et guarana. Six saveurs, zéro taurine.',
  },

  /* --------------------------------------------------------------- rendu */
  theme: 'light',        // 'light' ou 'dark'
  artwork: 'label',      // préfixe des fichiers d'étiquette dans assets/web/
  environment: 'assets/web/env-studio-rgbe.png',
  surface: {
    grain: 'assets/web/alu-grain.jpg',
    droplets: 'assets/web/condensation.jpg',
  },

  /* ---------------------------------------------------------------- objet
     Profil de révolution, du centre du fond au centre du couvercle, en unités
     monde. Décrire une bouteille ou un pot revient à changer ces points. */
  object: {
    height: 1.334,
    profile: [
      [0.000, 0.052], [0.090, 0.044], [0.160, 0.022], [0.205, 0.004], [0.232, 0.000],
      [0.258, 0.010], [0.278, 0.038], [0.288, 0.074], [0.290, 0.110],
      [0.290, 1.115], [0.288, 1.155], [0.279, 1.196], [0.262, 1.235],
      [0.238, 1.268], [0.219, 1.296], [0.211, 1.312],
      [0.216, 1.325], [0.223, 1.331], [0.220, 1.334], [0.206, 1.331], [0.199, 1.323],
      [0.150, 1.316], [0.060, 1.313], [0.000, 1.315],
    ],
    label: { radius: 0.2915, height: 1.02, center: 0.615 },
    tab: true,           // languette d'ouverture, propre aux canettes
    metal: 0xC4CAD4,
  },

  /* ------------------------------------------------------------- variantes
     Une par écran. `glow` teinte la page, `tint` sert de fond d'étiquette
     quand l'artwork n'en porte pas. */
  items: [
    { key:'litchi',  name:'Double Litchi',     glow:'#8B2ED6', tint:'#A94FE0',
      tagline:'Une explosion de litchi frais, sans le sirop. La plus exotique de la gamme.' },
    { key:'coco',    name:'Coco Citron Vert',  glow:'#8FB81E', tint:'#B9D62E',
      tagline:'Le tropique en version sèche : coco crémeuse, lime qui claque.' },
    { key:'kiwi',    name:'Kiwi Concombre',    glow:'#12B07E', tint:'#1FC98F',
      tagline:'La plus fraîche de la bande. Kiwi juteux, concombre, pointe de menthe.' },
    { key:'peche',   name:'Pêche Blanche',     glow:'#FF7A4D', tint:'#FF8A5B',
      tagline:'Douce, mais pas molle. Pêche blanche et fleur d’oranger.' },
    { key:'pomme',   name:'Pomme Rhubarbe',    glow:'#E0356B', tint:'#F04A6E',
      tagline:'Le verger en plus vif : pomme verte acidulée, rhubarbe franche.' },
    { key:'abricot', name:'Abricot Framboise', glow:'#F0912A', tint:'#F5A32E',
      tagline:'Un duo plein soleil. Abricot mûr, framboise, soupçon de vanille.' },
  ],

  /* -------------------------------------------------------------- ouverture */
  intro: {
    title: 'Le peps,<br>sans le crash.',
    sub: 'Six saveurs. 11 g de sucres. Zéro taurine.',
    hint: 'Scroller pour découvrir',
  },

  /* --------------------------------------------------------------- arguments
     Imprimés sur l'objet, un par quart de tour. Quatre au maximum : au-delà,
     ils se chevauchent sur le tour. */
  claims: [
    { title:'11 G DE SUCRES',    crossed:'27 G DE SUCRES',       body:'Contre 27 g en moyenne sur le marché.' },
    { title:'ARÔMES NATURELS',   crossed:'ARÔMES ARTIFICIELS',   body:'Des mélanges d’arômes naturels de fruits.' },
    { title:'CAFÉINE DE GRAINS', crossed:'CAFÉINE ARTIFICIELLE', body:'80 mg extraits de grains d’arabica.' },
    { title:'STÉVIA',            crossed:'ASPARTAME · SUCRALOSE', body:'Un édulcorant d’origine végétale.' },
  ],

  /* -------------------------------------------------------------------- faq */
  faq: {
    title: 'Questions fréquentes',
    items: [
      { q:'Qu’est-ce qui distingue HOLA des autres energy drinks ?',
        a:'Trois fois moins de sucres, des arômes naturels de fruits, une caféine extraite de grains de café plutôt que de synthèse, et de la stévia à la place des édulcorants artificiels.' },
      { q:'Est-ce que c’est pétillant ?',
        a:'Légèrement. On a réduit la gazéification pour que les arômes de fruits restent lisibles.' },
      { q:'Combien de sucres par canette ?',
        a:'11 g pour 25 cl, soit environ 2,7 morceaux, contre 27 g en moyenne sur le marché.' },
      { q:'Y a-t-il des vitamines ?',
        a:'B3, B5, B6 et B12, à hauteur de 100 % des valeurs nutritionnelles de référence par canette.' },
      { q:'Pourquoi pas de taurine ?',
        a:'Parce qu’elle n’apporte rien de démontré à côté de la caféine dans ce type de boisson, et qu’elle alourdit le goût.' },
      { q:'Combien de canettes par jour ?',
        a:'Une à deux maximum. L’apport recommandé pour un adulte reste sous 400 mg de caféine par jour, toutes sources confondues.' },
      { q:'Où est-ce fabriqué ?',
        a:'Recette développée et boisson embouteillée en France, dans les Hauts-de-France. Canettes recyclables à l’infini.' },
    ],
  },

  /* ----------------------------------------------------------- inscription */
  signup: {
    title: 'Rejoignez la bande',
    lede: 'Les nouvelles saveurs et les points de vente qui ouvrent près de chez vous. Un mail par mois, pas plus.',
    placeholder: 'votre@email.fr',
    button: 'Je m’inscris',
    invalid: 'Cette adresse ne ressemble pas à un e-mail. Vérifiez le @ et le nom de domaine.',
    done: 'C’est noté. Le premier mail arrive au prochain lancement de saveur.',
    legal: '© 2026 HOLA ENERGY — marque de démonstration, produit fictif.<br>' +
           'À consommer avec modération. Déconseillé aux enfants, aux adolescents, ' +
           'aux femmes enceintes ou allaitantes.',
  },
};
