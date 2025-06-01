import os
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import time
import sqlite3
import hashlib
import re


MAX_TRIES = 6

class HangmanGame:
    def __init__(self, root):
        """
        Inicjalizuje grę i ustawia wartości domyślne, np. tryb gry, liczba graczy, słowo do zgadnięcia, historia, itp.

        Args:
            root (tkinter): instancja tk.Tk() — główne okno aplikacji.
        """
        self.root = root
        self.root.title("Hangman Game")
        self.root.geometry("500x600")
        self.mode = None
        self.players = 1
        self.score = 0
        self.scores = []
        self.active_players = []
        self.time_limit = 0
        self.end_time = 0
        self.timer_label = None
        self.timer_running = False
        self.current_player = 0
        self.word = ""
        self.guessed = set()
        self.tries = MAX_TRIES
        self.canvas = None
        self.score_label = None
        self.username = ""
        self.player_names = []
        self.history = []
        self.current_category = ""

        self.connU = sqlite3.connect('users.db')
        self.connW = sqlite3.connect('words.db')
        self.create_user_table()
        self.create_word_table()
        self.show_login_window()

    def create_word_table(self):
        """
        Tworzy tablicę słów.
        """
        cursor = self.connW.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL
            )
        """)
        self.connW.commit()

    def create_user_table(self):
        """
        Tworzy tablicę użytkowników.
        """
        cursor = self.connU.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        ''')
        self.connU.commit()

    def show_login_window(self):
        """
        Pokazuje okno logowania.
        """
        self.clear_window()
        tk.Label(self.root, text="Login to Hangman", font=("Helvetica", 20)).pack(pady=20)

        tk.Label(self.root, text="Username").pack()
        self.login_username_entry = tk.Entry(self.root)
        self.login_username_entry.pack(pady=5)

        tk.Label(self.root, text="Password").pack()
        self.login_password_entry = tk.Entry(self.root, show="*")
        self.login_password_entry.pack(pady=5)

        tk.Button(self.root, text="Login", command=self.login_user).pack(pady=10)
        tk.Button(self.root, text="Register", command=self.show_register_window).pack()

    def login_user(self):
        """
        System logowania.
        """
        username = self.login_username_entry.get().strip()
        password = self.login_password_entry.get().strip()

        if not username or not password:
            messagebox.showwarning("Input error", "Please enter username and password.")
            return

        cursor = self.connU.cursor()
        cursor.execute("SELECT password FROM users WHERE username=?", (username,))
        row = cursor.fetchone()

        if row and row[0] == self.hash_password(password):
            self.username = username
            messagebox.showinfo("Success", f"Welcome, {username}!")
            self.setup_menu()
        else:
            messagebox.showerror("Error", "Invalid username or password.")

    def show_register_window(self):
        """
        Okno rejestracji.
        """
        self.clear_window()
        tk.Label(self.root, text="Register New User", font=("Helvetica", 20)).pack(pady=20)

        tk.Label(self.root, text="Username").pack()
        self.reg_username_entry = tk.Entry(self.root)
        self.reg_username_entry.pack(pady=5)

        tk.Label(self.root, text="Password").pack()
        self.reg_password_entry = tk.Entry(self.root, show="*")
        self.reg_password_entry.pack(pady=5)

        tk.Label(self.root, text="Confirm Password").pack()
        self.reg_confirm_password_entry = tk.Entry(self.root, show="*")
        self.reg_confirm_password_entry.pack(pady=5)

        tk.Button(self.root, text="Register", command=self.register_user).pack(pady=10)
        tk.Button(self.root, text="Back to Login", command=self.show_login_window).pack()

    def register_user(self):
        """
        System rejestracji.
        """
        username = self.reg_username_entry.get().strip()
        password = self.reg_password_entry.get().strip()
        confirm_password = self.reg_confirm_password_entry.get().strip()

        if not username or not password or not confirm_password:
            messagebox.showwarning("Input error", "Please fill all fields.")
            return

        if password != confirm_password:
            messagebox.showwarning("Input error", "Passwords do not match.")
            return

        brainfart = self.validate_password(password)
        if not brainfart:
            messagebox.showwarning(
                "Invalid Password",
                "Password must be at least 8 characters long, contain uppercase and lowercase letters, and at least one number."
            )
            return

        cursor = self.connU.cursor()
        cursor.execute("SELECT username FROM users WHERE username=?", (username,))
        if cursor.fetchone():
            messagebox.showerror("Error", "Username already exists.")
            return

        hashed = self.hash_password(password)
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        self.connU.commit()
        messagebox.showinfo("Success", "Registration successful! Please log in.")
        self.show_login_window()

    def hash_password(self, password):
        """
        Haszuje hasła.

        Returns:
            str: zhaszowane hasło
        """
        return hashlib.sha256(password.encode()).hexdigest()


    def validate_password(self, password):
        """
        Walidacja hasła według warunków - 1 litera duża, 1 litera mała, 1 liczba, nie krótsze niż 5.

        Args:
            passwords (str): hasło.

        Returns:
            bool: True/False.
        """
        if len(password) < 5 :
            return False
        if not re.search(r"[A-Z]", password):
            return False
        if not re.search(r"[a-z]", password):
            return False
        if not re.search(r"\d", password):
            return False
        else: return True


    def setup_menu(self):
        """
        Tworzy główne menu gry (tryby gry, import słów, historia, zakończenie).
        """
        self.clear_window()
        tk.Label(self.root, text="Hangman Game", font=("Helvetica", 20)).pack(pady=10)
        if self.username:
            tk.Label(self.root, text=f"Logged in as: {self.username}", font=("Helvetica", 12), fg="blue").pack(pady=5)
        else:
            tk.Label(self.root, text="Not logged in", font=("Helvetica", 12), fg="red").pack(pady=5)
        tk.Button(self.root, text="Singleplayer", width=25, height=2, command=self.singleplayer_menu).pack(pady=5)
        tk.Button(self.root, text="Multiplayer", width=25, height=2, command=self.multiplayer_menu).pack(pady=5)
        tk.Button(self.root, text="Import words from file", width=25, height=2, command=self.import_words).pack(pady=5)
        tk.Button(self.root, text="View session history", width=25, height=2, command=self.show_history_window).pack(pady=5)
        tk.Button(self.root, text="Export session history", width=25, height=2, command=self.export_history).pack(pady=5)
        tk.Button(self.root, text="Exit", width=25, height=2, command=self.root.quit).pack(pady=5)

    def import_words(self):
        """
        Wczytywanie słów wraz z kategoriami do bazy danych z pliku txt.
        """
        file_path = filedialog.askopenfilename(title="Select Word List File", filetypes=[("Text files", "*.txt")])
        if file_path:
            try:
                cursor = self.connW.cursor()
                with open(file_path, 'r', encoding='utf-8') as file:
                    added = 0
                    for line in file:
                        parts = line.strip().split(';')
                        if len(parts) != 2:
                            continue
                        word, category = parts[0].strip().lower(), parts[1].strip().capitalize()
                        if word.isalpha():
                            try:
                                cursor.execute("INSERT INTO words (text, category) VALUES (?, ?)", (word, category))
                                added += 1
                            except sqlite3.IntegrityError:
                                continue
                self.connW.commit()
                messagebox.showinfo("Success", f"Added {added} new words with categories.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load words: {e}")

    def singleplayer_menu(self):
        """
        Wyświetla menu wyboru trybu singleplayer (czasowy / normalny).
        """
        self.clear_window()
        tk.Label(self.root, text="Singleplayer Mode", font=("Helvetica", 16)).pack(pady=10)
        tk.Button(self.root, text="Timed", width=20, height=2, command=lambda: self.start_singleplayer(True)).pack(pady=5)
        tk.Button(self.root, text="Normal", width=20, height=2, command=lambda: self.start_singleplayer(False)).pack(pady=5)
        tk.Button(self.root, text="Back", width=20, height=2, command=self.setup_menu).pack(pady=5)

    def multiplayer_menu(self):
        """
        Pozwala ustawić liczbę graczy i ich imiona, przygotowuje grę multiplayer przy zalożeniu ze pierwszy gracz jest tym, na którego koncie jesteśmy zalogowani.
        """
        self.players = simpledialog.askinteger("Multiplayer", "Enter number of players (2+):", minvalue=2)
        if not self.players:
            return
        self.player_names = []
        for i in range(self.players):
            if i == 0:
                self.player_names.append(self.username)
            else:
                name = simpledialog.askstring("Player Name", f"Enter name for Player {i + 1}:")
                self.player_names.append(name if name else f"Player {i + 1}")
        self.scores = [0] * self.players
        self.active_players = [True] * self.players
        self.current_player = -1
        self.start_multiplayer()

    def start_singleplayer(self, timed):
        """
        Rozpoczyna grę singleplayer; ustawia tryb normalny lub czasowy.

        Args:
            timed (bool): Czy gra jest w trybie czasowym (TRUE) czy normalnym (FALSE).
        """
        if not self.username:
            messagebox.showerror("Error", "You must be logged in to play.")
            self.show_login_window()
            return

        self.mode = 'timed' if timed else 'normal'
        self.score = 0
        if timed:
            self.time_limit = simpledialog.askinteger("Timed Mode", "Enter time limit (seconds):", minvalue=10)
            if not self.time_limit:
                return
            self.end_time = time.time() + self.time_limit
            self.timer_running = True
            self.next_word_timed()
        else:
            self.next_word()


    def start_multiplayer(self):
        """
        Rozpoczyna grę lub turę dla następnego gracza w trybie multiplayer.
        """
        if all(not active for active in self.active_players):
            self.show_multiplayer_scores()
            return

        start_index = self.current_player
        while True:
            self.current_player = (self.current_player + 1) % self.players
            if self.active_players[self.current_player]:
                break
            if self.current_player == start_index:
                self.show_multiplayer_scores()
                return

        self.mode = 'multiplayer'
        self.word = self.get_random_word()
        self.guessed = set()
        self.tries = MAX_TRIES
        self.display_game(f"{self.player_names[self.current_player]}'s Turn")

    def export_history(self):
        """
        Eksportuje historię gier do pliku .txt, którego nazwę samemu podajemy.
        """
        if not self.history:
            messagebox.showinfo("Export History", "No history to export.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Text files", "*.txt")],
                                                 title="Save History As")
        if not file_path:
            return
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write("\n".join(self.history))
            messagebox.showinfo("Success", f"History saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save history:\n{e}")

    def show_history_window(self):
        """
        Pokazuje nowe okno z historią rozegranych gier.
        """
        if not self.history:
            messagebox.showinfo("History", "No history to show.")
            return
        history_window = tk.Toplevel(self.root)
        history_window.title("Game History")
        history_window.geometry("500x500")
        tk.Label(history_window, text="Game History", font=("Helvetica", 16)).pack(pady=10)
        text_area = tk.Text(history_window, wrap=tk.WORD, font=("Courier", 10))
        text_area.pack(expand=True, fill='both', padx=10, pady=10)
        scrollbar = tk.Scrollbar(text_area)
        scrollbar.pack(side='right', fill='y')
        text_area.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=text_area.yview)
        text_area.insert(tk.END, "\n".join(self.history))
        text_area.config(state=tk.DISABLED)
        tk.Button(history_window, text="Close", command=history_window.destroy).pack(pady=5)

    def display_game(self, title):
        """
        Wyświetla główny ekran gry (pole do wpisu liter, wisielec, słowo).
        Args:
            title (str): Tytuł wyświetlany nad grą
        """
        self.clear_window()
        tk.Label(self.root, text=title, font=("Helvetica", 16)).pack(pady=10)
        if self.mode == 'timed':
            self.timer_label = tk.Label(self.root, text="", font=("Helvetica", 12))
            self.timer_label.pack()
            self.category_label = tk.Label(self.root, text=f"Category: {self.current_category}", font=("Helvetica", 12),
                                           fg="gray")
            self.category_label.pack(pady=5)
            self.update_timer()

        self.canvas = tk.Canvas(self.root, width=180, height=230, bg="white")
        self.canvas.pack(pady=10)
        self.word_label = tk.Label(self.root, text=self.get_display_word(), font=("Courier", 20))
        self.word_label.pack(pady=10)
        self.entry = tk.Entry(self.root)
        self.entry.pack(pady=5)
        self.entry.bind("<Return>", self.make_guess)
        self.status_label = tk.Label(self.root, text=f"Tries left: {self.tries}", font=("Helvetica", 12))
        self.status_label.pack(pady=5)
        self.score_label = tk.Label(self.root, text=f"Score: {self.score}" if self.mode != 'multiplayer' else f"{self.player_names[self.current_player]}'s Score: {self.scores[self.current_player]}", font=("Helvetica", 12))
        self.score_label.pack(pady=5)
        self.draw_hangman()

    def update_timer(self):
        """
        Aktualizuje licznik czasu i kończy grę po upływie limitu.
        """
        if self.mode != 'timed' or not self.timer_running:
            return
        remaining = int(self.end_time - time.time())
        if remaining <= 0:
            self.timer_label.config(text="Time left: 0")
            self.timer_running = False
            messagebox.showinfo("Time's Up", f"Your score: {self.score}")
            self.history.append(f"Mode: Singleplayer (Timed, {self.time_limit}s) | Player: {self.username} | Score: {self.score}")
            self.setup_menu()
        else:
            self.timer_label.config(text=f"Time left: {remaining}")
            self.root.after(1000, self.update_timer)

    def next_word(self):
        """
        Losuje nowe słowo i resetuje licznik prób w trybie normalnym singleplayer.
        """
        self.word = self.get_random_word()
        self.guessed = set()
        self.tries = MAX_TRIES
        self.display_game("Singleplayer - Normal Mode")

    def next_word_timed(self):
        """
        Losuje nowe słowo i resetuje licznik prób w trybie czasowym singleplayer.
        """
        self.word = self.get_random_word()
        self.guessed = set()
        self.tries = MAX_TRIES
        self.display_game("Singleplayer - Timed Mode")


    def get_display_word(self):
        """
        Zwraca wersję słowa z podkreśleniami dla niezgadniętych liter.
        Returns:
            str: np. "x _ x x _ x _ _"
        """
        return ' '.join([letter if letter in self.guessed else '_' for letter in self.word])

    def make_guess(self, event):
        """
        Przetwarza literę wpisaną przez gracza, aktualizuje stan gry.
        Args:
            event: obiekt zdarzenia tkinter, przekazywany automatycznie po naciśnięciu Enter.
        """
        guess = self.entry.get().lower()
        self.entry.delete(0, tk.END)
        if not guess.isalpha() or len(guess) != 1 or guess in self.guessed:
            return
        self.guessed.add(guess)
        if guess not in self.word:
            self.tries -= 1
        self.word_label.config(text=self.get_display_word())
        self.status_label.config(text=f"Tries left: {self.tries}")
        self.draw_hangman()

        if self.mode == 'timed' and self.tries == 0:
            self.timer_running = False
            messagebox.showinfo("Fail", f"You lost! The word was: {self.word}\nYour score: {self.score}")
            self.history.append(f"Mode: Singleplayer (Timed, {self.time_limit}s) | Player: {self.username} | Score: {self.score}")
            self.setup_menu()
            return

        if all(letter in self.guessed for letter in self.word):
            self.after_round(True)
        elif self.tries == 0:
            messagebox.showinfo("Fail", f"You lost! The word was: {self.word}")
            self.after_round(False)

    def draw_hangman(self):
        """
        Rysuje aktualny stan wisielca na Canvas.
        """
        if not self.canvas:
            return
        self.canvas.delete("all")
        self.canvas.create_line(20, 230, 160, 230)
        self.canvas.create_line(40, 230, 40, 20)
        self.canvas.create_line(40, 20, 110, 20)
        self.canvas.create_line(110, 20, 110, 40)
        parts = 6 - self.tries
        if parts >= 1: self.canvas.create_oval(90, 40, 130, 80)
        if parts >= 2: self.canvas.create_line(110, 80, 110, 140)
        if parts >= 3: self.canvas.create_line(110, 90, 80, 110)
        if parts >= 4: self.canvas.create_line(110, 90, 140, 110)
        if parts >= 5: self.canvas.create_line(110, 140, 90, 180)
        if parts >= 6: self.canvas.create_line(110, 140, 130, 180)

    def after_round(self, won):
        """
        Obsługuje zakończenie rundy — aktualizuje wynik, przechodzi do kolejnego słowa lub kończy grę.

        Args:
            won (bool): Czy gracz odgadł słowo.
        """
        if self.mode == 'normal':
            if won:
                self.score += 1
                self.next_word()
            else:
                self.history.append(f"Mode: Singleplayer (Normal) | Player: {self.username} | Score: {self.score}")
                messagebox.showinfo("Game Over", f"Your score: {self.score}")
                self.setup_menu()
        elif self.mode == 'timed':
            if won:
                self.score += 1
            self.next_word_timed()
        elif self.mode == 'multiplayer':
            if won:
                self.scores[self.current_player] += self.tries
            else:
                self.active_players[self.current_player] = False
            self.start_multiplayer()

    def show_multiplayer_scores(self):
        """
        Wyświetla końcowe wyniki graczy w trybie multiplayer i zapisuje je do historii.
        """
        scores_text = "\n".join([f"{self.player_names[i]}: {score}" for i, score in enumerate(self.scores)])
        messagebox.showinfo("Final Scores", scores_text)

        score_line = ", ".join([f"{self.player_names[i]}: {score}" for i, score in enumerate(self.scores)])
        self.history.append(f"Mode: Multiplayer | {score_line}")

        self.setup_menu()

    def get_random_word(self):
        """
        Dobiera losowe słowa z bazy danych.

        Returns:
            str: słowo z bazy.
        """
        cursor = self.connW.cursor()
        cursor.execute("SELECT text, category FROM words ORDER BY RANDOM() LIMIT 1")
        row = cursor.fetchone()
        if row:
            self.current_category = row[1]
            return row[0]
        else:
            self.current_category = "Unknown"
            return "juanpablo"

    def clear_window(self):
        """
        Czyści zawartość głównego okna (self.root).
        """
        for widget in self.root.winfo_children():
            widget.destroy()

    def on_close(self):
        """
        Zamykanie połączeń i usunięcie words.db.
        """
        self.connU.close()
        self.connW.close()
        if os.path.exists("words.db"):
            os.remove("words.db")
            print("words.db deleted.")
        root.destroy()



if __name__ == '__main__':
    root = tk.Tk()
    app = HangmanGame(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
