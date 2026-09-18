"use client";

/**
 * Le chat.
 *
 * Il ressemble à ce qu'on attend d'une interface moderne — le texte
 * ruisselle, le composeur grandit avec ce qu'on écrit, Entrée envoie et
 * Maj+Entrée passe à la ligne. Une chose l'en distingue, et c'est le sujet
 * du produit :
 *
 *   QUAND LE GARDE-FOU REPREND UN MESSAGE, ON LE VOIT.
 *
 * Le texte s'affiche, puis il est relu, et s'il avance un fait non déclaré
 * il est BARRÉ sous les yeux de l'utilisateur, avec la liste de ce qui a été
 * retiré. On aurait pu masquer l'incident en attendant la fin pour tout
 * afficher. On ne le fait pas : un modèle qui se corrige en public vaut
 * mieux qu'un modèle qui n'a jamais l'air de se tromper — et le second
 * n'existe pas.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import type { Invention } from "@/lib/contrat";

export interface Tour {
  id: string;
  role: "client" | "cheffe" | "journal" | "retrait";
  texte: string;
  trouves?: Invention[];
}

interface Props {
  projet: string;
  debut: Tour[];
  onOutil?: (nom: string, resultat: unknown) => void;
}

export default function Chat({ projet, debut, onOutil }: Props) {
  const [tours, setTours] = useState<Tour[]>(debut);
  const [brouillon, setBrouillon] = useState("");
  const [saisie, setSaisie] = useState("");
  const [occupe, setOccupe] = useState(false);
  const [souci, setSouci] = useState<string | null>(null);
  const filRef = useRef<HTMLDivElement>(null);
  const zoneRef = useRef<HTMLTextAreaElement>(null);

  // On ne recolle en bas QUE si l'utilisateur y était déjà : le tirer vers le
  // bas pendant qu'il relit plus haut est la faute la plus agaçante d'un chat.
  const colle = useRef(true);
  const auBas = () => {
    const f = filRef.current;
    if (f) colle.current = f.scrollHeight - f.scrollTop - f.clientHeight < 90;
  };
  useEffect(() => {
    const f = filRef.current;
    if (f && colle.current) f.scrollTop = f.scrollHeight;
  }, [tours, brouillon]);

  const grandir = useCallback(() => {
    const z = zoneRef.current;
    if (!z) return;
    z.style.height = "auto";
    z.style.height = Math.min(z.scrollHeight, 190) + "px";
  }, []);

  async function envoyer() {
    const texte = saisie.trim();
    if (!texte || occupe) return;
    setSaisie("");
    setSouci(null);
    setOccupe(true);
    colle.current = true;
    setTours((t) => [...t, { id: `m${Date.now()}`, role: "client", texte }]);
    requestAnimationFrame(grandir);

    let recu = "";
    try {
      const r = await fetch("/api/cheffe", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ projet, texte }),
      });
      if (!r.ok || !r.body) throw new Error(await r.text() || `erreur ${r.status}`);

      const lecteur = r.body.getReader();
      const dec = new TextDecoder();
      let reste = "";

      for (;;) {
        const { done, value } = await lecteur.read();
        if (done) break;
        reste += dec.decode(value, { stream: true });
        const morceaux = reste.split("\n\n");
        reste = morceaux.pop() ?? "";

        for (const m of morceaux) {
          if (!m.startsWith("data: ")) continue;
          const e = JSON.parse(m.slice(6));

          if (e.type === "texte") {
            recu += e.delta;
            setBrouillon(recu);
          } else if (e.type === "outil") {
            setTours((t) => [...t, {
              id: `o${Date.now()}${Math.random()}`,
              role: "journal",
              texte: journalDe(e.nom, e.resultat),
            }]);
            onOutil?.(e.nom, e.resultat);
          } else if (e.type === "refus") {
            // Le message est déjà à l'écran. On ne l'efface pas : on le barre.
            setBrouillon("");
            setTours((t) => [...t, {
              id: `r${Date.now()}`, role: "retrait",
              texte: recu, trouves: e.trouves as Invention[],
            }]);
            recu = "";
          } else if (e.type === "erreur") {
            setSouci(e.message);
          } else if (e.type === "fin") {
            if (recu.trim()) {
              setTours((t) => [...t, {
                id: `c${Date.now()}`, role: "cheffe", texte: recu,
              }]);
            }
            setBrouillon("");
            recu = "";
          }
        }
      }
    } catch (e) {
      setSouci(e instanceof Error ? e.message : "la connexion a été coupée");
      setBrouillon("");
    } finally {
      setOccupe(false);
      zoneRef.current?.focus();
    }
  }

  return (
    <section className="chat">
      <div className="fil" ref={filRef} onScroll={auBas} aria-live="polite">
        <div className="fil-dedans">
          {tours.map((t) => <Bulle key={t.id} tour={t} />)}

          {brouillon && (
            <div className="tour">
              <div className="nom"><i /> cheffe</div>
              <div className="corps">
                {enParagraphes(brouillon)}
                <span className="curseur" aria-hidden="true" />
              </div>
            </div>
          )}

          {occupe && !brouillon && (
            <div className="tour">
              <div className="nom"><i /> cheffe</div>
              <div className="tape"><i /><i /><i /></div>
            </div>
          )}

          {souci && (
            <div className="avis mauvais" role="alert">{souci}</div>
          )}
        </div>
      </div>

      <div className="composeur">
        <div className="composeur-dedans">
          <div className="boite">
            <textarea
              ref={zoneRef}
              rows={1}
              value={saisie}
              placeholder="Décrivez le métier, ou donnez le SIREN…"
              aria-label="Votre message"
              disabled={occupe}
              onChange={(e) => { setSaisie(e.target.value); grandir(); }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); envoyer(); }
              }}
            />
            <button
              className="envoyer"
              onClick={envoyer}
              disabled={occupe || !saisie.trim()}
              aria-label="Envoyer"
            >
              <svg width="15" height="15" viewBox="0 0 16 16" fill="none"
                   stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"
                   strokeLinejoin="round" aria-hidden="true">
                <path d="M8 13V3M4 7l4-4 4 4" />
              </svg>
            </button>
          </div>
          <p className="sous">
            Rien n'est écrit sur votre entreprise sans sa source.
          </p>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------- affichage */

