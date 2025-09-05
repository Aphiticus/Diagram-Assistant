"""
Diagram Assistant - Interactive Node Diagram Editor

This script provides a Tkinter GUI for creating, editing, and visualizing hierarchical diagrams.
Features:
- Add/delete nodes
- Change node color, shape, orientation, and size
- Undo/redo actions
- Edit node label and style
- Export diagram visually

Example usage:
1. Run the script.
2. Click "Add Child" to add nodes.
3. Select a node to change its color, shape, or orientation.
4. Double-click a node to edit its label and size.
5. Use Undo/Redo to revert changes.

Simple diagram example:
Root
 ├─ New Node
 └─ New Node
      └─ New Node

"""

import tkinter as tk
from tkinter import ttk, colorchooser
from PIL import Image
import io
import json

NODE_WIDTH = 100
NODE_HEIGHT = 40
X_SPACING = 40
Y_SPACING = 60
OUTLINE_WIDTH = 1
EDGE_OFFSET = 20
CANVAS_DEFAULT_WIDTH = 600
CANVAS_DEFAULT_HEIGHT = 400
FONT_SIZE_LABEL = 10
FONT_SIZE_RECORD = 8
FONT_FAMILY = "Arial"
FONT_WEIGHT_LABEL = "bold"
FONT_WEIGHT_RECORD = "normal"

class DiagramApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Diagram Assistant")
        menubar = tk.Menu(root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Save", command=self.save_diagram)
        filemenu.add_command(label="Load", command=self.load_diagram)
        filemenu.add_separator()
        filemenu.add_command(label="Export as PNG", command=self.export_png)
        menubar.add_cascade(label="File", menu=filemenu)
        root.config(menu=menubar)
        control_frame = tk.Frame(root)
        control_frame.pack(side="top", fill="x")
        tk.Button(control_frame, text="Add Child", command=self.add_child).pack(side="left")
        tk.Button(control_frame, text="Delete Node", command=self.delete_node).pack(side="left")
        tk.Label(control_frame, text="Node Color:").pack(side="left")
        self.node_color = tk.StringVar(value="#ffffff")
        tk.Button(control_frame, text="Pick", command=self.pick_color).pack(side="left")
        tk.Label(control_frame, text="Shape:").pack(side="left")
        self.node_shape = tk.StringVar(value="ellipse")
        shape_menu = ttk.Combobox(
            control_frame,
            textvariable=self.node_shape,
            values=[
                "ellipse", "box", "record",
                "diamond", "parallelogram", "triangle", "hexagon"
            ],
            state="readonly"
        )
        shape_menu.pack(side="left")
        shape_menu.bind("<<ComboboxSelected>>", self.on_shape_change)
        tk.Label(control_frame, text="Orientation:").pack(side="left")
        self.orientation = tk.StringVar(value="TB")
        orient_menu = ttk.Combobox(
            control_frame,
            textvariable=self.orientation,
            values=["TB", "LR", "RL"],  # Added RL
            state="readonly"
        )
        orient_menu.pack(side="left")
        orient_menu.bind("<<ComboboxSelected>>", self.on_orientation_change)
        tk.Button(control_frame, text="Undo", command=self.undo).pack(side="left")
        tk.Button(control_frame, text="Redo", command=self.redo).pack(side="left")
        tk.Button(control_frame, text="Center", command=self.center_canvas).pack(side="left")
        display_frame = tk.Frame(root)
        display_frame.pack(side="top", fill="both", expand=True)
        self.tree = ttk.Treeview(display_frame)
        self.tree.pack(side="left", fill="y")
        self.tree.insert("", "end", "root", text="Root")
        self.canvas = tk.Canvas(display_frame, bg="white")
        self.canvas.pack(side="right", fill="both", expand=True)
        self.node_attrs = {}
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<Button-3>", self.on_tree_right_click)
        self.canvas.bind("<Double-1>", self.on_canvas_double_click)
        self.canvas.bind("<Button-1>", self.on_canvas_single_click)
        self.global_orientation = "TB"  
        self.history = []
        self.redo_stack = []
        self.save_history()
        root.bind("<Control-z>", lambda event: self.undo())
        root.bind("<Control-y>", lambda event: self.redo())

    def save_history(self):
        import copy
        state = (
            copy.deepcopy(self.node_attrs),
            [self.tree.item(i, "text") for i in self.tree.get_children("")],
            self.global_orientation
        )
        self.history.append(state)
        if len(self.history) > 100:
            self.history.pop(0)
        self.redo_stack.clear()
    def restore_history(self, state):
        import copy
        self.node_attrs = copy.deepcopy(state[0])
        root_children = self.tree.get_children("")
        for i, name in zip(root_children, state[1]):
            self.tree.item(i, text=name)
        self.global_orientation = state[2]
        self.update_diagram()

    def undo(self):
        if len(self.history) > 1:
            self.redo_stack.append(self.history.pop())
            prev_state = self.history[-1]
            self.restore_history(prev_state)

    def redo(self):
        if self.redo_stack:
            next_state = self.redo_stack.pop()
            self.history.append(next_state)
            self.restore_history(next_state)

    def pick_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.node_color.set(color)
            self.apply_node_attr("color", color)
            self.save_history()

    def on_shape_change(self, event=None):
        self.apply_node_attr("shape", self.node_shape.get())
        self.save_history()

    def on_orientation_change(self, event=None):
        selected = self.tree.selection()
        if selected:
            node_id = selected[0]
            self.apply_node_attr("orientation", self.orientation.get())
            if node_id == "root":
                self.global_orientation = self.orientation.get()
        else:
            self.global_orientation = self.orientation.get()
        self.update_diagram()
        self.save_history()

    def apply_node_attr(self, key, value):
        selected = self.tree.selection()
        if selected:
            node_id = selected[0]
            attrs = self.node_attrs.get(node_id, {
                "color": self.node_color.get(),
                "shape": self.node_shape.get(),
                "orientation": self.orientation.get(),
                "font_size_label": FONT_SIZE_LABEL,
                "font_weight_label": FONT_WEIGHT_LABEL
            })
            attrs[key] = value
            self.node_attrs[node_id] = attrs
            self.update_diagram()
            self.save_history()

    def on_tree_right_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id:
            color = colorchooser.askcolor()[1]
            if color:
                attrs = self.node_attrs.get(item_id, {
                    "color": "#ffffff",
                    "shape": self.node_shape.get(),
                    "orientation": self.orientation.get(),
                    "font_size_label": FONT_SIZE_LABEL
                })
                attrs["color"] = color
                self.node_attrs[item_id] = attrs
                self.node_color.set(color)
                self.update_diagram()
                self.save_history()

    def add_child(self):
        selected = self.tree.selection()
        if selected:
            node_id = self.tree.insert(selected[0], "end", text="New Node")
            self.node_attrs[node_id] = {
                "color": self.node_color.get(),
                "shape": self.node_shape.get(),
                "orientation": self.orientation.get(),
                "font_size_label": FONT_SIZE_LABEL
            }
            self.update_diagram()
            self.save_history()

    def delete_node(self):
        selected = self.tree.selection()
        for node in selected:
            if node != "root":
                self.tree.delete(node)
                self.node_attrs.pop(node, None)
        self.update_diagram()
        self.save_history()

    def center_canvas(self):
        sr = self.canvas.bbox("all")
        if sr:
            x0, y0, x1, y1 = sr
            canvas_w = self.canvas.winfo_width()
            canvas_h = self.canvas.winfo_height()
            cx = (x1 + x0) // 2 - canvas_w // 2
            cy = (y1 + y0) // 2 - canvas_h // 2
            self.canvas.xview_moveto(max(cx, 0) / max((x1 - x0), 1))
            self.canvas.yview_moveto(max(cy, 0) / max((y1 - y0), 1))

    def export_png(self):
        old_selection = self.tree.selection()
        self.tree.selection_remove(self.tree.selection())
        self.update_diagram()
        bbox = self.canvas.bbox("all")
        if not bbox:
            self.tree.selection_set(old_selection)
            self.update_diagram()
            return
        x0, y0, x1, y1 = bbox
        width = x1 - x0
        height = y1 - y0
        from tkinter.filedialog import asksaveasfilename
        file_path = asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if not file_path:
            self.tree.selection_set(old_selection)
            self.update_diagram()
            return
        if not file_path.lower().endswith(".png"):
            file_path += ".png"
        ps = self.canvas.postscript(colormode='color', x=x0, y=y0, width=width, height=height)
        img = Image.open(io.BytesIO(ps.encode('utf-8')))
        img = img.convert("RGBA")
        img = img.crop((0, 0, width, height))
        border = 30  
        out_w = width + 2 * border
        out_h = height + 2 * border
        out_img = Image.new("RGBA", (out_w, out_h), "white")
        paste_x = (out_w - width) // 2
        paste_y = (out_h - height) // 2
        out_img.paste(img, (paste_x, paste_y), img)
        out_img = out_img.convert("RGB")
        out_img.save(file_path, "PNG")
        self.tree.selection_set(old_selection)
        self.update_diagram()

    def save_diagram(self):
        from tkinter.filedialog import asksaveasfilename
        file_path = asksaveasfilename(defaultextension=".diagram", filetypes=[("Diagram files", "*.diagram")])
        if not file_path:
            return
        if not file_path.lower().endswith(".diagram"):
            file_path += ".diagram"
        def get_tree(node):
            return {
                "id": node,
                "text": self.tree.item(node, "text"),
                "attrs": self.node_attrs.get(node, {}),
                "children": [get_tree(child) for child in self.tree.get_children(node)]
            }
        data = {
            "tree": get_tree("root"),
            "global_orientation": self.global_orientation
        }
        with open(file_path, "w", encoding="utf-8") as f:
            import json
            json.dump(data, f, indent=2)

    def load_diagram(self):
        from tkinter.filedialog import askopenfilename
        file_path = askopenfilename(defaultextension=".diagram", filetypes=[("Diagram files", "*.diagram")])
        if not file_path:
            return
        try:
            import json
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return
        for node in self.tree.get_children(""):
            self.tree.delete(node)
        self.node_attrs.clear()
        if not self.tree.exists("root"):
            self.tree.insert("", "end", "root", text=data["tree"]["text"])
        else:
            self.tree.item("root", text=data["tree"]["text"])
        self.node_attrs["root"] = data["tree"].get("attrs", {})
        def restore_tree(parent, node_data):
            node_id = self.tree.insert(parent, "end", text=node_data["text"])
            self.node_attrs[node_id] = node_data.get("attrs", {})
            for child in node_data.get("children", []):
                restore_tree(node_id, child)
            return node_id
        for child in data["tree"].get("children", []):
            restore_tree("root", child)
        self.global_orientation = data.get("global_orientation", "TB")
        self.update_diagram()
        self.save_history()

    def update_diagram(self):
        self.canvas.delete("all")
        self.canvas.config(bg="white")
        # Store node bounding boxes for hit-testing
        self.node_canvas_boxes = {}  # node_id: (x0, y0, x1, y1)
        node_width = NODE_WIDTH
        node_height = NODE_HEIGHT
        x_spacing = X_SPACING
        y_spacing = Y_SPACING
        outline_width = OUTLINE_WIDTH
        edge_offset = EDGE_OFFSET
        font_label = (FONT_FAMILY, FONT_SIZE_LABEL, FONT_WEIGHT_LABEL)
        font_record = (FONT_FAMILY, FONT_SIZE_RECORD, FONT_WEIGHT_RECORD)
        selected_nodes = set(self.tree.selection())
        def draw_node(node, x, y):
            label = self.tree.item(node)["text"]
            attrs = self.node_attrs.get(node, {})
            color = attrs.get("color", "#ffffff")
            shape = attrs.get("shape", "ellipse")
            font_size_label = attrs.get("font_size_label", FONT_SIZE_LABEL)
            font_weight_label = attrs.get("font_weight_label", FONT_WEIGHT_LABEL)
            node_width = attrs.get("node_width", NODE_WIDTH)
            node_height = attrs.get("node_height", NODE_HEIGHT)
            justify = attrs.get("justify", "center")
            font_label = (FONT_FAMILY, font_size_label, font_weight_label)
            font_record = (FONT_FAMILY, FONT_SIZE_RECORD, FONT_WEIGHT_RECORD)
            highlight = node in selected_nodes
            highlight_color = "#ff6600"
            highlight_width = 3
            # Store bounding box for hit-testing
            self.node_canvas_boxes[node] = (x, y, x + node_width, y + node_height)
            if highlight:
                if shape == "ellipse":
                    self.canvas.create_oval(
                        x-2, y-2, x+node_width+2, y+node_height+2,
                        outline=highlight_color, width=highlight_width
                    )
                elif shape in ("box", "record"):
                    self.canvas.create_rectangle(
                        x-2, y-2, x+node_width+2, y+node_height+2,
                        outline=highlight_color, width=highlight_width
                    )
                elif shape == "diamond":
                    points = [
                        x+node_width//2, y-2,
                        x+node_width+2, y+node_height//2,
                        x+node_width//2, y+node_height+2,
                        x-2, y+node_height//2
                    ]
                    self.canvas.create_polygon(points, outline=highlight_color, width=highlight_width, fill="")
                elif shape == "parallelogram":
                    offset = max(10, node_width//5)
                    points = [
                        x+offset, y-2,
                        x+node_width+2, y-2,
                        x+node_width-offset+2, y+node_height+2,
                        x-2, y+node_height+2
                    ]
                    self.canvas.create_polygon(points, outline=highlight_color, width=highlight_width, fill="")
                elif shape == "triangle":
                    points = [
                        x+node_width//2, y-2,
                        x+node_width+2, y+node_height+2,
                        x-2, y+node_height+2
                    ]
                    self.canvas.create_polygon(points, outline=highlight_color, width=highlight_width, fill="")
                elif shape == "hexagon":
                    points = [
                        x+node_width//4, y-2,
                        x+3*node_width//4, y-2,
                        x+node_width+2, y+node_height//2,
                        x+3*node_width//4, y+node_height+2,
                        x+node_width//4, y+node_height+2,
                        x-2, y+node_height//2
                    ]
                    self.canvas.create_polygon(points, outline=highlight_color, width=highlight_width, fill="")
            # Determine anchor and justify for create_text
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
                self.canvas.create_oval(
                    x, y, x+node_width, y+node_height,
                    fill=color, outline="black", width=OUTLINE_WIDTH
                )
                self.canvas.create_text(
                    text_x, y+node_height//2,
                    text=label, font=font_label, **text_kwargs
                )
            elif shape == "box":
                self.canvas.create_rectangle(
                    x, y, x+node_width, y+node_height,
                    fill=color, outline="black", width=OUTLINE_WIDTH
                )
                self.canvas.create_text(
                    text_x, y+node_height//2,
                    text=label, font=font_label, **text_kwargs
                )
            elif shape == "record":
                self.canvas.create_rectangle(
                    x, y, x+node_width, y+node_height,
                    fill=color, outline="black", width=OUTLINE_WIDTH
                )
                self.canvas.create_line(
                    x, y+node_height//2, x+node_width, y+node_height//2,
                    width=OUTLINE_WIDTH, smooth=True
                )
                self.canvas.create_text(
                    text_x, y+node_height//4,
                    text=label, font=font_label, **text_kwargs
                )
                self.canvas.create_text(
                    x+node_width//2, y+3*node_height//4,
                    text="id:int | name:str", font=font_record
                )
                return
            elif shape == "diamond":
                points = [
                    x+node_width//2, y,
                    x+node_width, y+node_height//2,
                    x+node_width//2, y+node_height,
                    x, y+node_height//2
                ]
                self.canvas.create_polygon(points, fill=color, outline="black", width=OUTLINE_WIDTH)
                self.canvas.create_text(
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
                self.canvas.create_polygon(points, fill=color, outline="black", width=OUTLINE_WIDTH)
                self.canvas.create_text(
                    x+node_width//2, y+node_height//2,
                    text=label, font=font_label
                )
            elif shape == "triangle":
                points = [
                    x+node_width//2, y,
                    x+node_width, y+node_height,
                    x, y+node_height
                ]
                self.canvas.create_polygon(points, fill=color, outline="black", width=OUTLINE_WIDTH)
                self.canvas.create_text(
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
                self.canvas.create_polygon(points, fill=color, outline="black", width=OUTLINE_WIDTH)
                self.canvas.create_text(
                    x+node_width//2, y+node_height//2,
                    text=label, font=font_label
                )
        def get_orientation(node, parent_orientation):
            attrs = self.node_attrs.get(node, {})
            return attrs.get("orientation", parent_orientation if parent_orientation else self.global_orientation)
        def boxes_overlap(box1, box2):
            return not (box1[2] <= box2[0] or box1[0] >= box2[2] or box1[3] <= box2[1] or box1[1] >= box2[3])
        def layout_tree(node, x, y, parent_orientation=None, placed_boxes=None):
            if placed_boxes is None:
                placed_boxes = []
            attrs = self.node_attrs.get(node, {})
            node_width = attrs.get("node_width", NODE_WIDTH)
            node_height = attrs.get("node_height", NODE_HEIGHT)
            draw_node(node, x, y)
            node_box = (x, y, x + node_width, y + node_height)
            placed_boxes.append(node_box)
            children = self.tree.get_children(node)
            n = len(children)
            if n == 0:
                return
            orientation = get_orientation(node, parent_orientation)
            if orientation == "LR":
                child_x = x + node_width + X_SPACING
                child_positions = []
                total_height = 0
                child_heights = []
                for child in children:
                    c_attrs = self.node_attrs.get(child, {})
                    c_height = c_attrs.get("node_height", NODE_HEIGHT)
                    child_heights.append(c_height)
                    total_height += c_height
                total_height += (n - 1) * Y_SPACING
                start_y = y + node_height // 2 - total_height // 2
                cy = start_y
                for i, child in enumerate(children):
                    c_attrs = self.node_attrs.get(child, {})
                    c_height = c_attrs.get("node_height", NODE_HEIGHT)
                    child_y = cy
                    tries = 0
                    while True:
                        child_box = (child_x, child_y, child_x + node_width, child_y + c_height)
                        collision = any(boxes_overlap(child_box, b) for b in placed_boxes)
                        if not collision:
                            break
                        child_y += c_height + Y_SPACING
                        tries += 1
                        if tries > 20:
                            break
                    child_positions.append((child, child_x, child_y))
                    placed_boxes.append((child_x, child_y, child_x + node_width, child_y + c_height))
                    cy = child_y + c_height + Y_SPACING
                for child, cx, cy in child_positions:
                    c_attrs = self.node_attrs.get(child, {})
                    c_width = c_attrs.get("node_width", NODE_WIDTH)
                    c_height = c_attrs.get("node_height", NODE_HEIGHT)
                    mid_parent_x = x + node_width + EDGE_OFFSET
                    mid_child_x = cx - EDGE_OFFSET
                    y0 = y + node_height // 2
                    x0 = x + node_width
                    y1 = cy + c_height // 2
                    x1 = cx
                    points = [
                        x0, y0,
                        mid_parent_x, y0,
                        mid_child_x, y1,
                        x1, y1
                    ]
                    self.canvas.create_line(
                        points,
                        arrow=tk.LAST, width=OUTLINE_WIDTH, smooth=True
                    )
                    layout_tree(child, cx, cy, orientation, placed_boxes)
            elif orientation == "RL":
                child_x = x - node_width - X_SPACING
                child_positions = []
                total_height = 0
                child_heights = []
                for child in children:
                    c_attrs = self.node_attrs.get(child, {})
                    c_height = c_attrs.get("node_height", NODE_HEIGHT)
                    child_heights.append(c_height)
                    total_height += c_height
                total_height += (n - 1) * Y_SPACING
                start_y = y + node_height // 2 - total_height // 2
                cy = start_y
                for i, child in enumerate(children):
                    c_attrs = self.node_attrs.get(child, {})
                    c_height = c_attrs.get("node_height", NODE_HEIGHT)
                    child_y = cy
                    tries = 0
                    while True:
                        child_box = (child_x, child_y, child_x + node_width, child_y + c_height)
                        collision = any(boxes_overlap(child_box, b) for b in placed_boxes)
                        if not collision:
                            break
                        child_y += c_height + Y_SPACING
                        tries += 1
                        if tries > 20:
                            break
                    child_positions.append((child, child_x, child_y))
                    placed_boxes.append((child_x, child_y, child_x + node_width, child_y + c_height))
                    cy = child_y + c_height + Y_SPACING
                for child, cx, cy in child_positions:
                    c_attrs = self.node_attrs.get(child, {})
                    c_width = c_attrs.get("node_width", NODE_WIDTH)
                    c_height = c_attrs.get("node_height", NODE_HEIGHT)
                    mid_parent_x = x - EDGE_OFFSET
                    mid_child_x = cx + c_width + EDGE_OFFSET
                    y0 = y + node_height // 2
                    x0 = x
                    y1 = cy + c_height // 2
                    x1 = cx + c_width
                    points = [
                        x0, y0,
                        mid_parent_x, y0,
                        mid_child_x, y1,
                        x1, y1
                    ]
                    self.canvas.create_line(
                        points,
                        arrow=tk.LAST, width=OUTLINE_WIDTH, smooth=True
                    )
                    layout_tree(child, cx, cy, orientation, placed_boxes)
            else:
                child_positions = []
                total_width = 0
                child_widths = []
                for child in children:
                    c_attrs = self.node_attrs.get(child, {})
                    c_width = c_attrs.get("node_width", NODE_WIDTH)
                    child_widths.append(c_width)
                    total_width += c_width
                total_width += (n - 1) * X_SPACING
                start_x = x + node_width // 2 - total_width // 2
                cx = start_x
                for i, child in enumerate(children):
                    c_attrs = self.node_attrs.get(child, {})
                    c_width = c_attrs.get("node_width", NODE_WIDTH)
                    child_x = cx
                    child_y = y + node_height + Y_SPACING
                    tries = 0
                    while True:
                        child_box = (child_x, child_y, child_x + c_width, child_y + NODE_HEIGHT)
                        collision = any(boxes_overlap(child_box, b) for b in placed_boxes)
                        if not collision:
                            break
                        child_x += c_width + X_SPACING
                        tries += 1
                        if tries > 20:
                            break
                    child_positions.append((child, child_x, child_y))
                    placed_boxes.append((child_x, child_y, child_x + c_width, child_y + NODE_HEIGHT))
                    cx = child_x + c_width + X_SPACING
                for child, cx, cy in child_positions:
                    c_attrs = self.node_attrs.get(child, {})
                    c_width = c_attrs.get("node_width", NODE_WIDTH)
                    c_height = c_attrs.get("node_height", NODE_HEIGHT)
                    mid_parent_y = y + node_height + EDGE_OFFSET
                    mid_child_y = cy - EDGE_OFFSET
                    x0 = x + node_width // 2
                    y0 = y + node_height
                    x1 = cx + c_width // 2
                    points = [
                        x0, y0,
                        x0, mid_parent_y,
                        x1, mid_child_y,
                        x1, cy
                    ]
                    self.canvas.create_line(
                        points,
                        arrow=tk.LAST, width=OUTLINE_WIDTH, smooth=True
                    )
                    layout_tree(child, cx, cy, orientation, placed_boxes)
        canvas_width = self.canvas.winfo_width() or CANVAS_DEFAULT_WIDTH
        canvas_height = self.canvas.winfo_height() or CANVAS_DEFAULT_HEIGHT
        root_orientation = get_orientation("root", None)
        root_attrs = self.node_attrs.get("root", {})
        root_width = root_attrs.get("node_width", NODE_WIDTH)
        root_height = root_attrs.get("node_height", NODE_HEIGHT)
        if root_orientation == "LR":
            x0 = 30
            y0 = canvas_height // 2 - root_height // 2
        elif root_orientation == "RL":
            x0 = canvas_width - root_width - 30
            y0 = canvas_height // 2 - root_height // 2
        else:
            x0 = canvas_width // 2 - root_width // 2
            y0 = 30
        layout_tree("root", x0, y0, None, [])
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
    def on_tree_select(self, event):
        selected = self.tree.selection()
        if selected:
            node_id = selected[0]
            attrs = self.node_attrs.get(node_id, {})
            self.node_color.set(attrs.get("color", "#ffffff"))
            self.node_shape.set(attrs.get("shape", "ellipse"))
            self.orientation.set(attrs.get("orientation", self.global_orientation))
            self.update_diagram()
    def on_tree_double_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id:
            old_text = self.tree.item(item_id, "text")
            attrs = self.node_attrs.get(item_id, {})
            current_font_size = attrs.get("font_size_label", FONT_SIZE_LABEL)
            current_font_weight = attrs.get("font_weight_label", FONT_WEIGHT_LABEL)
            current_width = attrs.get("node_width", NODE_WIDTH)
            current_height = attrs.get("node_height", NODE_HEIGHT)
            current_justify = attrs.get("justify", "center")
            current_color = attrs.get("color", "#ffffff")
            dialog = tk.Toplevel(self.root)
            dialog.title("Edit Node")
            tk.Label(dialog, text="Node Name:").pack()
            name_text = tk.Text(dialog, height=3, width=30)
            name_text.pack()
            name_text.insert("1.0", old_text)
            tk.Label(dialog, text="Justify:").pack()
            justify_var = tk.StringVar(value=current_justify)
            justify_menu = ttk.Combobox(dialog, textvariable=justify_var, values=["left", "center", "right"], state="readonly")
            justify_menu.pack()
            # Add color picker below Justify
            tk.Label(dialog, text="Node Color:").pack()
            color_var = tk.StringVar(value=current_color)
            color_frame = tk.Frame(dialog)
            color_frame.pack()
            color_display = tk.Label(color_frame, width=8, height=2, background=current_color)  # was width=4
            color_display.pack(side="left", padx=2)
            def pick_color():
                color = colorchooser.askcolor(color_var.get())[1]
                if color:
                    color_var.set(color)
                    color_display.config(background=color)
            tk.Button(color_frame, text="Pick", command=pick_color).pack(side="left")
            tk.Label(dialog, text="Font Size:").pack()
            font_var = tk.IntVar(value=current_font_size)
            tk.Entry(dialog, textvariable=font_var).pack()
            tk.Label(dialog, text="Font Style:").pack()
            style_var = tk.StringVar(value=current_font_weight)
            style_menu = ttk.Combobox(dialog, textvariable=style_var, values=["normal", "bold", "italic"], state="readonly")
            style_menu.pack()
            tk.Label(dialog, text="Node Width:").pack()
            width_var = tk.IntVar(value=current_width)
            tk.Entry(dialog, textvariable=width_var).pack()
            tk.Label(dialog, text="Node Height:").pack()
            height_var = tk.IntVar(value=current_height)
            tk.Entry(dialog, textvariable=height_var).pack()
            def apply(event=None):
                new_text = name_text.get("1.0", "end-1c").strip()
                new_font_size = font_var.get()
                new_font_weight = style_var.get()
                new_width = width_var.get()
                new_height = height_var.get()
                new_justify = justify_var.get()
                new_color = color_var.get()
                if new_text:
                    self.tree.item(item_id, text=new_text)
                attrs["font_size_label"] = new_font_size
                attrs["font_weight_label"] = new_font_weight
                attrs["node_width"] = new_width
                attrs["node_height"] = new_height
                attrs["justify"] = new_justify
                attrs["color"] = new_color
                self.node_attrs[item_id] = attrs
                self.update_diagram()
                self.save_history()
                dialog.destroy()
            tk.Button(dialog, text="Apply", command=apply).pack()
            name_text.bind("<Control-Return>", apply)
            dialog.transient(self.root)
            dialog.grab_set()
            dialog.wait_window()

    def on_canvas_double_click(self, event):
        # Find which node (if any) was double-clicked
        if not hasattr(self, "node_canvas_boxes"):
            return
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        for node_id, (x0, y0, x1, y1) in self.node_canvas_boxes.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                # Select the node in the tree for consistency
                self.tree.selection_set(node_id)
                self.on_tree_double_click_canvas(node_id)
                break

    def on_tree_double_click_canvas(self, item_id):
        old_text = self.tree.item(item_id, "text")
        attrs = self.node_attrs.get(item_id, {})
        current_font_size = attrs.get("font_size_label", FONT_SIZE_LABEL)
        current_font_weight = attrs.get("font_weight_label", FONT_WEIGHT_LABEL)
        current_width = attrs.get("node_width", NODE_WIDTH)
        current_height = attrs.get("node_height", NODE_HEIGHT)
        current_justify = attrs.get("justify", "center")
        current_color = attrs.get("color", "#ffffff")
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Node")
        tk.Label(dialog, text="Node Name:").pack()
        name_text = tk.Text(dialog, height=3, width=30)
        name_text.pack()
        name_text.insert("1.0", old_text)
        tk.Label(dialog, text="Justify:").pack()
        justify_var = tk.StringVar(value=current_justify)
        justify_menu = ttk.Combobox(dialog, textvariable=justify_var, values=["left", "center", "right"], state="readonly")
        justify_menu.pack()
        # Add color picker below Justify
        tk.Label(dialog, text="Node Color:").pack()
        color_var = tk.StringVar(value=current_color)
        color_frame = tk.Frame(dialog)
        color_frame.pack()
        color_display = tk.Label(color_frame, width=8, height=2, background=current_color)  # was width=4
        color_display.pack(side="left", padx=2)
        def pick_color():
            color = colorchooser.askcolor(color_var.get())[1]
            if color:
                color_var.set(color)
                color_display.config(background=color)
        tk.Button(color_frame, text="Pick", command=pick_color).pack(side="left")
        tk.Label(dialog, text="Font Size:").pack()
        font_var = tk.IntVar(value=current_font_size)
        tk.Entry(dialog, textvariable=font_var).pack()
        tk.Label(dialog, text="Font Style:").pack()
        style_var = tk.StringVar(value=current_font_weight)
        style_menu = ttk.Combobox(dialog, textvariable=style_var, values=["normal", "bold", "italic"], state="readonly")
        style_menu.pack()
        tk.Label(dialog, text="Node Width:").pack()
        width_var = tk.IntVar(value=current_width)
        tk.Entry(dialog, textvariable=width_var).pack()
        tk.Label(dialog, text="Node Height:").pack()
        height_var = tk.IntVar(value=current_height)
        tk.Entry(dialog, textvariable=height_var).pack()
        def apply(event=None):
            new_text = name_text.get("1.0", "end-1c").strip()
            new_font_size = font_var.get()
            new_font_weight = style_var.get()
            new_width = width_var.get()
            new_height = height_var.get()
            new_justify = justify_var.get()
            new_color = color_var.get()
            if new_text:
                self.tree.item(item_id, text=new_text)
            attrs["font_size_label"] = new_font_size
            attrs["font_weight_label"] = new_font_weight
            attrs["node_width"] = new_width
            attrs["node_height"] = new_height
            attrs["justify"] = new_justify
            attrs["color"] = new_color
            self.node_attrs[item_id] = attrs
            self.update_diagram()
            self.save_history()
            dialog.destroy()
        tk.Button(dialog, text="Apply", command=apply).pack()
        name_text.bind("<Control-Return>", apply)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.wait_window()

    def on_canvas_single_click(self, event):
        # Highlight/select the node in the tree when user clicks on a node in the canvas
        if not hasattr(self, "node_canvas_boxes"):
            return
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        for node_id, (x0, y0, x1, y1) in self.node_canvas_boxes.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                self.tree.selection_set(node_id)
                self.update_diagram()
                break

root = tk.Tk()
app = DiagramApp(root)
root.mainloop()

