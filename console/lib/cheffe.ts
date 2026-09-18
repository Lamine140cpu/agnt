/**
 * La cheffe d'orchestre : la seule qui parle au client, et la seule qui
 * touche au contrat.
 *
 * SON VRAI MÉTIER N'EST PAS DE CONVERSER, C'EST DE TENIR LE CONTRAT. Les
 * décisions qui font marcher ce genre de site sont numériques — 33 px par
 * image, 64 % de hauteur de toile, 4,5:1 de contraste. Une cheffe qui se
 * contente de relayer de la prose les perd toutes.
 *
 * DEUX GARDE-FOUS L'ENCADRENT, et ils ne se remplacent pas :
 *
 *   1. la consigne lui dit de ne rien inventer ;
 *   2. `verifierTexte` VÉRIFIE qu'elle ne l'a pas fait.
 *
 * Le second n'est pas une ceinture de sécurité en plus du premier : c'est le
 * seul des deux qui tienne. Demander gentiment à un modèle de ne pas
 * compléter, c'est lui demander de ne pas faire son métier.
 */
import Anthropic from "@anthropic-ai/sdk";

/** Les deux rôles, et leurs réglages. Écrits ici et nulle part ailleurs. */
export const ROLES = {
  // Elle dialogue : quelqu'un attend devant l'écran.
  cheffe: { modele: "claude-opus-5", effort: "medium", jetons: 8_000 },
  // Il écrit hors ligne : personne n'attend, la qualité prime.
  architecte: { modele: "claude-fable-5", effort: "xhigh", jetons: 16_000 },
} as const;

export const CONSIGNE = `Tu es la cheffe d'orchestre d'Ultra Motion. Tu fabriques des
sites d'une seule page où un film défile au rythme du défilement : un
plan-séquence d'une cinquantaine de secondes, découpé en images, redessiné
sur une toile. Six actes de texte, un par plan.

TON MÉTIER EST DE TENIR LE CONTRAT, PAS DE FAIRE LA CONVERSATION.

LA RÈGLE QUI PASSE AVANT TOUTES LES AUTRES

Tu n'écris jamais un fait sur l'entreprise sans sa source. Jamais
d'ancienneté, de nombre de véhicules ou de salariés, de certification, de
zone desservie, d'horaires, de téléphone, de date de création — sauf s'il
vient du registre ou si le client vient de te le donner, et alors tu
l'enregistres avec son origine.

Ce n'est pas une préférence de style. Un contrôle automatique compare
chacune de tes phrases aux faits déclarés et REFUSE ce qui déborde. Si tu
écris un chiffre non déclaré, ton message est retiré sous les yeux du
client. Tu peux parler du métier, du geste, de la matière : tout cela est
vrai sans avoir besoin d'être vérifié.

Un fait que tu ne connais pas devient une QUESTION OUVERTE. Tu ne la combles
pas, tu ne l'estimes pas, et tu ne la contournes pas par une formule vague.
Le directeur de la publication et l'hébergeur sont des obligations légales :
une estimation y serait un faux. Si le client insiste pour que tu estimes,
refuse — c'est le seul endroit où tu lui tiens tête, et tu lui expliques
pourquoi en une phrase.

CE QUE TU FAIS, DANS CET ORDRE

1. Comprendre le métier et à qui il s'adresse. Peu de questions, précises.
2. Demander le SIREN, et interroger le registre plutôt que le client.
3. Poser les faits obtenus, ouvrir les questions que le registre ne sait pas.
4. Demander les ressources : logo, photos, ce qui existe déjà.
5. Quand le contrat tient debout, lancer l'écriture puis le film.

TON

Bref, concret, tutoiement exclu — vouvoiement. Pas de listes à puces sauf
pour énumérer des questions ouvertes. Pas de superlatifs, pas de « n'hésitez
pas ». Une phrase qui dit une chose vaut mieux que trois qui l'enrobent.
Réponds en français.`;

/* ------------------------------------------------------------- les outils */

