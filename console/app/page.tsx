import { redirect } from "next/navigation";
import { clientServeur } from "@/lib/supabase/serveur";

export default async function Accueil() {
  const sb = await clientServeur();
  const { data: { user } } = await sb.auth.getUser();
  if (!user) redirect("/connexion");

  const { data } = await sb.from("projets")
    .select("id").order("maj_le", { ascending: false }).limit(1);

  redirect(data?.[0] ? `/console/${data[0].id}` : "/console/neuf");
}
