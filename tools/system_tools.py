import os
import subprocess
import time
from pathlib import Path

import pyautogui
import pygetwindow as gw


pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.15


APP_REGISTRY = {
    "notepad": "notepad.exe",
    "bloc-notes": "notepad.exe",
    "calculator": "calc.exe",
    "calculatrice": "calc.exe",
    "explorer": "explorer.exe",
    "fichiers": "explorer.exe",
}


def normalize_text(text: str) -> str:
    return text.strip().lower()


def open_notepad() -> str:
    subprocess.Popen(["notepad.exe"])
    return "Bien, Monsieur. Le Bloc-notes est ouvert."


def open_calculator() -> str:
    subprocess.Popen(["calc.exe"])
    return "Bien, Monsieur. La calculatrice est ouverte."


def open_folder(path: str) -> str:
    if not os.path.exists(path):
        return f"Je suis navré, Monsieur. Le dossier demandé est introuvable : {path}"

    subprocess.Popen(["explorer", path])
    return f"Très bien, Monsieur. J'ouvre le dossier : {path}"


def find_folder_by_name(folder_name: str) -> str | None:
    folder_name = normalize_text(folder_name)

    home = Path.home()
    search_roots = [
        home / "Desktop",
        home / "Documents",
        home / "Downloads",
        home / "Pictures",
        home / "Music",
        home / "Videos",
        home,
    ]

    for root in search_roots:
        if root.exists() and root.is_dir() and root.name.lower() == folder_name:
            return str(root)

    for root in search_roots:
        if not root.exists():
            continue

        try:
            for current_root, dirs, _ in os.walk(root):
                for directory in dirs:
                    if directory.lower() == folder_name:
                        return os.path.join(current_root, directory)
        except PermissionError:
            continue
        except Exception:
            continue

    return None


def open_folder_by_name(folder_name: str) -> str:
    special_folders = {
        "bureau": str(Path.home() / "Desktop"),
        "desktop": str(Path.home() / "Desktop"),
        "documents": str(Path.home() / "Documents"),
        "document": str(Path.home() / "Documents"),
        "downloads": str(Path.home() / "Downloads"),
        "téléchargements": str(Path.home() / "Downloads"),
        "telechargements": str(Path.home() / "Downloads"),
        "images": str(Path.home() / "Pictures"),
        "photos": str(Path.home() / "Pictures"),
        "musique": str(Path.home() / "Music"),
        "music": str(Path.home() / "Music"),
        "vidéos": str(Path.home() / "Videos"),
        "videos": str(Path.home() / "Videos"),
    }

    normalized_name = normalize_text(folder_name)

    if normalized_name in special_folders:
        return open_folder(special_folders[normalized_name])

    found_path = find_folder_by_name(folder_name)

    if found_path is None:
        return (
            f"Je suis navré, Monsieur. "
            f"Je n'ai trouvé aucun dossier nommé '{folder_name}'."
        )

    return open_folder(found_path)


def _possible_app_search_roots() -> list[Path]:
    home = Path.home()

    roots = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
        home / "AppData" / "Local" / "Programs",
        home / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        Path(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"),
        home / "Desktop",
    ]

    return [root for root in roots if root.exists()]


def _find_app_candidates(app_name: str) -> list[Path]:
    normalized = normalize_text(app_name)
    candidates: list[Path] = []

    keywords = [normalized]
    if normalized.endswith(".exe"):
        keywords.append(normalized[:-4])

    for root in _possible_app_search_roots():
        try:
            for current_root, _, files in os.walk(root):
                for file_name in files:
                    lower_name = file_name.lower()

                    # .exe ou raccourcis du menu démarrer / bureau
                    if not (lower_name.endswith(".exe") or lower_name.endswith(".lnk")):
                        continue

                    if any(keyword in lower_name for keyword in keywords):
                        candidates.append(Path(current_root) / file_name)
        except PermissionError:
            continue
        except Exception:
            continue

    return candidates


def _score_candidate(candidate: Path, app_name: str) -> int:
    score = 0
    normalized_app = normalize_text(app_name)
    name = candidate.name.lower()
    full_path = str(candidate).lower()

    if name == f"{normalized_app}.exe" or name == f"{normalized_app}.lnk":
        score += 100

    if normalized_app in name:
        score += 40

    if "start menu" in full_path:
        score += 20

    if "desktop" in full_path:
        score += 10

    if candidate.suffix.lower() == ".exe":
        score += 15

    return score


def _launch_path(path: Path) -> None:
    suffix = path.suffix.lower()

    if suffix == ".lnk":
        os.startfile(str(path))
        return

    if suffix == ".exe":
        subprocess.Popen([str(path)])
        return

    os.startfile(str(path))


def open_app(app_name: str) -> str:
    normalized = normalize_text(app_name)

    # 1) Liste connue rapide
    if normalized in APP_REGISTRY:
        command = APP_REGISTRY[normalized]
        try:
            subprocess.Popen([command])
            return f"Très bien, Monsieur. J'ouvre {app_name}."
        except Exception as e:
            return f"Je suis navré, Monsieur. Une erreur est survenue : {e}"

    # 2) Recherche automatique
    candidates = _find_app_candidates(app_name)

    if not candidates:
        return (
            f"Je suis navré, Monsieur. "
            f"Je n'ai trouvé aucune application correspondant à '{app_name}'."
        )

    candidates.sort(key=lambda p: _score_candidate(p, app_name), reverse=True)
    best_candidate = candidates[0]

    try:
        _launch_path(best_candidate)
        return f"Très bien, Monsieur. J'ouvre {best_candidate.stem}."
    except Exception as e:
        return (
            f"Je suis navré, Monsieur. "
            f"J'ai trouvé une application possible, mais son ouverture a échoué : {e}"
        )


def type_text(text: str, interval: float = 0.03) -> str:
    pyautogui.write(text, interval=interval)
    return "Très bien, Monsieur. Le texte a été saisi."


def press_key(key: str) -> str:
    pyautogui.press(key)
    return f"Très bien, Monsieur. J'ai appuyé sur la touche '{key}'."


def hotkey(keys: list[str]) -> str:
    if not keys:
        return "Je suis navré, Monsieur. Aucune touche n'a été fournie."

    pyautogui.hotkey(*keys)
    return f"Très bien, Monsieur. J'ai exécuté le raccourci : {' + '.join(keys)}."


def click_mouse(button: str = "left", clicks: int = 1) -> str:
    pyautogui.click(button=button, clicks=clicks)
    return "Très bien, Monsieur. Clic exécuté."


def move_mouse(x: int, y: int, duration: float = 0.2) -> str:
    pyautogui.moveTo(x, y, duration=duration)
    return f"Très bien, Monsieur. J'ai déplacé la souris en ({x}, {y})."


def fullscreen_active_window() -> str:
    pyautogui.press("f11")
    return "Très bien, Monsieur. J'ai basculé la fenêtre active en plein écran."


def focus_window_by_title(title: str) -> str:
    windows = gw.getWindowsWithTitle(title)

    if not windows:
        return (
            f"Je suis navré, Monsieur. "
            f"Aucune fenêtre correspondant à '{title}' n'a été trouvée."
        )

    target = windows[0]

    try:
        if target.isMinimized:
            target.restore()

        target.activate()
        time.sleep(0.2)
        return f"Très bien, Monsieur. La fenêtre '{target.title}' est désormais au premier plan."
    except Exception as e:
        return f"Je suis navré, Monsieur. Impossible de focaliser la fenêtre : {e}"