export const OUTILS: Anthropic.Tool[] = [
  {
    name: "chercher_registre",
    description:
      "Interroge le registre public des entreprises à partir d'un SIREN " +
      "(9 chiffres). Rend les faits officiels, avec leur source. À préférer " +
      "toujours à ce que le client dit de mémoire.",
    input_schema: {
      type: "object",
      properties: { siren: { type: "string", description: "9 chiffres" } },
      required: ["siren"],
      additionalProperties: false,
    },
  },
  {
    name: "poser_faits",
    description:
      "Enregistre des faits dans le contrat. Chaque fait DOIT porter son " +
      "origine et sa source. N'appelle jamais cet outil pour un fait que tu " +
      "as déduit, estimé ou supposé.",
    input_schema: {
      type: "object",
      properties: {
        faits: {
          type: "array",
          items: {
            type: "object",
            properties: {
              cle: { type: "string" },
              valeur: { type: "string" },
              origine: { type: "string", enum: ["registre", "client", "mesure", "choix"] },
              source: {
                type: "string",
                description:
                  "D'où vient ce fait : le nom du registre, ou « le client, " +
                  "le <date> » quand il l'a dit lui-même.",
              },
            },
            required: ["cle", "valeur", "origine", "source"],
            additionalProperties: false,
          },
        },
      },
      required: ["faits"],
      additionalProperties: false,
    },
  },
  {
    name: "ouvrir_questions",
    description:
      "Déclare des faits comme MANQUANTS. Ils apparaissent au client comme " +
      "questions ouvertes, et la page n'affirmera rien à leur sujet.",
    input_schema: {
      type: "object",
      properties: { cles: { type: "array", items: { type: "string" } } },
      required: ["cles"],
      additionalProperties: false,
    },
  },
  {
    name: "lancer",
    description:
      "Met une étape du moteur en file : écrire les six actes, produire le " +
      "film, construire la page, contrôler. N'appelle cet outil que lorsque " +
      "le contrat a de quoi la mener à bien.",
    input_schema: {
      type: "object",
      properties: {
        quoi: { type: "string", enum: ["ecrire", "filmer", "construire", "controler"] },
      },
      required: ["quoi"],
      additionalProperties: false,
    },
  },
];

/* ---------------------------------------------------------- la frontière */

export class SansCle extends Error {
  constructor() {
    super("ANTHROPIC_API_KEY absente — la cheffe ne peut pas répondre.");
    this.name = "SansCle";
  }
}

export function client() {
  const cle = process.env.ANTHROPIC_API_KEY;
  if (!cle) throw new SansCle();
  return new Anthropic({ apiKey: cle });
}

/**
 * Ouvre le flux d'une réponse de la cheffe.
 *
 * Trois réglages comptent, et ils ne sont pas décoratifs :
 *
 *  - le FLUX : sans lui une réponse longue tombe en délai d'attente ;
 *  - les REPLIS DE REFUS : un refus de sécurité rend une réponse vide avec
 *    un code 200. Sans repli, le chat se tait sans rien dire ;
 *  - l'EFFORT : `medium` ici, parce que quelqu'un attend en face.
 */
type ParamsFlux = Parameters<
  ReturnType<typeof client>["beta"]["messages"]["stream"]
>[0];

/**
 * LES REPLIS DE REFUS — passés par-dessus les types, et il faut savoir
 * pourquoi.
 *
 * Le SDK installé (0.71.x) ne connaît encore ni le champ `fallbacks` ni ce
 * drapeau bêta : ils sont plus récents que ses types. Le corps de la requête
 * étant sérialisé tel quel, les champs partent quand même — mais ça n'a PAS
 * été vérifié contre l'API, faute de clé dans l'environnement où ce fichier
 * a été écrit.
 *
 * À éprouver le jour où une clé arrive : envoyer une demande qui déclenche
 * un refus, et regarder si la réponse porte un bloc `fallback`. Si l'API
 * répond 400 sur un champ inconnu, c'est que le SDK doit être remonté — et
 * non que ce bloc doit être supprimé : sans repli, un refus de sécurité rend
 * une réponse vide avec un code 200, et le chat se tait sans rien dire.
 */
const REPLIS = {
  betas: ["server-side-fallback-2026-07-01"],
  fallbacks: "default",
};

export function flux(messages: Anthropic.MessageParam[], contexte: string) {
  const base = {
    model: ROLES.cheffe.modele,
    max_tokens: ROLES.cheffe.jetons,
    system: [
      // La consigne ne bouge jamais : elle est mise en cache, et le contexte
      // — qui change à chaque tour — vient après elle, jamais avant.
      { type: "text" as const, text: CONSIGNE,
        cache_control: { type: "ephemeral" as const } },
      { type: "text" as const, text: contexte },
    ],
    output_config: { effort: ROLES.cheffe.effort },
    tools: OUTILS,
    messages,
  };
  return client().beta.messages.stream({ ...base, ...REPLIS } as ParamsFlux);
}
