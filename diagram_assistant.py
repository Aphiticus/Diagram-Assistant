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

import tkinter as tk
from tkinter import ttk, colorchooser
from PIL import Image
import io
import json
from shapes import ShapeComboBox, draw_shape, compute_class_node_height

X_SPACING = 40
Y_SPACING = 60
EDGE_OFFSET = 20
CANVAS_DEFAULT_WIDTH = 600
CANVAS_DEFAULT_HEIGHT = 400

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
        self.node_shape = tk.StringVar(value="class")  # Default to "class"
        self.shape_combo = ShapeComboBox(
            control_frame,
            variable=self.node_shape,
            command=self.on_shape_change
        )
        self.shape_combo.pack(side="left", padx=2)
        tk.Label(control_frame, text="Orientation:").pack(side="left")
        self.orientation = tk.StringVar(value="TB")
        orient_menu = ttk.Combobox(
            control_frame,
            textvariable=self.orientation,
            values=["TB", "LR", "RL"],
            state="readonly"
        )
        orient_menu.pack(side="left")
        orient_menu.bind("<<ComboboxSelected>>", self.on_orientation_change)
        tk.Button(control_frame, text="Undo", command=self.undo).pack(side="left")
        tk.Button(control_frame, text="Redo", command=self.redo).pack(side="left")
        tk.Button(control_frame, text="Center", command=self.center_canvas).pack(side="left")
        tk.Button(control_frame, text="Reverse Edge", command=self.reverse_edge).pack(side="left")
        display_frame = tk.Frame(root)
        display_frame.pack(side="top", fill="both", expand=True)
        self.canvas = tk.Canvas(display_frame, bg="white")
        self.canvas.pack(side="right", fill="both", expand=True)
        self.nodes = {}
        self.root_node_id = "root"
        self.nodes[self.root_node_id] = {
            "id": self.root_node_id,
            "text": "Root",
            "attrs": {
                "color": "#ffffff",
                "shape": "class", 
                "orientation": "TB",
                "font_size_label": 10,
                "font_weight_label": "bold"
            },
            "children": []
        }
        self.selected_node_id = self.root_node_id
        self.global_orientation = "TB"
        self.history = []
        self.redo_stack = []
        self.save_history()
        self.canvas.bind("<Double-1>", self.on_canvas_double_click)
        self.canvas.bind("<Button-1>", self.on_canvas_single_click)
        root.bind("<Control-z>", lambda event: self.undo())
        root.bind("<Control-y>", lambda event: self.redo())
        root.bind("<Delete>", lambda event: self.delete_node()) 
        self.update_diagram() 

    def save_history(self):
        import copy
        state = (
            copy.deepcopy(self.nodes),
            self.selected_node_id,
            self.global_orientation
        )
        self.history.append(state)
        if len(self.history) > 100:
            self.history.pop(0)
        self.redo_stack.clear()

    def restore_history(self, state):
        import copy
        self.nodes = copy.deepcopy(state[0])
        self.selected_node_id = state[1]
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
        self.apply_node_attr("orientation", self.orientation.get())
        if self.selected_node_id == self.root_node_id:
            self.global_orientation = self.orientation.get()
        self.update_diagram()
        self.save_history()

    def apply_node_attr(self, key, value):
        node_id = self.selected_node_id
        node = self.nodes.get(node_id)
        if node:
            node["attrs"][key] = value
            self.update_diagram()
            self.save_history()

    def add_child(self):
        parent_id = self.selected_node_id
        parent = self.nodes.get(parent_id)
        if parent is not None:
            new_id = f"node_{len(self.nodes)}"
            self.nodes[new_id] = {
                "id": new_id,
                "text": "New Node",
                "attrs": {
                    "color": self.node_color.get(),
                    "shape": self.node_shape.get(),
                    "orientation": self.orientation.get(),
                    "font_size_label": 10,
                    "font_weight_label": "bold"
                },
                "children": []
            }
            parent["children"].append(new_id)
            self.selected_node_id = new_id
            self.update_diagram()
            self.save_history()

    def delete_node(self):
        node_id = self.selected_node_id
        if node_id == self.root_node_id:
            return
        def find_parent(nid, parent_id=None):
            for pid, node in self.nodes.items():
                if nid in node["children"]:
                    return pid
            return None
        parent_id = find_parent(node_id)
        if parent_id:
            self.nodes[parent_id]["children"].remove(node_id)
        def delete_subtree(nid):
            for child in self.nodes[nid]["children"]:
                delete_subtree(child)
            del self.nodes[nid]
        delete_subtree(node_id)
        self.selected_node_id = self.root_node_id
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
        self.update_diagram()
        bbox = self.canvas.bbox("all")
        if not bbox:
            return
        x0, y0, x1, y1 = bbox
        width = x1 - x0
        height = y1 - y0
        from tkinter.filedialog import asksaveasfilename
        file_path = asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if not file_path:
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
        self.update_diagram()

    def save_diagram(self):
        from tkinter.filedialog import asksaveasfilename
        file_path = asksaveasfilename(defaultextension=".diagram", filetypes=[("Diagram files", "*.diagram")])
        if not file_path:
            return
        if not file_path.lower().endswith(".diagram"):
            file_path += ".diagram"
        def serialize_node(nid):
            node = self.nodes[nid]
            return {
                "id": nid,
                "text": node["text"],
                "attrs": node["attrs"],
                "children": [serialize_node(child) for child in node["children"]]
            }
        data = {
            "tree": serialize_node(self.root_node_id),
            "global_orientation": self.global_orientation
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_diagram(self):
        from tkinter.filedialog import askopenfilename
        file_path = askopenfilename(defaultextension=".diagram", filetypes=[("Diagram files", "*.diagram")])
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return
        self.nodes.clear()
        def restore_tree(node_data):
            nid = node_data["id"]
            self.nodes[nid] = {
                "id": nid,
                "text": node_data["text"],
                "attrs": node_data.get("attrs", {}),
                "children": []
            }
            for child in node_data.get("children", []):
                self.nodes[nid]["children"].append(child["id"])
                restore_tree(child)
        restore_tree(data["tree"])
        self.root_node_id = data["tree"]["id"]
        self.selected_node_id = self.root_node_id
        self.global_orientation = data.get("global_orientation", "TB")
        self.update_diagram()
        self.save_history()
        self.center_root_top()

    def center_root_top(self):
        self.update_diagram()

    def update_diagram(self):
        self.canvas.delete("all")
        self.canvas.config(bg="white")
        self.node_canvas_boxes = {}
        node_width = 100
        node_height = 40
        x_spacing = X_SPACING
        y_spacing = Y_SPACING
        edge_offset = EDGE_OFFSET
        selected_nodes = {self.selected_node_id}

        def draw_node(node_id, x, y):
            node = self.nodes[node_id]
            label = node["text"]
            attrs = node["attrs"]
            node_width = attrs.get("node_width", 100)
            node_height = attrs.get("node_height", 40)
            self.node_canvas_boxes[node_id] = (x, y, x + node_width, y + node_height)
            node_height = draw_shape(self.canvas, x, y, node_width, node_height, label, attrs, node_id in selected_nodes)
            attrs["node_height"] = node_height
            node["attrs"] = attrs

        def get_orientation(node_id, parent_orientation):
            attrs = self.nodes[node_id]["attrs"]
            return attrs.get("orientation", parent_orientation if parent_orientation else self.global_orientation)

        def boxes_overlap(box1, box2):
            return not (box1[2] <= box2[0] or box1[0] >= box2[2] or box1[3] <= box2[1] or box1[1] >= box2[3])

        def layout_tree(node_id, x, y, parent_orientation=None, placed_boxes=None):
            if placed_boxes is None:
                placed_boxes = []
            node = self.nodes[node_id]
            attrs = node["attrs"]
            node_width = attrs.get("node_width", 100)
            node_height = attrs.get("node_height", 40)
            draw_node(node_id, x, y)
            node_box = (x, y, x + node_width, y + node_height)
            placed_boxes.append(node_box)
            children = node["children"]
            n = len(children)
            if n == 0:
                return
            orientation = get_orientation(node_id, parent_orientation)
            if orientation == "LR":
                child_x = x + node_width + X_SPACING
                child_positions = []
                total_height = 0
                child_heights = []
                for child in children:
                    c_attrs = self.nodes[child]["attrs"]
                    c_height = c_attrs.get("node_height", 40)
                    child_heights.append(c_height)
                    total_height += c_height
                total_height += (n - 1) * Y_SPACING
                start_y = y + node_height // 2 - total_height // 2
                cy = start_y
                for i, child in enumerate(children):
                    c_attrs = self.nodes[child]["attrs"]
                    c_height = c_attrs.get("node_height", 40)
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
                    c_attrs = self.nodes[child]["attrs"]
                    c_width = c_attrs.get("node_width", 100)
                    c_height = c_attrs.get("node_height", 40)
                    parent_shape = self.nodes[node_id]["attrs"].get("shape", "ellipse")
                    if parent_shape == "stick_figure":
                        y0 = y + node_height - 2
                    else:
                        y0 = y + node_height // 2
                    mid_parent_x = x + node_width + EDGE_OFFSET
                    mid_child_x = cx - EDGE_OFFSET
                    x0 = x + node_width
                    y1 = cy + c_height // 2
                    x1 = cx
                    points = [
                        x0, y0,
                        mid_parent_x, y0,
                        mid_child_x, y1,
                        x1, y1
                    ]
                    if c_attrs.get("reverse_edge", False):
                        self.canvas.create_line(
                            points,
                            arrow=tk.FIRST, width=1, smooth=True
                        )
                    else:
                        self.canvas.create_line(
                            points,
                            arrow=tk.LAST, width=1, smooth=True
                        )
                    layout_tree(child, cx, cy, orientation, placed_boxes)
            elif orientation == "RL":
                child_x = x - node_width - X_SPACING
                child_positions = []
                total_height = 0
                child_heights = []
                for child in children:
                    c_attrs = self.nodes[child]["attrs"]
                    c_height = c_attrs.get("node_height", 40)
                    child_heights.append(c_height)
                    total_height += c_height
                total_height += (n - 1) * Y_SPACING
                start_y = y + node_height // 2 - total_height // 2
                cy = start_y
                for i, child in enumerate(children):
                    c_attrs = self.nodes[child]["attrs"]
                    c_height = c_attrs.get("node_height", 40)
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
                    c_attrs = self.nodes[child]["attrs"]
                    c_width = c_attrs.get("node_width", 100)
                    c_height = c_attrs.get("node_height", 40)
                    parent_shape = self.nodes[node_id]["attrs"].get("shape", "ellipse")
                    if parent_shape == "stick_figure":
                        y0 = y + node_height - 2
                    else:
                        y0 = y + node_height // 2
                    mid_parent_x = x - EDGE_OFFSET
                    mid_child_x = cx + c_width + EDGE_OFFSET
                    x0 = x
                    y1 = cy + c_height // 2
                    x1 = cx + c_width
                    points = [
                        x0, y0,
                        mid_parent_x, y0,
                        mid_child_x, y1,
                        x1, y1
                    ]
                    if c_attrs.get("reverse_edge", False):
                        self.canvas.create_line(
                            points,
                            arrow=tk.FIRST, width=1, smooth=True
                        )
                    else:
                        self.canvas.create_line(
                            points,
                            arrow=tk.LAST, width=1, smooth=True
                        )
                    layout_tree(child, cx, cy, orientation, placed_boxes)
            else:
                child_positions = []
                total_width = 0
                child_widths = []
                child_heights = []
                for child in children:
                    c_attrs = self.nodes[child]["attrs"]
                    c_width = c_attrs.get("node_width", 100)
                    c_height = c_attrs.get("node_height", 40)
                    child_widths.append(c_width)
                    child_heights.append(c_height)
                    total_width += c_width
                total_width += (n - 1) * X_SPACING
                start_x = x + node_width // 2 - total_width // 2
                cx = start_x
                for i, child in enumerate(children):
                    c_attrs = self.nodes[child]["attrs"]
                    c_width = c_attrs.get("node_width", 100)
                    c_height = c_attrs.get("node_height", 40)
                    child_x = cx
                    child_y = y + node_height + Y_SPACING
                    tries = 0
                    while True:
                        child_box = (child_x, child_y, child_x + c_width, child_y + c_height)
                        collision = any(boxes_overlap(child_box, b) for b in placed_boxes)
                        if not collision:
                            break
                        child_x += c_width + X_SPACING
                        tries += 1
                        if tries > 20:
                            break
                    child_positions.append((child, child_x, child_y))
                    placed_boxes.append((child_x, child_y, child_x + c_width, child_y + c_height))
                    cx = child_x + c_width + X_SPACING
                for child, cx, cy in child_positions:
                    c_attrs = self.nodes[child]["attrs"]
                    c_width = c_attrs.get("node_width", 100)
                    c_height = c_attrs.get("node_height", 40)
                    parent_shape = self.nodes[node_id]["attrs"].get("shape", "ellipse")
                    if parent_shape == "stick_figure":
                        x0 = x + node_width // 2
                        y0 = y + node_height + 15
                    else:
                        x0 = x + node_width // 2
                        y0 = y + node_height
                    mid_parent_y = y0 + EDGE_OFFSET
                    mid_child_y = cy - EDGE_OFFSET
                    x1 = cx + c_width // 2
                    points = [
                        x0, y0,
                        x0, mid_parent_y,
                        x1, mid_child_y,
                        x1, cy
                    ]
                    if c_attrs.get("reverse_edge", False):
                        self.canvas.create_line(
                            points,
                            arrow=tk.FIRST, width=1, smooth=True
                        )
                    else:
                        self.canvas.create_line(
                            points,
                            arrow=tk.LAST, width=1, smooth=True
                        )
                    layout_tree(child, cx, cy, orientation, placed_boxes)
        canvas_width = self.canvas.winfo_width() or CANVAS_DEFAULT_WIDTH
        canvas_height = self.canvas.winfo_height() or CANVAS_DEFAULT_HEIGHT
        root_orientation = get_orientation(self.root_node_id, None)
        root_attrs = self.nodes[self.root_node_id]["attrs"]
        root_width = root_attrs.get("node_width", 100)
        root_height = root_attrs.get("node_height", 40)
        x0 = (canvas_width // 2) - (root_width // 2)
        y0 = 30
        layout_tree(self.root_node_id, x0, y0, None, [])
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def on_canvas_double_click(self, event):
        if not hasattr(self, "node_canvas_boxes"):
            return
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        for node_id, (x0, y0, x1, y1) in self.node_canvas_boxes.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                self.selected_node_id = node_id
                self.on_node_edit_dialog(node_id)
                break

    def on_node_edit_dialog(self, node_id):
        node = self.nodes[node_id]
        old_text = node["text"]
        attrs = node["attrs"]
        current_font_size = attrs.get("font_size_label", 10)
        current_font_weight = attrs.get("font_weight_label", "bold")
        current_width = attrs.get("node_width", 100)
        current_height = attrs.get("node_height", 40)
        current_justify = attrs.get("justify", "center")
        current_color = attrs.get("color", "#ffffff")
        shape = attrs.get("shape", self.node_shape.get())
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Node")
        tk.Label(dialog, text="Node Name:").pack()
        if shape == "class":
            tk.Label(dialog, text="Class Title:").pack()
            title_var = tk.StringVar(value=attrs.get("class_title", old_text))
            title_entry = tk.Entry(dialog, textvariable=title_var)
            title_entry.pack()
            tk.Label(dialog, text="Class Info (one per line):").pack()
            lines_text = tk.Text(dialog, height=5, width=30)
            lines = attrs.get("class_lines", [])
            if lines and lines[-1].strip() != "":
                lines = lines + [""]
            elif not lines:
                lines = [""]
            lines_text.insert("1.0", "\n".join(lines))
            lines_text.pack()
        else:
            name_text = tk.Text(dialog, height=3, width=30)
            name_text.pack()
            name_text.insert("1.0", old_text)
        tk.Label(dialog, text="Justify:").pack()
        justify_var = tk.StringVar(value=current_justify)
        justify_menu = ttk.Combobox(dialog, textvariable=justify_var, values=["left", "center", "right"], state="readonly")
        justify_menu.pack()
        tk.Label(dialog, text="Node Color:").pack()
        color_var = tk.StringVar(value=current_color)
        color_frame = tk.Frame(dialog)
        color_frame.pack()
        color_display = tk.Label(color_frame, width=8, height=2, background=current_color)
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
            if shape == "class":
                new_title = title_var.get().strip()
                new_lines = [l.strip() for l in lines_text.get("1.0", "end-1c").splitlines() if l.strip()]
                node["text"] = new_title
                attrs["class_title"] = new_title
                attrs["class_lines"] = new_lines
                attrs["node_height"] = compute_class_node_height(len(new_lines))
            else:
                new_text = name_text.get("1.0", "end-1c").strip()
                node["text"] = new_text
                attrs["node_height"] = int(height_var.get())
            attrs["font_size_label"] = font_var.get()
            attrs["font_weight_label"] = style_var.get()
            attrs["node_width"] = int(width_var.get())
            attrs["justify"] = justify_var.get()
            attrs["color"] = color_var.get()
            node["attrs"] = attrs
            self.selected_node_id = node_id
            self.update_diagram()
            self.save_history()
            dialog.destroy()
        tk.Button(dialog, text="Apply", command=apply).pack()
        if shape == "class":
            title_entry.bind("<Control-Return>", apply)
            lines_text.bind("<Control-Return>", apply)
        else:
            name_text.bind("<Control-Return>", apply)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.wait_window()

    def on_canvas_single_click(self, event):
        if not hasattr(self, "node_canvas_boxes"):
            return
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        for node_id, (x0, y0, x1, y1) in self.node_canvas_boxes.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                self.selected_node_id = node_id
                self.update_diagram()
                break

    def reverse_edge(self):
        node_id = self.selected_node_id
        if node_id == self.root_node_id:
            return
        attrs = self.nodes[node_id]["attrs"]
        attrs["reverse_edge"] = not attrs.get("reverse_edge", False)
        self.nodes[node_id]["attrs"] = attrs
        self.update_diagram()
        self.save_history()

root = tk.Tk()
app = DiagramApp(root)
root.mainloop()
