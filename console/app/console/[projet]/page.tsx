import { redirect, notFound } from "next/navigation";
import Link from "next/link";
import { clientServeur } from "@/lib/supabase/serveur";
import Chat, { type Tour } from "@/composants/Chat";
import Rail from "@/composants/Rail";
import Projection from "@/composants/Projection";
import Etapes from "@/composants/Etapes";
import type { Fait } from "@/lib/contrat";

export default async function Console({ params }: { params: Promise<{ projet: string }> }) {
  const { projet } = await params;
  const sb = await clientServeur();
  const { data: { user } } = await sb.auth.getUser();
  if (!user) redirect("/connexion");

  const [{ data: compte }, { data: tous }] = await Promise.all([
    sb.from("comptes").select("plan").eq("id", user.id).single(),
    sb.from("projets").select("id, nom, etat").order("maj_le", { ascending: false }),
  ]);

  // « neuf » n'est pas un identifiant : c'est la page vide qu'on voit quand
  // aucun projet n'existe encore.
  if (projet === "neuf") {
    return <Atelier plan={compte?.plan ?? "essai"} tous={tous ?? []} courant={null}
                    etat="parler" faits={[]} tours={[]} url={null} />;
  }

  const { data: p } = await sb.from("projets")
    .select("id, nom, etat, url").eq("id", projet).single();
  if (!p) notFound();

  const [{ data: faits }, { data: msgs }] = await Promise.all([
    sb.from("faits").select("cle, valeur, origine, source").eq("projet", projet).order("cle"),
    sb.from("messages").select("id, role, texte, meta").eq("projet", projet).order("id"),
  ]);

  const tours: Tour[] = (msgs ?? []).map((m) => ({
    id: String(m.id),
    role: m.role as Tour["role"],
    texte: m.texte,
    trouves: (m.meta as { trouves?: Tour["trouves"] })?.trouves,
  }));

  return <Atelier plan={compte?.plan ?? "essai"} tous={tous ?? []} courant={p.id}
                  etat={p.etat} faits={(faits ?? []) as Fait[]} tours={tours}
                  url={p.url} />;
}

function Atelier(props: {
  plan: string;
  tous: { id: string; nom: string; etat: string }[];
  courant: string | null;
  etat: string;
  faits: Fait[];
  tours: Tour[];
  url: string | null;
}) {
  return (
    <div className="atelier">
      <nav className="cote">
        <div className="cote-tete"><div className="logo">UM</div><b>Ultra Motion</b></div>
        <Link className="neuf" href="/console/neuf">
          <span aria-hidden="true">+</span> Nouveau site
        </Link>
        <div className="projets">
          {props.tous.map((p) => (
            <Link key={p.id} href={`/console/${p.id}`}
                  aria-current={p.id === props.courant ? "page" : undefined}>
              <span className="n">{p.nom}</span>
              <span className="e">{p.etat}</span>
            </Link>
          ))}
        </div>
        <div className="cote-pied">
          <span>Plan</span><span className="plan-pastille">{props.plan}</span>
        </div>
      </nav>

      {props.courant ? (
        <Chat projet={props.courant} debut={props.tours} />
      ) : (
        <section className="chat">
          <div className="fil"><div className="fil-dedans">
            <div className="tour">
              <div className="nom"><i /> cheffe</div>
              <div className="corps">
                <p>Créez un projet pour commencer. Je vous demanderai le métier,
                  puis le SIREN — j'interroge le registre plutôt que votre mémoire.</p>
              </div>
            </div>
          </div></div>
        </section>
      )}

      <main className="scene">
        <Etapes etat={props.etat} />
        <div className="aire">
          <Projection url={props.url} etat={props.etat} />
          <Rail faits={props.faits} />
        </div>
      </main>
    </div>
  );
}
