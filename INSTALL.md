# AGNT — Guide d'installation complet

## Prérequis
- VPS Ubuntu 22.04
- Accès root
- Clé API Anthropic (console.anthropic.com)

---

## Étape 1 — Connexion SSH à ton VPS

Sur ton PC (Windows : utilise PowerShell ou PuTTY) :
```bash
ssh root@TON_IP_VPS
```

---

## Étape 2 — Mise à jour du système

```bash
apt update && apt upgrade -y
```

---

## Étape 3 — Installation de Python et des outils

```bash
apt install -y python3 python3-pip python3-venv git curl

# Vérifier
python3 --version   # doit afficher 3.10+
```

---

## Étape 4 — Installation des dépendances système pour Playwright

```bash
apt install -y \
  libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
  libcups2 libxkbcommon0 libxcomposite1 libxdamage1 \
  libxfixes3 libxrandr2 libgbm1 libasound2 \
  fonts-liberation libappindicator3-1 xdg-utils \
  libx11-xcb1 libxcb-dri3-0 libxss1
```

---

## Étape 5 — Copier les fichiers du projet

Option A — Via Git (si tu héberges le code sur GitHub) :
```bash
git clone https://github.com/TON_USER/agnt.git
cd agnt
```

Option B — Créer manuellement :
```bash
mkdir -p /root/agnt/static
cd /root/agnt
# Puis copier-coller chaque fichier
```

---

## Étape 6 — Créer l'environnement Python

```bash
cd /root/agnt
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Étape 7 — Installer le navigateur Playwright

```bash
source venv/bin/activate
playwright install chromium
playwright install-deps chromium
```

---

## Étape 8 — Configurer la clé API

```bash
export ANTHROPIC_API_KEY="sk-ant-XXXXXXXXXXXXXXXX"

# Pour que ça persiste après reboot :
echo 'export ANTHROPIC_API_KEY="sk-ant-XXXXXXXXXXXXXXXX"' >> /root/.bashrc
source /root/.bashrc
```

---

## Étape 9 — Lancer l'agent

```bash
cd /root/agnt
source venv/bin/activate
python server.py
```

Tu dois voir :
```
 * Running on http://0.0.0.0:8080
```

---

## Étape 10 — Ouvrir dans le navigateur

Va sur : `http://TON_IP_VPS:8080`

---

## Étape 11 (optionnel) — Lancer en arrière-plan avec screen

```bash
apt install -y screen
screen -S agnt
cd /root/agnt && source venv/bin/activate && python server.py
# Ctrl+A puis D pour détacher
# screen -r agnt pour reprendre
```

---

## Étape 12 (optionnel) — Ouvrir le port firewall

```bash
ufw allow 8080
ufw enable
```

---

## Structure du projet

```
agnt/
├── agent.py          # Boucle principale de l'agent
├── browser.py        # Contrôle Playwright
├── config.py         # Configuration
├── server.py         # Serveur web Flask
├── requirements.txt  # Dépendances Python
└── static/
    └── index.html    # Interface web
```

---

## Dépannage

**Playwright ne trouve pas Chromium :**
```bash
playwright install chromium --with-deps
```

**Port 8080 refusé :**
```bash
ufw allow 8080
```

**ModuleNotFoundError :**
```bash
source venv/bin/activate  # Toujours activer le venv !
```

**L'agent est bloqué sur un CAPTCHA :**
C'est normal sur certains sites (Google, Indeed). Essaie des sites moins protégés pour tester.
