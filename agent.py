import anthropic
import base64
import json
from browser import Browser
from config import ANTHROPIC_API_KEY, MAX_STEPS

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Tu es un agent de navigation web autonome. Tu contrôles un vrai navigateur pour accomplir des tâches complexes.

À chaque étape, tu reçois un screenshot du navigateur et tu dois décider de la prochaine action.

Actions disponibles (réponds TOUJOURS en JSON valide) :
- {"action": "navigate", "url": "https://..."}
- {"action": "click", "x": 123, "y": 456}
- {"action": "type", "text": "texte à taper"}
- {"action": "scroll", "direction": "down", "amount": 300}
- {"action": "wait", "seconds": 2}
- {"action": "screenshot"}
- {"action": "done", "message": "Tâche accomplie : ..."}
- {"action": "error", "message": "Impossible de continuer car ..."}

Règles :
1. Analyse PRÉCISÉMENT le screenshot avant d'agir
2. Sois méthodique : une action à la fois
3. Si tu vois un CAPTCHA, utilise {"action": "wait", "seconds": 5} puis réessaie
4. Quand la tâche est accomplie, utilise "done"
5. Réponds UNIQUEMENT en JSON, rien d'autre
"""

def encode_screenshot(path: str) -> str:
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")

def run_agent(task: str, callback=None) -> dict:
    browser = Browser()
    history = []
    steps_log = []

    def log(step_type, content):
        entry = {"type": step_type, "content": content}
        steps_log.append(entry)
        if callback:
            callback(entry)

    try:
        browser.start()
        log("start", f"Démarrage de l'agent pour : {task}")

        for step in range(MAX_STEPS):
            # Prendre un screenshot
            screenshot_path = browser.screenshot(f"/tmp/step_{step}.png")
            screenshot_b64 = encode_screenshot(screenshot_path)

            log("screenshot", screenshot_path)

            # Construire le message pour Claude
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Tâche : {task}\n\nÉtape {step + 1}/{MAX_STEPS}. Voici le screenshot actuel du navigateur. Quelle est la prochaine action ?"
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": screenshot_b64
                            }
                        }
                    ]
                }
            ]

            # Ajouter l'historique des actions précédentes
            if history:
                history_text = "\n".join([f"- Étape {i+1}: {h}" for i, h in enumerate(history)])
                messages[0]["content"][0]["text"] += f"\n\nActions déjà effectuées :\n{history_text}"

            # Appel Claude API
            response = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=500,
                system=SYSTEM_PROMPT,
                messages=messages
            )

            raw = response.content[0].text.strip()
            log("thinking", raw)

            # Parser la réponse JSON
            try:
                action = json.loads(raw)
            except json.JSONDecodeError:
                # Essayer d'extraire le JSON si Claude a ajouté du texte
                import re
                match = re.search(r'\{.*\}', raw, re.DOTALL)
                if match:
                    action = json.loads(match.group())
                else:
                    log("error", "Réponse invalide de Claude")
                    break

            log("action", action)
            history.append(str(action))

            # Exécuter l'action
            action_type = action.get("action")

            if action_type == "done":
                log("done", action.get("message", "Tâche accomplie"))
                return {"success": True, "message": action.get("message"), "steps": steps_log}

            elif action_type == "error":
                log("error", action.get("message", "Erreur inconnue"))
                return {"success": False, "message": action.get("message"), "steps": steps_log}

            elif action_type == "navigate":
                browser.navigate(action["url"])

            elif action_type == "click":
                browser.click(action["x"], action["y"])

            elif action_type == "type":
                browser.type_text(action["text"])

            elif action_type == "scroll":
                browser.scroll(action.get("direction", "down"), action.get("amount", 300))

            elif action_type == "wait":
                import time
                time.sleep(action.get("seconds", 2))

            elif action_type == "screenshot":
                pass  # Le screenshot sera pris au prochain tour

        log("error", "Nombre maximum d'étapes atteint")
        return {"success": False, "message": "Trop d'étapes, tâche abandonnée", "steps": steps_log}

    except Exception as e:
        log("error", str(e))
        return {"success": False, "message": str(e), "steps": steps_log}

    finally:
        browser.stop()
