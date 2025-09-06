import tkinter as tk
from PIL import Image
import io

NODE_WIDTH = 100
NODE_HEIGHT = 40
OUTLINE_WIDTH = 1
FONT_SIZE_LABEL = 10
FONT_SIZE_RECORD = 8
FONT_FAMILY = "Arial"
FONT_WEIGHT_LABEL = "bold"
FONT_WEIGHT_RECORD = "normal"

class ShapeComboBox(tk.Frame):
    """Custom grid dropdown for shape selection with icons and labels centered in a grid."""
    SHAPE_LIST = [
        ("ellipse", "Ellipse"),
        ("box", "Box"),
        ("class", "Class"),
        ("diamond", "Diamond"),
        ("parallelogram", "Parallelogram"),
        ("triangle", "Triangle"),
        ("hexagon", "Hexagon"),
        ("stick_figure", "Stick Figure"),
        ("circle", "Circle"),
        ("rbox", "R-Box"),
        ("assembly", "Assembly"),
        ("interface", "Interface"),
    ]
    ICON_SIZE = 32
    GRID_COLS = 3

    def __init__(self, master, variable, command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.variable = variable
        self.command = command
        self.icons = []
        self._make_icons()
        self.selected_index = self._find_index(variable.get())
        self.button = tk.Button(
            self,
            text=self.SHAPE_LIST[self.selected_index][1],
            width=24,
            height=2,
            command=self._show_popup,
            anchor="center",
            justify="center"
        )
        self.button.pack()
        variable.trace_add("write", self._on_var_change)
        self.popup = None

    def _make_icons(self):
        for shape, _ in self.SHAPE_LIST:
            img = self._draw_shape_icon(shape)
            self.icons.append(img)

    def _draw_shape_icon(self, shape):
        size = self.ICON_SIZE
        canvas = tk.Canvas(width=size, height=size, bg="white", highlightthickness=0)
        x0, y0, x1, y1 = 4, 4, size-4, size-4
        if shape == "ellipse":
            canvas.create_oval(x0, y0, x1, y1, fill="#e0e0e0", outline="black")
        elif shape == "circle":
            r = (size-8)//2
            cx, cy = size//2, size//2
            canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill="#e0e0e0", outline="black")
        elif shape == "box":
            canvas.create_rectangle(x0, y0, x1, y1, fill="#e0e0e0", outline="black")
        elif shape == "class":
            canvas.create_rectangle(x0, y0, x1, y1, fill="#e0e0e0", outline="black")
            canvas.create_rectangle(x0, y0, x1, y0+(y1-y0)//3, fill="#b0c4ff", outline="black")
            canvas.create_line(x0, y0+(y1-y0)//3, x1, y0+(y1-y0)//3)
        elif shape == "diamond":
            points = [size//2, y0, x1, size//2, size//2, y1, x0, size//2]
            canvas.create_polygon(points, fill="#e0e0e0", outline="black")
        elif shape == "parallelogram":
            offset = 6
            points = [x0+offset, y0, x1, y0, x1-offset, y1, x0, y1]
            canvas.create_polygon(points, fill="#e0e0e0", outline="black")
        elif shape == "triangle":
            points = [size//2, y0, x1, y1, x0, y1]
            canvas.create_polygon(points, fill="#e0e0e0", outline="black")
        elif shape == "hexagon":
            points = [
                x0+4, y0, x1-4, y0, x1, size//2, x1-4, y1, x0+4, y1, x0, size//2
            ]
            canvas.create_polygon(points, fill="#e0e0e0", outline="black")
        elif shape == "stick_figure":
            cx, cy = size//2, size//3
            r = 4
            canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#fff", outline="black")
            canvas.create_line(cx, cy+r, cx, y1-4)
            canvas.create_line(cx-6, cy+8, cx+6, cy+8)
            canvas.create_line(cx, y1-4, cx-5, y1)
            canvas.create_line(cx, y1-4, cx+5, y1)
        elif shape == "rbox":
            radius = 8
            canvas.create_arc(x0, y0, x0+2*radius, y0+2*radius, start=90, extent=90, style="pieslice", fill="#e0e0e0", outline="black")
            canvas.create_arc(x1-2*radius, y0, x1, y0+2*radius, start=0, extent=90, style="pieslice", fill="#e0e0e0", outline="black")
            canvas.create_arc(x1-2*radius, y1-2*radius, x1, y1, start=270, extent=90, style="pieslice", fill="#e0e0e0", outline="black")
            canvas.create_arc(x0, y1-2*radius, x0+2*radius, y1, start=180, extent=90, style="pieslice", fill="#e0e0e0", outline="black")
            canvas.create_rectangle(x0+radius, y0, x1-radius, y1, fill="#e0e0e0", outline="")
            canvas.create_rectangle(x0, y0+radius, x1, y1-radius, fill="#e0e0e0", outline="")
            canvas.create_line(x0+radius, y0, x1-radius, y0, fill="black")
            canvas.create_line(x1, y0+radius, x1, y1-radius, fill="black")
            canvas.create_line(x0+radius, y1, x1-radius, y1, fill="black")
            canvas.create_line(x0, y0+radius, x0, y1-radius, fill="black")
            canvas.create_arc(x0, y0, x0+2*radius, y0+2*radius, start=90, extent=90, style="arc", outline="black")
            canvas.create_arc(x1-2*radius, y0, x1, y0+2*radius, start=0, extent=90, style="arc", outline="black")
            canvas.create_arc(x1-2*radius, y1-2*radius, x1, y1, start=270, extent=90, style="arc", outline="black")
            canvas.create_arc(x0, y1-2*radius, x0+2*radius, y1, start=180, extent=90, style="arc", outline="black")
        elif shape == "assembly":
            cx, cy, r = size//2, size//2, (size-10)//2
            canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill="#e0e0e0", outline="black")
            canvas.create_arc(cx-r-4, cy-r-4, cx+r+4, cy+r+4, start=300, extent=120, style="arc", outline="black", width=2)
            canvas.create_line(cx-r-6, cy, cx-r, cy, fill="black", width=2)
            canvas.create_line(cx+r, cy, cx+r+6, cy, fill="black", width=2)
        elif shape == "interface":
            cx, cy = size // 2, size // 2
            r = size // 5
            line_length = 10
            canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                outline="gray", width=2, fill="#e0e0e0"
            )
            canvas.create_line(
                cx - r - line_length, cy, cx - r, cy,
                fill="gray", width=2
            )
            canvas.create_text(
                cx, cy,
                text="I", font=(FONT_FAMILY, 10, "bold"), anchor="center"
            )
        canvas.update()
        ps = canvas.postscript(colormode='color', width=size, height=size)
        pil_img = Image.open(io.BytesIO(ps.encode('utf-8')))
        pil_img = pil_img.convert("RGBA").resize((size, size), Image.LANCZOS)
        img_bytes = io.BytesIO()
        pil_img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        tk_img = tk.PhotoImage(data=img_bytes.read())
        canvas.destroy()
        return tk_img

    def _find_index(self, shape_name):
        for i, (shape, _) in enumerate(self.SHAPE_LIST):
            if shape == shape_name:
                return i
        return 0

    def _show_popup(self):
        if self.popup and tk.Toplevel.winfo_exists(self.popup):
            self.popup.destroy()
        self.popup = tk.Toplevel(self)
        self.popup.wm_overrideredirect(True)
        self.popup.attributes("-topmost", True)
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        self.popup.geometry(f"+{x}+{y}")
        for idx, (shape, label) in enumerate(self.SHAPE_LIST):
            row = idx // self.GRID_COLS
            col = idx % self.GRID_COLS
            frame = tk.Frame(self.popup, padx=6, pady=6)
            frame.grid(row=row, column=col)
            btn = tk.Button(
                frame,
                image=self.icons[idx],
                text=label,
                compound="top",
                anchor="center",
                justify="center",
                width=100,
                height=70,
                command=lambda i=idx: self._select_and_close(i)
            )
            btn.pack()
        self.popup.bind("<FocusOut>", lambda e: self.popup.destroy())
        self.popup.focus_set()

    def _select_and_close(self, idx):
        self._select(idx)
        if self.popup:
            self.popup.destroy()
            self.popup = None

    def _select(self, idx):
        shape, label = self.SHAPE_LIST[idx]
        self.selected_index = idx
        self.variable.set(shape)
        self.button.config(
            text=label,
            width=24,
            height=2,
            anchor="center",
            justify="center"
        )
        if self.command:
            self.command()

    def _on_var_change(self, *args):
        idx = self._find_index(self.variable.get())
        self.selected_index = idx
        self.button.config(
            text=self.SHAPE_LIST[idx][1],
            width=24,
            height=2,
            anchor="center",
            justify="center"
        )

def compute_class_node_height(lines_count, font_size_record=FONT_SIZE_RECORD):
    """Compute the height of a class node based on the number of lines."""
    line_height = font_size_record + 6
    title_height = NODE_HEIGHT // 3
    min_height = NODE_HEIGHT
    padding = 10
    total_height = title_height + (lines_count * line_height) + padding
    return max(min_height, total_height)

def draw_shape(canvas, x, y, node_width, node_height, label, attrs, is_selected):
    """Draw a shape on the canvas based on the specified attributes."""
    color = attrs.get("color", "#ffffff")
    shape = attrs.get("shape", "ellipse")
    font_size_label = attrs.get("font_size_label", FONT_SIZE_LABEL)
    font_weight_label = attrs.get("font_weight_label", FONT_WEIGHT_LABEL)
    justify = attrs.get("justify", "center")
    font_label = (FONT_FAMILY, font_size_label, font_weight_label)
    font_record = (FONT_FAMILY, FONT_SIZE_RECORD, FONT_WEIGHT_RECORD)
    highlight_color = "#ff6600"
    highlight_width = 3

    if is_selected or attrs.get("is_root", False):
        if shape == "ellipse":
            canvas.create_oval(
                x-2, y-2, x+node_width+2, y+node_height+2,
                outline=highlight_color, width=highlight_width
            )
        elif shape == "circle":
            diameter = min(node_width, node_height)
            cx = x + node_width // 2
            cy = y + node_height // 2
            canvas.create_oval(
                cx - diameter // 2 - 2, cy - diameter // 2 - 2,
                cx + diameter // 2 + 2, cy + diameter // 2 + 2,
                outline=highlight_color, width=highlight_width
            )
        elif shape in ("box", "class"):
            canvas.create_rectangle(
                x-2, y-2, x+node_width+2, y+node_height+2,
                outline=highlight_color, width=highlight_width
            )
        elif shape == "rbox":
            radius = min(node_width, node_height) // 5
            def rounded_rect(canvas, x, y, w, h, r, **kwargs):
                arc_kwargs = {k: v for k, v in kwargs.items() if k != "fill"}
                line_kwargs = {k: v for k, v in kwargs.items() if k != "outline"}
                canvas.create_arc(x-2, y-2, x-2+2*r, y-2+2*r, start=90, extent=90, style="arc", **arc_kwargs)
                canvas.create_arc(x+w-2*r+2, y-2, x+w+2, y-2+2*r, start=0, extent=90, style="arc", **arc_kwargs)
                canvas.create_arc(x+w-2*r+2, y+h-2*r+2, x+w+2, y+h+2, start=270, extent=90, style="arc", **arc_kwargs)
                canvas.create_arc(x-2, y+h-2*r+2, x-2+2*r, y+h+2, start=180, extent=90, style="arc", **arc_kwargs)
                canvas.create_line(x-2+r, y-2, x+w+2-r, y-2, **line_kwargs, fill=kwargs.get("outline", "black"))
                canvas.create_line(x+w+2, y-2+r, x+w+2, y+h+2-r, **line_kwargs, fill=kwargs.get("outline", "black"))
                canvas.create_line(x-2+r, y+h+2, x+w+2-r, y+h+2, **line_kwargs, fill=kwargs.get("outline", "black"))
                canvas.create_line(x-2, y-2+r, x-2, y+h+2-r, **line_kwargs, fill=kwargs.get("outline", "black"))
            rounded_rect(canvas, x, y, node_width, node_height, radius, outline=highlight_color, width=highlight_width)
        elif shape == "diamond":
            points = [
                x+node_width//2, y,
                x+node_width, y+node_height//2,
                x+node_width//2, y+node_height,
                x, y+node_height//2
            ]
            canvas.create_polygon(points, outline=highlight_color, width=highlight_width, fill="")
        elif shape == "parallelogram":
            offset = max(10, node_width//5)
            points = [
                x+offset, y,
                x+node_width, y,
                x+node_width-offset, y+node_height,
                x, y+node_height
            ]
            canvas.create_polygon(points, outline=highlight_color, width=highlight_width, fill="")
        elif shape == "triangle":
            points = [
                x+node_width//2, y,
                x+node_width, y+node_height,
                x, y+node_height
            ]
            canvas.create_polygon(points, outline=highlight_color, width=highlight_width, fill="")
        elif shape == "hexagon":
            points = [
                x+node_width//4, y,
                x+3*node_width//4, y,
                x+node_width, y+node_height//2,
                x+3*node_width//4, y+node_height,
                x+node_width//4, y+node_height,
                x, y+node_height//2
            ]
            canvas.create_polygon(points, outline=highlight_color, width=highlight_width, fill="")
        elif shape == "stick_figure":
            cx = x + node_width // 2
            cy = y + node_height // 3
            head_radius = min(node_width, node_height) // 6
            body_y1 = y + node_height - node_height // 6
            highlight_pad = 8
            canvas.create_oval(
                cx - head_radius - highlight_pad,
                cy - head_radius - highlight_pad,
                cx + head_radius + highlight_pad,
                body_y1 + highlight_pad,
                outline=highlight_color, width=highlight_width
            )
        elif shape == "assembly":
            cx = x + node_width // 2
            cy = y + node_height // 2
            r = min(node_width, node_height) // 2 - 4
            canvas.create_oval(
                cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4,
                outline=highlight_color, width=highlight_width
            )
        elif shape == "interface":
            cx = x + node_width // 2
            cy = y + node_height // 2
            r = min(node_width, node_height) // 3
            canvas.create_oval(
                cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4,
                outline=highlight_color, width=highlight_width
            )

    if justify == "left":
        anchor = "w"
        text_x = x + 5
    elif justify == "right":
        anchor = "e"
        text_x = x + node_width - 5
    else:
        anchor = "center"
        text_x = x + node_width // 2
    text_kwargs = {"anchor": anchor, "justify": justify}

    if shape == "ellipse":
        canvas.create_oval(
            x, y, x+node_width, y+node_height,
            fill=color, outline="black", width=OUTLINE_WIDTH
        )
        canvas.create_text(
            text_x, y+node_height//2,
            text=label, font=font_label, **text_kwargs
        )
    elif shape == "circle":
        diameter = min(node_width, node_height)
        cx = x + node_width // 2
        cy = y + node_height // 2
        canvas.create_oval(
            cx - diameter // 2, cy - diameter // 2,
            cx + diameter // 2, cy + diameter // 2,
            fill=color, outline="black", width=OUTLINE_WIDTH
        )
        canvas.create_text(
            cx, cy,
            text=label, font=font_label, anchor="center"
        )
    elif shape == "box":
        canvas.create_rectangle(
            x, y, x+node_width, y+node_height,
            fill=color, outline="black", width=OUTLINE_WIDTH
        )
        canvas.create_text(
            text_x, y+node_height//2,
            text=label, font=font_label, **text_kwargs
        )
    elif shape == "class":
        lines = attrs.get("class_lines", [])
        font_size_record = attrs.get("font_size_record", FONT_SIZE_RECORD)
        if "font_size_record" not in attrs and "font_size_label" in attrs:
            font_size_record = max(8, attrs.get("font_size_label", FONT_SIZE_LABEL) - 2)
        line_height = font_size_record + 2
        node_height = compute_class_node_height(len(lines), font_size_record)
        attrs["node_height"] = node_height
        canvas.create_rectangle(
            x, y, x+node_width, y+node_height,
            fill=color, outline="black", width=OUTLINE_WIDTH
        )
        title = attrs.get("class_title", label)
        canvas.create_rectangle(
            x, y, x+node_width, y+node_height//3,
            fill="#e0e0ff", outline="black", width=1
        )
        canvas.create_text(
            x+node_width//2, y+node_height//6,
            text=title, font=font_label, anchor="center"
        )
        canvas.create_line(
            x, y+node_height//3, x+node_width, y+node_height//3,
            width=1
        )
        if lines:
            for idx, line in enumerate(lines):
                canvas.create_text(
                    x+10,
                    y+node_height//3 + 6 + idx*line_height,
                    text="• " + line,
                    font=(FONT_FAMILY, font_size_record, FONT_WEIGHT_RECORD),
                    anchor="w"
                )
        else:
            canvas.create_text(
                x+node_width//2, y+2*node_height//3,
                text=label, font=font_record, anchor="center"
            )
        return node_height
    elif shape == "diamond":
        points = [
            x+node_width//2, y,
            x+node_width, y+node_height//2,
            x+node_width//2, y+node_height,
            x, y+node_height//2
        ]
        canvas.create_polygon(points, fill=color, outline="black", width=OUTLINE_WIDTH)
        canvas.create_text(
            x+node_width//2, y+node_height//2,
            text=label, font=font_label
        )
    elif shape == "parallelogram":
        offset = max(10, node_width//5)
        points = [
            x+offset, y,
            x+node_width, y,
            x+node_width-offset, y+node_height,
            x, y+node_height
        ]
        canvas.create_polygon(points, fill=color, outline="black", width=OUTLINE_WIDTH)
        canvas.create_text(
            x+node_width//2, y+node_height//2,
            text=label, font=font_label
        )
    elif shape == "triangle":
        points = [
            x+node_width//2, y,
            x+node_width, y+node_height,
            x, y+node_height
        ]
        canvas.create_polygon(points, fill=color, outline="black", width=OUTLINE_WIDTH)
        canvas.create_text(
            x+node_width//2, y+node_height//2,
            text=label, font=font_label
        )
    elif shape == "hexagon":
        points = [
            x+node_width//4, y,
            x+3*node_width//4, y,
            x+node_width, y+node_height//2,
            x+3*node_width//4, y+node_height,
            x+node_width//4, y+node_height,
            x, y+node_height//2
        ]
        canvas.create_polygon(points, fill=color, outline="black", width=OUTLINE_WIDTH)
        canvas.create_text(
            x+node_width//2, y+node_height//2,
            text=label, font=font_label
        )
    elif shape == "stick_figure":
        cx = x + node_width // 2
        cy = y + node_height // 3
        head_radius = min(node_width, node_height) // 6
        body_y0 = cy + head_radius
        body_y1 = y + node_height - node_height // 6
        canvas.create_oval(
            cx - head_radius, cy - head_radius,
            cx + head_radius, cy + head_radius,
            fill="#fff", outline="black", width=OUTLINE_WIDTH
        )
        canvas.create_line(
            cx, body_y0, cx, body_y1,
            fill="black", width=OUTLINE_WIDTH
        )
        arm_y = body_y0 + (body_y1 - body_y0) // 4
        arm_span = node_width // 3
        canvas.create_line(
            cx - arm_span, arm_y, cx + arm_span, arm_y,
            fill="black", width=OUTLINE_WIDTH
        )
        leg_y0 = body_y1
        leg_y1 = y + node_height
        leg_span = node_width // 5
        canvas.create_line(
            cx, leg_y0, cx - leg_span, leg_y1,
            fill="black", width=OUTLINE_WIDTH
        )
        canvas.create_line(
            cx, leg_y0, cx + leg_span, leg_y1,
            fill="black", width=OUTLINE_WIDTH
        )
        canvas.create_text(
            cx, y + node_height,
            text=label, font=font_label, anchor="n"
        )
    elif shape == "rbox":
        radius = min(node_width, node_height) // 5
        def rounded_rect(canvas, x, y, w, h, r, **kwargs):
            canvas.create_arc(x, y, x+2*r, y+2*r, start=90, extent=90, style="pieslice", **kwargs)
            canvas.create_arc(x+w-2*r, y, x+w, y+2*r, start=0, extent=90, style="pieslice", **kwargs)
            canvas.create_arc(x+w-2*r, y+h-2*r, x+w, y+h, start=270, extent=90, style="pieslice", **kwargs)
            canvas.create_arc(x, y+h-2*r, x+2*r, y+h, start=180, extent=90, style="pieslice", **kwargs)
            canvas.create_rectangle(x+r, y, x+w-r, y+h, **kwargs)
            canvas.create_rectangle(x, y+r, x+w, y+h-r, **kwargs)
        rounded_rect(canvas, x, y, node_width, node_height, radius, fill=color, outline="black", width=OUTLINE_WIDTH)
        canvas.create_text(
            x+node_width//2, y+node_height//2,
            text=label, font=font_label, anchor="center"
        )
    elif shape == "assembly":
        cx = x + node_width // 2
        cy = y + node_height // 2
        r = min(node_width, node_height) // 2 - 4
        canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=color, outline="black", width=OUTLINE_WIDTH
        )
        arc_pad = 8
        canvas.create_arc(
            cx - r - arc_pad, cy - r - arc_pad, cx + r + arc_pad, cy + r + arc_pad,
            start=300, extent=120, style="arc", outline="black", width=2
        )
        canvas.create_line(
            cx - r - 18, cy, cx - r, cy, fill="black", width=2
        )
        canvas.create_line(
            cx + r, cy, cx + r + 18, cy, fill="black", width=2
        )
        canvas.create_text(
            cx, cy,
            text=label, font=font_label, anchor="center"
        )
    elif shape == "interface":
        cx = x + node_width // 2
        cy = y + node_height // 2
        r = min(node_width, node_height) // 3
        line_length = 18
        canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline="gray", width=2, fill=color
        )
        canvas.create_line(
            cx - r - line_length, cy, cx - r, cy,
            fill="gray", width=3
        )
        canvas.create_text(
            cx, cy,
            text=label, font=font_label, anchor="center"
        )
    return node_height