function Bulle({ tour }: { tour: Tour }) {
  if (tour.role === "journal") {
    return <div className="journal"><div>{tour.texte}</div></div>;
  }

  if (tour.role === "retrait") {
    return (
      <div className="retrait" role="status">
        <p className="quoi">
          Je retire ce message : il avance{" "}
          {tour.trouves?.length === 1 ? "un fait" : `${tour.trouves?.length} faits`}{" "}
          que je ne peux pas justifier.
        </p>
        <p className="barre">{tour.texte}</p>
        <ul>
          {tour.trouves?.map((t, i) => (
            <li key={i}>{t.quoi} — « {t.extrait} »</li>
          ))}
        </ul>
      </div>
    );
  }

  const moi = tour.role === "client";
  return (
    <div className={`tour${moi ? " moi" : ""}`}>
      {!moi && <div className="nom"><i /> cheffe</div>}
      <div className="corps">{enParagraphes(tour.texte)}</div>
    </div>
  );
}

/** Les paragraphes, sans passer par un rendu HTML : le texte du modèle ne
 *  doit jamais devenir du balisage exécuté. */
function enParagraphes(t: string) {
  return t.split(/\n{2,}/).map((p, i) => (
    <p key={i}>
      {p.split("\n").map((l, j) => (
        <span key={j}>{j > 0 && <br />}{l}</span>
      ))}
    </p>
  ));
}

function journalDe(nom: string, r: unknown): string {
  const d = (r ?? {}) as Record<string, unknown>;
  if (nom === "chercher_registre") {
    return d.trouve
      ? `registre — ${d.faits} faits relevés, ${d.ouvertes} questions ouvertes`
      : "registre — aucun établissement à ce SIREN";
  }
  if (nom === "poser_faits") {
    return d.refuse ? `refusé — ${d.motif}` : `contrat — ${d.poses} fait(s) posés`;
  }
  if (nom === "ouvrir_questions") return `contrat — ${d.ouvertes} question(s) ouverte(s)`;
  if (nom === "lancer") return `moteur — « ${d.quoi} » mis en file`;
  return `${nom} — ${JSON.stringify(r)}`;
}
