import os

# Clé API Anthropic - à mettre dans la variable d'environnement ANTHROPIC_API_KEY
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Nombre maximum d'étapes par tâche
MAX_STEPS = 30

# Port du serveur web
PORT = int(os.environ.get("PORT", 8080))

# Host
HOST = "0.0.0.0"
