# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
import json
import vlc
import os
from pathlib import Path

# --- ΡΥΘΜΙΣΗ PATHS ---
config_dir = Path.home() / ".config" / "troikas-radio"
config_dir.mkdir(parents=True, exist_ok=True)
json_file = os.path.join(str(config_dir), "radio_stations.json")

# --- ΧΡΩΜΑΤΑ & ΓΡΑΜΜΑΤΟΣΕΙΡΑ ---
BG_COLOR = "#1a1a1a"   
CARD_COLOR = "#262626"   
FG_TEXT = "#eeeeee"   
ACCENT_COLOR = "#4cd137"    
EDIT_C = "#fbc531"          
DEL_C  = "#e84118"          
STATUS_BG = "#0a0a0a"       
MAIN_FONT = "Ubuntu"

class RadioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TROiKAS Radio")
        self.root.geometry("550x750")
        self.root.configure(bg=BG_COLOR)

        self.current_playing_index = None 
        
        self.instance = vlc.Instance('--no-video --quiet --no-xlib')
        self.player = self.instance.media_player_new()
        
        self.stations = self.load_data()
        self.setup_ui()

    def load_data(self):
        if not os.path.exists(json_file): return []
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("radio_stations", [])
        except: return []

    def setup_ui(self):
        # Τίτλος
        tk.Label(self.root, text="TROiKAS RADIO", font=(MAIN_FONT, 24, "bold"), 
                 bg=BG_COLOR, fg=ACCENT_COLOR).pack(pady=20)
        
        # Κουμπί Προσθήκης
        tk.Button(self.root, text="+ ADD STATION", command=self.open_add, 
                  bg=ACCENT_COLOR, fg="black", font=(MAIN_FONT, 10, "bold"),
                  padx=15, pady=5, bd=0, cursor="hand2").pack(pady=10)

        # --- SCROLLABLE FRAME (ΧΩΡΙΣ ΟΡΑΤΗ ΜΠΑΡΑ) ---
        self.canvas = tk.Canvas(self.root, bg=BG_COLOR, highlightthickness=0)
        # Δημιουργούμε το scrollbar αλλά ΔΕΝ το κάνουμε .pack() - έτσι μένει κρυφό
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg=BG_COLOR)

        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # Επιτρέπουμε το σκρολάρισμα με τη ροδέλα του ποντικιού
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))

        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw", width=530)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        # --- STATUS BAR ---
        self.status_frame = tk.Frame(self.root, bg=STATUS_BG, height=60)
        self.status_frame.pack(side="bottom", fill="x")
        
        self.status_label = tk.Label(self.status_frame, text="READY", 
                                     font=(MAIN_FONT, 10, "bold"),
                                     bg=STATUS_BG, fg="#666", pady=15)
        self.status_label.pack()

        self.render_stations()

    def render_stations(self):
        for w in self.scroll_frame.winfo_children(): w.destroy()
        self.play_buttons = {} 

        for i, s in enumerate(self.stations):
            f = tk.Frame(self.scroll_frame, bg=CARD_COLOR, pady=12, padx=15)
            f.pack(fill="x", pady=4, padx=10)

            # PLAY/STOP Button
            is_playing = (self.current_playing_index == i)
            btn_text = "STOP" if is_playing else "PLAY"
            btn_fg = DEL_C if is_playing else ACCENT_COLOR
            
            btn = tk.Button(f, text=btn_text, font=(MAIN_FONT, 8, "bold"), bg="#333", fg=btn_fg, 
                            bd=0, padx=10, pady=5, width=6)
            self.play_buttons[i] = btn
            btn.configure(command=lambda idx=i, url=s['src']: self.toggle_play(idx, url))
            btn.pack(side="left", padx=(0, 15))

            # Στοιχεία Σταθμού
            tk.Label(f, text=str(s['freq']), font=(MAIN_FONT, 11, "bold"), 
                     bg=CARD_COLOR, fg=ACCENT_COLOR, width=6, anchor="w").pack(side="left")
            tk.Label(f, text=str(s['title']), font=(MAIN_FONT, 11), 
                     bg=CARD_COLOR, fg=FG_TEXT, anchor="w").pack(side="left", fill="x", expand=True)

            # EDIT/DEL
            tk.Button(f, text="EDIT", font=(MAIN_FONT, 8, "bold"), bg="#333", fg=EDIT_C, 
                      command=lambda idx=i: self.open_edit(idx), bd=0, padx=10, pady=5).pack(side="left", padx=2)
            tk.Button(f, text="DEL", font=(MAIN_FONT, 8, "bold"), bg="#333", fg=DEL_C, 
                      command=lambda idx=i: self.delete(idx), bd=0, padx=10, pady=5).pack(side="left", padx=2)

    def toggle_play(self, index, url):
        old_index = self.current_playing_index
        station_name = self.stations[index]['title']
        
        if self.current_playing_index == index:
            self.player.stop()
            self.current_playing_index = None
            self.status_label.configure(text="STATUS: STOPPED", fg=DEL_C)
        else:
            self.player.stop()
            media = self.instance.media_new(url)
            self.player.set_media(media)
            self.player.play()
            self.current_playing_index = index
            self.status_label.configure(text="NOW PLAYING: " + station_name.upper(), fg=ACCENT_COLOR)

        if old_index is not None and old_index in self.play_buttons:
            self.play_buttons[old_index].configure(text="PLAY", fg=ACCENT_COLOR)
        if self.current_playing_index is not None:
            self.play_buttons[self.current_playing_index].configure(text="STOP", fg=DEL_C)

    def open_add(self):
        self.modal_window("Add Station", lambda d: (self.stations.append(d), self.save_data()))

    def open_edit(self, index):
        current = self.stations[index]
        self.modal_window("Edit Station", lambda d: (self.stations.__setitem__(index, d), self.save_data()), current)

    def modal_window(self, title, callback, data=None):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("350x420")
        win.configure(bg=CARD_COLOR) 
        win.transient(self.root) 
        win.grab_set() 

        fields = [("Station Name", "title"), ("Frequency", "freq"), ("Stream URL", "src")]
        entries = {}

        for label, key in fields:
            tk.Label(win, text=label, bg=CARD_COLOR, fg=FG_TEXT, font=(MAIN_FONT, 10)).pack(pady=(15, 2))
            e = tk.Entry(win, bg="#1a1a1a", fg="white", insertbackground="white", 
                         bd=0, font=(MAIN_FONT, 11), highlightthickness=1, highlightbackground="#333")
            if data: e.insert(0, data[key])
            e.pack(pady=5, padx=30, fill="x", ipady=5)
            entries[key] = e

        def on_save():
            new_data = {k: e.get() for k, e in entries.items()}
            callback(new_data)
            win.destroy()

        tk.Button(win, text="SAVE CHANGES", font=(MAIN_FONT, 10, "bold"), 
                  bg=ACCENT_COLOR, fg="black", command=on_save, 
                  bd=0, pady=12, cursor="hand2").pack(pady=30, padx=30, fill="x")

    def delete(self, i):
        if self.current_playing_index == i:
            self.player.stop()
            self.current_playing_index = None
            self.status_label.configure(text="READY", fg="#666")
        self.stations.pop(i)
        self.save_data()

    def save_data(self):
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({"radio_stations": self.stations}, f, indent=4, ensure_ascii=False)
            self.render_stations()
        except Exception as e:
            print("Save Error:", e)

if __name__ == "__main__":
    root = tk.Tk()
    app = RadioApp(root)
    root.mainloop()