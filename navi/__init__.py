import curses
import json
import os
import subprocess
from pathlib import Path

try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _version

    __version__ = _version("navi")
except PackageNotFoundError:
    try:
        from setuptools_scm import get_version

        __version__ = get_version(root=".", relative_to=__file__)
    except Exception:
        __version__ = "0.0.0-dev"


class Launcher:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.user_input = ""
        self.apps = self._get_apps()
        self.filtered_apps = self.apps
        self.selection_index = 0
        self.usage_path = Path.home() / ".config/launchy/usage.json"
        self.usage_data = self._load_usage()

    def _get_apps(self):
        apps = []
        app_names = set()

        xdg_data_dirs = os.environ["XDG_DATA_DIRS"].split(":")
        app_dirs = [os.path.join(d, "applications") for d in xdg_data_dirs if d]

        for app_dir in app_dirs:
            if not os.path.isdir(app_dir):
                continue
            for root, _, filenames in os.walk(app_dir):
                for filename in filenames:
                    if filename.endswith(".desktop"):
                        with open(os.path.join(root, filename), "r") as f:
                            current_section = None
                            app_info = {}
                            nodisplay = False
                            for line in f:
                                line = line.strip()
                                if not line or line.startswith("#"):
                                    continue
                                if line.startswith("[") and line.endswith("]"):
                                    current_section = line[1:-1].strip()
                                    continue
                                # Only parse the main Desktop Entry section
                                if current_section != "Desktop Entry":
                                    continue
                                if "=" in line:
                                    key, value = line.split("=", 1)
                                    key = key.strip()
                                    value = value.strip()
                                    if key == "Name":
                                        app_info["name"] = value
                                    elif key == "Exec":
                                        app_info["exec"] = value
                                    elif key == "NoDisplay":
                                        nodisplay = value.lower() == "true"
                            # Add app only if valid and not duplicate
                            if (
                                not nodisplay
                                and "name" in app_info
                                and "exec" in app_info
                                and app_info["name"] not in app_names
                            ):
                                apps.append(app_info)
                                app_names.add(app_info["name"])

        return apps

    def _load_usage(self):
        if self.usage_path.exists():
            with open(self.usage_path, "r") as f:
                return json.load(f)
        return {}

    def _save_usage(self):
        self.usage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.usage_path, "w") as f:
            json.dump(self.usage_data, f)

    def _increment_usage(self, app_name):
        self.usage_data[app_name] = self.usage_data.get(app_name, 0) + 1
        self._save_usage()

    def fuzzy_match(self, query, text):
        score = 0
        match_indices = []
        query_index = 0
        text_index = 0
        while query_index < len(query) and text_index < len(text):
            if query[query_index].lower() == text[text_index].lower():
                score += 1
                if match_indices and match_indices[-1] == text_index - 1:
                    score += 1  # Bonus for consecutive matches
                match_indices.append(text_index)
                query_index += 1
            text_index += 1

        if query_index == len(query):
            return score, match_indices
        else:
            return 0, []

    def run(self):
        curses.curs_set(1)
        curses.start_color()
        curses.use_default_colors()
        curses.set_escdelay(25)
        curses.init_pair(1, 7, -1) # white on cattpuccin
        curses.init_pair(2, 4, -1) # pastel blue ..
        curses.init_pair(3, 6, -1) # teal / greenish-blue ..

        while True:
            self.draw()
            self.handle_input()

    def _get_apps_sorted_by_usage(self):
        return sorted(
            self.apps,
            key=lambda app: self.usage_data.get(
                app["name"], 0
            ),  # default 0 if not in usage_data
            reverse=True,
        )

    def draw(self):
        self.stdscr.clear()
        n_rows, n_cols = self.stdscr.getmaxyx()
        self.stdscr.addstr(0, 0, f"> {self.user_input}", curses.color_pair(1))


        if self.user_input:
            self.filtered_apps = []
            for app in self.apps:
                score, indices = self.fuzzy_match(self.user_input, app["name"])
                if score > 0:
                    self.filtered_apps.append((app, score, indices))
            self.filtered_apps.sort(key=lambda x: x[1], reverse=True)
            self.filtered_apps = [app for app, score, indices in self.filtered_apps]
        else:
            self.filtered_apps = self._get_apps_sorted_by_usage()

        for i, app in enumerate(self.filtered_apps[:n_rows]):
            is_selected = i == self.selection_index
            color = curses.color_pair(2) if is_selected else curses.color_pair(1)
            self.stdscr.addstr(i + 1, 0, "", color)
            score, indices = self.fuzzy_match(self.user_input, app["name"])
            for j, char in enumerate(app["name"]):
                if j in indices:
                    self.stdscr.addstr(char, curses.color_pair(3) | curses.A_BOLD)
                else:
                    self.stdscr.addstr(char, color)
        self.stdscr.move(0, len(self.user_input) + 2)
        self.stdscr.refresh()

    def handle_input(self):
        try:
            ch = self.stdscr.getch()
        except curses.error:
            return

        key = curses.keyname(ch).decode("utf-8")

        if key == "^[":
            exit()
        elif ch == curses.KEY_BACKSPACE or key == "^H":
            self.user_input = self.user_input[:-1]
            self.selection_index = 0
        elif key == "^J":
            if self.filtered_apps:
                selected_app = self.filtered_apps[self.selection_index]
                self._increment_usage(selected_app["name"])
                command = selected_app["exec"].split(" ")[0]
                subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                    close_fds=True
                )
                exit()
        elif ch == curses.KEY_UP or key == "^P":
            self.selection_index = max(0, self.selection_index - 1)
        elif ch == curses.KEY_DOWN or key == "^N":
            if self.filtered_apps:
                self.selection_index = min(
                    len(self.filtered_apps) - 1, self.selection_index + 1
                )
        elif len(key) == 1 and key.isprintable():
            self.user_input += key
            self.selection_index = 0


def _main(stdscr):
    launcher = Launcher(stdscr)
    launcher.run()


def main():
    try:
        curses.wrapper(_main)
    except KeyboardInterrupt: 
        exit()


if __name__ == "__main__":
    main()
