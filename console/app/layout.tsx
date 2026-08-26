import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ultra Motion — la console",
  description:
    "Fabrique des sites d'une page où un film défile au rythme du défilement. " +
    "Rien n'est écrit sur votre entreprise sans sa source.",
};

// Le thème sombre est le défaut assumé : la fenêtre de projection montre un
// site noir, et une chrome claire autour ferait mal juger ses couleurs.
export const viewport: Viewport = { colorScheme: "dark light" };

export default function Racine({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          rel="stylesheet"
          href={
            "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500" +
            "&family=IBM+Plex+Sans:wght@400;500;600&family=Instrument+Serif&display=swap"
          }
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
