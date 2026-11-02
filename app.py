"""Bridge Trimmer: see the stress in a Poly Bridge 3 save and write a cheaper copy."""
import os, sys, glob, threading, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import trimmer

BG, PANEL, LINE, TEXT, DIM, ACC = "#14171f", "#1e222d", "#333a4a", "#eef0f5", "#9aa3b5", "#f2b632"
FONT = "Segoe UI"

def heat(p):
    """green under 50%, through yellow, red at 100%"""
    t = max(0.0, min(1.0, p / 100))
    a, b, f = ((70, 200, 110), (245, 200, 60), t * 2) if t < .5 else ((245, 200, 60), (235, 60, 60), t * 2 - 1)
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * f) for x, y in zip(a, b))

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bridge Trimmer for Poly Bridge 3"); self.geometry("1280x860"); self.minsize(1000, 790); self.configure(bg=BG)
        self.b = None; self.edges = None; self.est = None; self.u = None; self.running = False; self.shot = None; self.shot_img = None
        s = ttk.Style(self); s.theme_use("clam")
        s.configure("TCombobox", background=LINE, arrowcolor=TEXT, bordercolor=LINE)
        s.map("TCombobox", fieldbackground=[("readonly", TEXT)], foreground=[("readonly", BG)], selectbackground=[("readonly", TEXT)], selectforeground=[("readonly", BG)])
        s.configure("Horizontal.TProgressbar", background=ACC, troughcolor=PANEL, bordercolor=PANEL)
        self.option_add("*TCombobox*Listbox.background", TEXT); self.option_add("*TCombobox*Listbox.foreground", BG)
        side = tk.Frame(self, bg=PANEL, width=310); side.pack(side="left", fill="y"); side.pack_propagate(False)
        def lab(t, f=10, c=DIM, p=(12, 3)):
            tk.Label(side, text=t, bg=PANEL, fg=c, font=(FONT, f), anchor="w", justify="left", wraplength=270).pack(fill="x", padx=20, pady=p)
        lab("Bridge Trimmer", 19, TEXT, (20, 0)); lab("Cheaper bridges from your own saves", 10, ACC, (0, 8))
        lab("Level"); self.level = ttk.Combobox(side, state="readonly"); self.level.pack(fill="x", padx=20)
        lab("Save"); self.slot = ttk.Combobox(side, state="readonly"); self.slot.pack(fill="x", padx=20)
        row = tk.Frame(side, bg=PANEL); row.pack(fill="x", padx=20, pady=(9, 0))
        for i, (t, f) in enumerate((("Open save...", self.open_file), ("Screenshot...", self.open_shot))):
            tk.Button(row, text=t, command=f, bg=LINE, fg=TEXT, relief="flat", font=(FONT, 10), cursor="hand2", pady=5, bd=0).pack(side="left", fill="x", expand=True, padx=(0, 6) if i == 0 else 0)
        lab("Stress the game showed (%), optional")
        self.obs = self.entry(side, "")
        lab("Keep stress under (%)"); self.target = self.entry(side, "90")
        self.go = self.btn(side, "Trim this bridge", self.start, True)
        lab("New save name"); self.name = self.entry(side, "Trimmed")
        self.sv = self.btn(side, "Save as new slot", self.save); self.sv.configure(state="disabled")
        self.ab = self.btn(side, "Build a new bridge", self.build)
        lab("New level? In the game, place one road piece and save. Pick that save here, click Build, then save it as a new slot.", 9, DIM, (6, 0))
        self.status = tk.Label(side, text="", bg=PANEL, fg=DIM, font=(FONT, 9), wraplength=270, justify="left", anchor="nw"); self.status.pack(fill="both", expand=True, padx=20, pady=10)
        main = tk.Frame(self, bg=BG); main.pack(side="left", fill="both", expand=True)
        self.head = tk.Label(main, text="Pick a level to begin", bg=BG, fg=TEXT, font=(FONT, 15, "bold"), anchor="w"); self.head.pack(fill="x", padx=20, pady=(18, 0))
        self.sub = tk.Label(main, text="", bg=BG, fg=DIM, font=(FONT, 11), anchor="w"); self.sub.pack(fill="x", padx=20, pady=(2, 8))
        self.cv = tk.Canvas(main, bg=PANEL, highlightthickness=0); self.cv.pack(fill="both", expand=True, padx=20, pady=(0, 18))
        self.cv.bind("<Configure>", lambda e: self.draw())
        self.level.bind("<<ComboboxSelected>>", lambda e: self.fill_slots())
        self.slot.bind("<<ComboboxSelected>>", lambda e: self.pick_slot())
        self.obs.bind("<KeyRelease>", lambda e: self.refresh())
        levels = sorted(os.path.basename(p) for p in glob.glob(trimmer.SAVE_ROOT + "/[0-9][0-9][0-9]") if glob.glob(p + "/*.slot"))
        self.level["values"] = levels
        if not levels: self.status.configure(text="No saves found here. Use Open save.")
        if len(sys.argv) > 1: self.load(sys.argv[1])
        elif levels: self.level.set(levels[-1]); self.fill_slots()

    def btn(self, side, text, cmd, main=False):
        b = tk.Button(side, text=text, command=cmd, bg=ACC if main else LINE, fg=BG if main else TEXT, activebackground="#ffd063",
                      relief="flat", font=(FONT, 11, "bold" if main else "normal"), cursor="hand2", pady=6, bd=0)
        b.pack(fill="x", padx=20, pady=(9, 0)); return b

    def entry(self, side, v):
        e = tk.Entry(side, bg=BG, fg=TEXT, insertbackground=TEXT, relief="flat", font=(FONT, 11), highlightthickness=1, highlightbackground=LINE)
        e.insert(0, v); e.pack(fill="x", padx=20, ipady=4); return e

    def fill_slots(self):
        d = os.path.join(trimmer.SAVE_ROOT, self.level.get())
        names = sorted((os.path.basename(p)[:-5] for p in glob.glob(d + "/*.slot")), key=lambda n: n == "Auto-Save")
        self.slot["values"] = names
        if names: self.slot.set(names[0]); self.pick_slot()

    def pick_slot(self):
        self.load(os.path.join(trimmer.SAVE_ROOT, self.level.get(), self.slot.get() + ".slot"))

    def open_file(self):
        p = filedialog.askopenfilename(initialdir=trimmer.SAVE_ROOT if os.path.isdir(trimmer.SAVE_ROOT) else None, filetypes=[("Poly Bridge 3 save", "*.slot")])
        if p: self.load(p)

    def open_shot(self):
        p = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp")])
        if p:
            self.shot = Image.open(p).convert("RGB"); self.draw()

    def load(self, path):
        try: self.b = trimmer.load(path)
        except Exception as x:
            self.b = None; self.head.configure(text="Couldn't read that save"); self.sub.configure(text=str(x)[:90]); self.cv.delete("all"); return
        self.edges = None; self.est = None; self.sv.configure(state="disabled")
        lvl = self.b["level"]; self.head.configure(text=(f"Level {lvl}  ·  " if lvl else "") + os.path.basename(path)[:-5])
        self.u = trimmer.stress(self.b)
        self.refresh(); self.status.configure(text="\n".join(trimmer.warnings(self.b)), fg=ACC)

    def scale(self):
        try: o = float(self.obs.get())
        except ValueError: return 1.0, False
        return (o / max(self.u), True) if self.u and o > 0 else (1.0, False)

    def refresh(self):
        if self.b is None: return
        b = self.b; t = f"Pieces ${trimmer.cost(b):,.0f}   ·   {len(b['br']['edges'])} pieces"
        if self.u:
            k, cal = self.scale(); t += f"   ·   Stress ~{max(self.u) * k:.0f}%" + ("" if cal else " (uncalibrated)")
        else: t += "   ·   Unstable in the solver"
        if self.edges is not None: t += f"      →   ${trimmer.cost(b, self.edges):,.0f}, ~{self.est:.0f}%"
        self.sub.configure(text=t); self.draw()

    def draw(self):
        c = self.cv; c.delete("all"); W, H = c.winfo_width(), c.winfo_height()
        if self.b is None or W < 50: return
        if self.shot is not None:
            w, h = self.shot.size; f = min((W - 20) / w, (H / 2 - 15) / h)
            self.shot_img = ImageTk.PhotoImage(self.shot.resize((max(1, int(w * f)), max(1, int(h * f)))))
            c.create_image(W / 2, 8, image=self.shot_img, anchor="n"); top, H2 = H / 2, H / 2
        else: top, H2 = 0, H
        b = self.b; edges = b["br"]["edges"] if self.edges is None else self.edges
        u = trimmer.stress(b, edges) if self.edges is not None else self.u
        k = self.scale()[0]
        pts = [b["P"][n] for e in b["br"]["edges"] for n in (e["a"], e["b"])] + list(b["A"].values())
        x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts); y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
        s = min((W - 80) / max(x1 - x0, 1), (H2 - 80) / max(y1 - y0, 1))
        T = lambda p: (W / 2 + (p[0] - (x0 + x1) / 2) * s, top + H2 / 2 - (p[1] - (y0 + y1) / 2) * s)
        for i, e in enumerate(edges):
            c.create_line(*T(b["P"][e["a"]]), *T(b["P"][e["b"]]), fill=heat(u[i] * k) if u else DIM, width=7 if e["mat"] == 1 else 3, capstyle="round")
        used = {n for e in edges for n in (e["a"], e["b"])}
        for n, p in b["J"].items():
            if n in used:
                x, y = T(p); c.create_oval(x - 3, y - 3, x + 3, y + 3, fill=TEXT, outline="")
        for p in b["A"].values():
            x, y = T(p); c.create_rectangle(x - 6, y - 6, x + 6, y + 6, fill="#d23a4e", outline="")

    def start(self):
        if self.running or self.b is None: return
        try:
            target = float(self.target.get()); obs = float(self.obs.get()) if self.obs.get().strip() else None
        except ValueError:
            messagebox.showerror("Bridge Trimmer", "Stress values must be numbers."); return
        self.running = True; self.go.configure(state="disabled", text="Trimming...")
        box = []
        def work():
            try: box.append(trimmer.trim(self.b, target, obs))
            except Exception as x: box.append(x)
        threading.Thread(target=work, daemon=True).start()
        def poll():
            if box: self.done(box[0])
            else: self.after(100, poll)
        poll()

    def done(self, r):
        self.running = False; self.go.configure(state="normal", text="Trim this bridge")
        if isinstance(r, Exception):
            self.status.configure(text=str(r), fg=ACC); return
        self.edges, self.est, log = r
        saved = trimmer.cost(self.b) - trimmer.cost(self.b, self.edges)
        msg = f"{len(log)} changes save ${saved:,.0f}." if log else "Nothing could be trimmed under that stress limit."
        if not self.obs.get().strip(): msg += "\nEstimate is uncalibrated. Enter the game's stress % for a better one."
        self.status.configure(text=msg + "\nAlways test the result in the game.", fg=TEXT)
        self.sv.configure(state="normal" if log else "disabled"); self.refresh()

    def build(self):
        if self.b is None: return
        try: nb, est = trimmer.auto_build(self.b)
        except Exception as x:
            self.status.configure(text=str(x), fg=ACC); return
        self.b = nb; self.u = trimmer.stress(nb); self.edges = list(nb["br"]["edges"]); self.est = est
        self.sv.configure(state="normal"); self.refresh()
        self.status.configure(text="Built from the outermost anchors. Stress is a rough estimate, and the app can't see terrain or no-build zones, so check it in the game.", fg=TEXT)

    def save(self):
        try: out = trimmer.save_new(self.b, self.edges, self.name.get().strip())
        except Exception as x:
            messagebox.showerror("Bridge Trimmer", str(x)); return
        self.status.configure(text=f"Saved as a new slot:\n{os.path.basename(out)}\nYour original wasn't changed. Open it from the level's saves.", fg=TEXT)

if __name__ == "__main__":
    App().mainloop()
