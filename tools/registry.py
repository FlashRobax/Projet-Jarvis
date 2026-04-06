from tools.system_tools import (
    click_mouse,
    focus_window_by_title,
    fullscreen_active_window,
    hotkey,
    move_mouse,
    open_app,
    open_calculator,
    open_folder_by_name,
    open_notepad,
    press_key,
    type_text,
)


TOOLS = {
    "open_notepad": {
        "function": open_notepad,
        "description": "Ouvre le Bloc-notes Windows.",
        "parameters": {}
    },

    "open_calculator": {
        "function": open_calculator,
        "description": "Ouvre la calculatrice Windows.",
        "parameters": {}
    },

    "open_folder_by_name": {
        "function": open_folder_by_name,
        "description": (
            "Ouvre un dossier en le recherchant par son nom. "
            "Exemples : Documents, Bureau, Downloads, JARVIS, etc."
        ),
        "parameters": {
            "folder_name": "Nom du dossier à ouvrir"
        }
    },

    "open_app": {
        "function": open_app,
        "description": (
            "Ouvre une application enregistrée dans la liste interne. "
            "Exemples : chrome, discord, vscode, calculatrice, bloc-notes."
        ),
        "parameters": {
            "app_name": "Nom de l'application à ouvrir"
        }
    },

    "type_text": {
        "function": type_text,
        "description": (
            "Tape du texte avec le clavier dans la fenêtre active."
        ),
        "parameters": {
            "text": "Texte à taper"
        }
    },

    "press_key": {
        "function": press_key,
        "description": "Appuie sur une touche simple du clavier.",
        "parameters": {
            "key": "Nom de la touche, ex: enter, esc, tab, f11"
        }
    },

    "hotkey": {
        "function": hotkey,
        "description": (
            "Exécute un raccourci clavier avec plusieurs touches. "
            "Exemples : ctrl+s, alt+tab, win+d."
        ),
        "parameters": {
            "keys": ["Liste des touches à presser ensemble"]
        }
    },

    "click_mouse": {
        "function": click_mouse,
        "description": "Effectue un clic souris à la position actuelle.",
        "parameters": {
            "button": "left ou right",
            "clicks": "Nombre de clics"
        }
    },

    "move_mouse": {
        "function": move_mouse,
        "description": "Déplace la souris à une position précise de l'écran.",
        "parameters": {
            "x": "Coordonnée X",
            "y": "Coordonnée Y",
            "duration": "Durée du déplacement en secondes"
        }
    },

    "fullscreen_active_window": {
        "function": fullscreen_active_window,
        "description": (
            "Bascule la fenêtre active en plein écran, généralement avec F11."
        ),
        "parameters": {}
    },

    "focus_window_by_title": {
        "function": focus_window_by_title,
        "description": (
            "Met au premier plan une fenêtre en recherchant un morceau de son titre."
        ),
        "parameters": {
            "title": "Titre ou partie du titre de la fenêtre"
        }
    },

    "shutdown": {
        "function": None,
        "description": "Éteint Jarvis.",
        "parameters": {}
    }
}