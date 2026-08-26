import { redirect, notFound } from "next/navigation";
import Link from "next/link";
import { clientServeur } from "@/lib/supabase/serveur";
import Chat, { type Tour } from "@/composants/Chat";
import Rail from "@/composants/Rail";
import Projection from "@/composants/Projection";
import Etapes from "@/composants/Etapes";
import Nouveau from "@/composants/Nouveau";
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
                    etat="parler" faits={[]} tours={[]} cle={null} publie={false} />;
  }

  const { data: p } = await sb.from("projets")
    .select("id, nom, cle, etat, version").eq("id", projet).single();
  if (!p) notFound();

  const [{ data: faits }, { data: msgs }] = await Promise.all([
    sb.from("faits").select("cle, valeur, origine, source").eq("projet", projet).order("cle"),
    sb.from("messages").select("id, role, texte, meta").eq("projet", projet).order("id"),
  ]);

  // « retrait » n'est pas un rôle de la base : la contrainte n'en connaît
  // que trois. Une rétractation y est un message de journal qui porte, dans
  // sa `meta`, ce qui a été retiré et pourquoi. On la reconstitue ici —
  // sinon, rouvrir le projet montrerait une ligne sèche à la place de la
  // phrase barrée, et le moment le plus utile du produit disparaîtrait au
  // premier rechargement.
  const tours: Tour[] = (msgs ?? []).map((m) => {
    const meta = (m.meta ?? {}) as { trouves?: Tour["trouves"]; retire?: string };
    const retrait = m.role === "journal" && meta.trouves?.length;
    return {
      id: String(m.id),
      role: (retrait ? "retrait" : m.role) as Tour["role"],
      texte: retrait ? (meta.retire ?? m.texte) : m.texte,
      trouves: meta.trouves,
    };
  });

  return <Atelier plan={compte?.plan ?? "essai"} tous={tous ?? []} courant={p.id}
                  etat={p.etat} faits={(faits ?? []) as Fait[]} tours={tours}
                  cle={p.cle} publie={Boolean(p.version)} />;
}

function Atelier(props: {
  plan: string;
  tous: { id: string; nom: string; etat: string }[];
  courant: string | null;
  etat: string;
  faits: Fait[];
  tours: Tour[];
  cle: string | null;
  publie: boolean;
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
        <Nouveau />
      )}

      <main className="scene">
        <Etapes etat={props.etat} />
        <div className="aire">
          <Projection cle={props.cle} publie={props.publie} etat={props.etat} />
          <Rail faits={props.faits} />
        </div>
      </main>
    </div>
  );
}
