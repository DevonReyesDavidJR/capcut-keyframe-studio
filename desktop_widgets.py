"""Antialiased rounded surfaces shared by native editor controls."""
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw, ImageTk

def rounded_surface(width, height, background, fill, radius=14, border=None):
    scale = 3
    image = Image.new("RGB", (max(2, width) * scale, max(2, height) * scale), background)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((scale, scale, (width - 1) * scale, (height - 1) * scale),
                           radius=max(1, radius * scale), fill=fill,
                           outline=border or fill, width=scale)
    return ImageTk.PhotoImage(image.resize((max(2, width), max(2, height)), Image.Resampling.LANCZOS))

class RoundedPanel(tk.Canvas):
    def __init__(self, parent, fill="#171a20", border="#303742", radius=16,
                 padding=12, width=200, height=80, autoheight=True):
        try:
            background = parent.cget("bg")
        except tk.TclError:
            background = "#101216"
        super().__init__(parent, bg=background, width=width, height=height,
                         highlightthickness=0, borderwidth=0)
        self.fill, self.border, self.radius = fill, border, radius
        self.padding, self.autoheight = padding, autoheight
        self.body = tk.Frame(self, bg=fill, borderwidth=0)
        self.window = self.create_window(padding, padding, anchor="nw", window=self.body)
        self.bind("<Configure>", self._layout)
        self.body.bind("<Configure>", self._content_changed)

    def _content_changed(self, event):
        if self.autoheight:
            requested = self.body.winfo_reqheight() + self.padding * 2
            if int(float(self.cget("height"))) != requested:
                self.configure(height=requested)

    def _layout(self, event):
        width, height = max(2, event.width), max(2, event.height)
        self.itemconfigure(self.window, width=max(1, width - self.padding * 2))
        if not self.autoheight:
            self.itemconfigure(self.window, height=max(1, height - self.padding * 2))
        self.surface = rounded_surface(width, height, self.cget("bg"), self.fill,
                                       min(self.radius, height // 2), self.border)
        self.delete("surface")
        self.create_image(0, 0, anchor="nw", image=self.surface, tags="surface")
        self.tag_lower("surface")

class RoundedCombobox(RoundedPanel):
    def __init__(self, parent, width=20, **kwargs):
        super().__init__(parent, fill="#262c36", border="#384250", radius=10,
                         padding=7, width=width * 8 + 20, height=40, autoheight=False)
        self.combo = ttk.Combobox(self.body, width=width, style="Rounded.TCombobox", **kwargs)
        self.combo.pack(fill="both", expand=True)

    def __setitem__(self, key, value):
        if key == "values":
            self.combo[key] = value
        else:
            super().__setitem__(key, value)

    def __getitem__(self, key):
        if key == "values":
            return self.combo[key]
        return super().__getitem__(key)

    def current(self, value=None):
        return self.combo.current() if value is None else self.combo.current(value)

    def get(self):
        return self.combo.get()

    def set(self, value):
        return self.combo.set(value)

    def bind(self, sequence=None, func=None, add=None):
        if sequence and sequence.startswith("<<") and hasattr(self, "combo"):
            return self.combo.bind(sequence, func, add)
        return super().bind(sequence, func, add)
