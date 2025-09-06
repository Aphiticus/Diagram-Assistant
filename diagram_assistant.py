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

import tkinter as tk
from tkinter import ttk, colorchooser
from PIL import Image
import io
import json
from shapes import ShapeComboBox, draw_shape, compute_class_node_height
import math

X_SPACING = 40
Y_SPACING = 60
EDGE_OFFSET = 20
CANVAS_DEFAULT_WIDTH = 600
CANVAS_DEFAULT_HEIGHT = 400
EXPORT_SCALE = 1.5  

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
        self.node_shape = tk.StringVar(value="class")  
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
            values=["TB", "BT", "LR", "RL"],  
            state="readonly"
        )
        orient_menu.pack(side="left")
        orient_menu.bind("<<ComboboxSelected>>", self.on_orientation_change)
        tk.Button(control_frame, text="Undo", command=self.undo).pack(side="left")
        tk.Button(control_frame, text="Redo", command=self.redo).pack(side="left")
        tk.Button(control_frame, text="Center", command=self.center_canvas).pack(side="left")
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
        self.dragging_node_id = None
        self.drag_offset = (0, 0)
        self.drag_line = None
        self.highlighted_node_id = None  
        self.connections = []  
        self.save_history()
        self.canvas.bind("<Double-1>", self.on_canvas_double_click)
        self.canvas.bind("<Button-1>", self.on_canvas_single_click)
        root.bind("<Control-z>", lambda event: self.undo())
        root.bind("<Control-y>", lambda event: self.redo())
        root.bind("<Delete>", lambda event: self.delete_node()) 
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)  
        self.update_diagram() 

    def save_history(self):
        import copy
        state = (
            copy.deepcopy(self.nodes),
            self.selected_node_id,
            self.global_orientation,
            copy.deepcopy(self.connections),
            self.highlighted_node_id
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
        self.connections = copy.deepcopy(state[3]) if len(state) > 3 else []
        self.highlighted_node_id = state[4] if len(state) > 4 else None
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
        # Temporarily disable highlight before export
        prev_selected = self.selected_node_id
        prev_highlighted = self.highlighted_node_id
        self.selected_node_id = None
        self.highlighted_node_id = None
        self.update_diagram()
        bbox = self.canvas.bbox("all")
        if not bbox:
            # Restore highlight state
            self.selected_node_id = prev_selected
            self.highlighted_node_id = prev_highlighted
            self.update_diagram()
            return
        x0, y0, x1, y1 = bbox
        width = x1 - x0
        height = y1 - y0
        from tkinter.filedialog import asksaveasfilename
        file_path = asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if not file_path:
            # Restore highlight state
            self.selected_node_id = prev_selected
            self.highlighted_node_id = prev_highlighted
            self.update_diagram()
            return
        if not file_path.lower().endswith(".png"):
            file_path += ".png"
        scale = EXPORT_SCALE  
        int_width = int(round(width * scale))
        int_height = int(round(height * scale))
        ps = self.canvas.postscript(
            colormode='color',
            x=x0, y=y0,
            width=width, height=height,
            pagewidth=int_width, pageheight=int_height,
            rotate=0
        )
        img = Image.open(io.BytesIO(ps.encode('utf-8')))
        img = img.convert("RGBA")
        img = img.resize((int_width, int_height), Image.LANCZOS)
        img = img.crop((0, 0, int_width, int_height))
        border = int(30 * scale)
        out_w = int_width + 2 * border
        out_h = int_height + 2 * border
        out_img = Image.new("RGBA", (out_w, out_h), "white")
        paste_x = (out_w - int_width) // 2
        paste_y = (out_h - int_height) // 2
        out_img.paste(img, (paste_x, paste_y), img)
        out_img = out_img.convert("RGB")
        out_img.save(file_path, "PNG")
        # Restore highlight state
        self.selected_node_id = prev_selected
        self.highlighted_node_id = prev_highlighted
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
            "global_orientation": self.global_orientation,
            "connections": self.connections
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
        if not hasattr(self, "nodes"):
            self.nodes = {}
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
        self.connections = data.get("connections", [])
        self.highlighted_node_id = None
        self.update_diagram()
        self.save_history()
        self.center_root_top()

    def center_root_top(self):
        self.update_diagram()

    def update_diagram(self):
        self.canvas.delete("all")
        self.canvas.config(bg="white")
        self.node_canvas_boxes = {}
        self.line_id_to_connection = {}  # Map canvas line id to connection
        node_width = 100
        node_height = 40
        x_spacing = X_SPACING
        y_spacing = Y_SPACING
        edge_offset = EDGE_OFFSET
        selected_nodes = {self.selected_node_id}
        def get_node_position(node_id, default_x, default_y):
            node = self.nodes[node_id]
            attrs = node["attrs"]
            mx = attrs.get("manual_x")
            my = attrs.get("manual_y")
            if mx is not None and my is not None:
                return mx, my
            return default_x, default_y

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
            x, y = get_node_position(node_id, x, y)
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
                    if child == self.dragging_node_id:
                        child_positions.append((child, child_x, child_y))
                        placed_boxes.append((child_x, child_y, child_x + node_width, child_y + c_height))
                        cy = child_y + c_height + Y_SPACING
                        continue
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
                    child_x, child_y = get_node_position(child, cx, cy)
                    c_attrs = self.nodes[child]["attrs"]
                    c_width = c_attrs.get("node_width", 100)
                    c_height = c_attrs.get("node_height", 40)
                    parent_shape = self.nodes[node_id]["attrs"].get("shape", "ellipse")
                    if parent_shape == "stick_figure":
                        y0 = y + node_height - 2
                    else:
                        y0 = y + node_height // 2
                    mid_parent_x = x + node_width + EDGE_OFFSET
                    mid_child_x = child_x - EDGE_OFFSET
                    x0 = x + node_width
                    y1 = child_y + c_height // 2
                    x1 = child_x
                    points = [
                        x0, y0,
                        mid_parent_x, y0,
                        mid_child_x, y1,
                        x1, y1
                    ]
                    layout_tree(child, child_x, child_y, orientation, placed_boxes)
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
                    if child == self.dragging_node_id:
                        child_positions.append((child, child_x, child_y))
                        placed_boxes.append((child_x, child_y, child_x + node_width, child_y + c_height))
                        cy = child_y + c_height + Y_SPACING
                        continue
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
                    child_x, child_y = get_node_position(child, cx, cy)
                    c_attrs = self.nodes[child]["attrs"]
                    c_width = c_attrs.get("node_width", 100)
                    c_height = c_attrs.get("node_height", 40)
                    parent_shape = self.nodes[node_id]["attrs"].get("shape", "ellipse")
                    if parent_shape == "stick_figure":
                        y0 = y + node_height - 2
                    else:
                        y0 = y + node_height // 2
                    mid_parent_x = x - EDGE_OFFSET
                    mid_child_x = child_x + c_width + EDGE_OFFSET
                    x0 = x
                    y1 = child_y + c_height // 2
                    x1 = child_x + c_width
                    points = [
                        x0, y0,
                        mid_parent_x, y0,
                        mid_child_x, y1,
                        x1, y1
                    ]

                    layout_tree(child, child_x, child_y, orientation, placed_boxes)
            elif orientation == "BT":
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
                    child_y = y - c_height - Y_SPACING
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
                    child_x, child_y = get_node_position(child, cx, cy)
                    c_attrs = self.nodes[child]["attrs"]
                    c_width = c_attrs.get("node_width", 100)
                    c_height = c_attrs.get("node_height", 40)
                    parent_shape = self.nodes[node_id]["attrs"].get("shape", "ellipse")
                    if parent_shape == "stick_figure":
                        x0 = x + node_width // 2
                        y0 = y - 15
                    else:
                        x0 = x + node_width // 2
                        y0 = y
                    mid_parent_y = y0 - EDGE_OFFSET
                    mid_child_y = child_y + c_height + EDGE_OFFSET
                    x1 = child_x + c_width // 2
                    points = [
                        x0, y0,
                        x0, mid_parent_y,
                        x1, mid_child_y,
                        x1, child_y + c_height
                    ]
                    layout_tree(child, child_x, child_y, orientation, placed_boxes)
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
                    child_x, child_y = get_node_position(child, cx, cy)
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
                    mid_child_y = child_y - EDGE_OFFSET
                    x1 = child_x + c_width // 2
                    points = [
                        x0, y0,
                        x0, mid_parent_y,
                        x1, mid_child_y,
                        x1, child_y
                    ]
                    layout_tree(child, child_x, child_y, orientation, placed_boxes)
        canvas_width = self.canvas.winfo_width() or CANVAS_DEFAULT_WIDTH
        canvas_height = self.canvas.winfo_height() or CANVAS_DEFAULT_HEIGHT
        root_orientation = self.nodes[self.root_node_id]["attrs"].get("orientation", self.global_orientation)
        root_attrs = self.nodes[self.root_node_id]["attrs"]
        root_width = root_attrs.get("node_width", 100)
        root_height = root_attrs.get("node_height", 40)
        x0 = (canvas_width // 2) - (root_width // 2)
        y0 = (canvas_height // 2) - (root_height // 2)
        layout_tree(self.root_node_id, x0, y0, None, [])
        # Draw connections (edges/arrows) after layout
        self.draw_connections()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def get_border_point(self, x0, y0, x1, y1, cx, cy, shape):
        """
        Given a rectangle (x0, y0, x1, y1), center (cx, cy), and a direction (to another center),
        return the point on the border in the direction of (tx, ty).
        Supports 'ellipse', 'circle', and rectangle-like shapes.
        """
        # Center of the node
        node_cx = (x0 + x1) / 2
        node_cy = (y0 + y1) / 2
        dx = cx - node_cx
        dy = cy - node_cy
        if dx == 0 and dy == 0:
            return node_cx, node_cy  # fallback

        if shape in ("ellipse", "circle"):
            # Ellipse/circle border intersection
            rx = abs(x1 - x0) / 2
            ry = abs(y1 - y0) / 2
            if rx == 0 or ry == 0:
                return node_cx, node_cy
            # Normalize direction
            norm = math.hypot(dx, dy)
            dxn = dx / norm
            dyn = dy / norm
            # Parametric intersection
            px = node_cx + rx * dxn
            py = node_cy + ry * dyn
            return px, py
        else:
            # Rectangle border intersection
            # Compute intersection with rectangle sides
            min_x, min_y, max_x, max_y = x0, y0, x1, y1
            # Direction vector
            dx = cx - node_cx
            dy = cy - node_cy
            # Avoid division by zero
            if dx == 0:
                y = max_y if dy > 0 else min_y
                return node_cx, y
            if dy == 0:
                x = max_x if dx > 0 else min_x
                return x, node_cy
            # Compute intersection with each side, pick nearest
            candidates = []
            # Left/right sides
            for x in (min_x, max_x):
                t = (x - node_cx) / dx
                y = node_cy + t * dy
                if min_y <= y <= max_y and t > 0:
                    candidates.append((x, y, t))
            # Top/bottom sides
            for y in (min_y, max_y):
                t = (y - node_cy) / dy
                x = node_cx + t * dx
                if min_x <= x <= max_x and t > 0:
                    candidates.append((x, y, t))
            if not candidates:
                return node_cx, node_cy
            # Pick the intersection with the smallest positive t
            x, y, _ = min(candidates, key=lambda c: c[2])
            return x, y

    def draw_connections(self):
        """Draw all user-created connections/arrows."""
        self.line_id_to_connection = {}
        for conn in self.connections:
            from_id = conn["from"]
            to_id = conn["to"]
            line_type = conn.get("type", "single")
            if from_id not in self.node_canvas_boxes or to_id not in self.node_canvas_boxes:
                continue
            x0, y0, x1, y1 = self.node_canvas_boxes[from_id]
            x0b, y0b, x1b, y1b = self.node_canvas_boxes[to_id]
            fx = (x0 + x1) / 2
            fy = (y0 + y1) / 2
            tx = (x0b + x1b) / 2
            ty = (y0b + y1b) / 2
            from_shape = self.nodes[from_id]["attrs"].get("shape", "ellipse")
            to_shape = self.nodes[to_id]["attrs"].get("shape", "ellipse")
            start_x, start_y = self.get_border_point(x0, y0, x1, y1, tx, ty, from_shape)
            end_x, end_y = self.get_border_point(x0b, y0b, x1b, y1b, fx, fy, to_shape)
            # --- Anti-collision detour ---
            waypoints = self.find_detour(start_x, start_y, end_x, end_y, from_id, to_id)
            points = [start_x, start_y]
            for wx, wy in waypoints:
                points.extend([wx, wy])
            points.extend([end_x, end_y])
            if line_type == "single":
                line_id = self.canvas.create_line(*points, width=2, fill="black")
                self._bind_line_context_menu(line_id, conn)
            elif line_type == "arrow":
                line_id = self.canvas.create_line(*points, width=2, fill="black", arrow=tk.LAST)
                self._bind_line_context_menu(line_id, conn)
            elif line_type == "double":
                # For parallel lines, you may want to offset all segments, but for now, just use the main path
                ids = self._draw_parallel_lines(start_x, start_y, end_x, end_y, arrow1=False, arrow2=False, conn=conn)
            elif line_type == "double_arrow":
                ids = self._draw_parallel_lines(start_x, start_y, end_x, end_y, arrow1=True, arrow2=True, conn=conn)
            elif line_type == "double_arrow_oneway":
                ids = self._draw_parallel_lines(start_x, start_y, end_x, end_y, arrow1=True, arrow2=False, conn=conn)
            # Add more types as needed

    def _bind_line_context_menu(self, line_id, conn):
        self.line_id_to_connection[line_id] = conn
        self.canvas.tag_bind(line_id, "<Button-3>", self._on_line_right_click)

    def _on_line_right_click(self, event):
        # Find which line was clicked
        line_id = self.canvas.find_withtag("current")
        if not line_id:
            return
        line_id = line_id[0]
        conn = self.line_id_to_connection.get(line_id)
        if not conn:
            return
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(
            label="Remove Connection",
            command=lambda: self._remove_connection_and_update(conn)
        )
        menu.tk_popup(event.x_root, event.y_root)

    def _remove_connection_and_update(self, conn):
        if conn in self.connections:
            self.connections.remove(conn)
            self.update_diagram()
            self.save_history()

    def _draw_parallel_lines(self, fx, fy, tx, ty, arrow1=False, arrow2=False, conn=None):
        """Draw two parallel lines between (fx,fy) and (tx,ty). Returns tuple of line ids."""
        import math
        dx = tx - fx
        dy = ty - fy
        length = math.hypot(dx, dy)
        if length == 0:
            return ()
        # Offset perpendicular to the line
        offset = 6
        ox = -dy / length * offset
        oy = dx / length * offset
        # First line
        line1 = self.canvas.create_line(
            fx + ox, fy + oy, tx + ox, ty + oy,
            width=2, fill="black",
            arrow=tk.LAST if arrow1 else None
        )
        # Second line
        line2 = self.canvas.create_line(
            fx - ox, fy - oy, tx - ox, ty - oy,
            width=2, fill="black",
            arrow=tk.FIRST if arrow2 else None
        )
        if conn:
            self._bind_line_context_menu(line1, conn)
            self._bind_line_context_menu(line2, conn)
        return (line1, line2)

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
                self.highlighted_node_id = node_id  # Highlight node for arrow drawing
                self.update_diagram()
                break

    def on_canvas_right_click(self, event):
        """Show context menu for node on right-click."""
        if not hasattr(self, "node_canvas_boxes"):
            return
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        for node_id, (x0, y0, x1, y1) in self.node_canvas_boxes.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                menu = tk.Menu(self.root, tearoff=0)
                menu.add_command(label="Rotate Orientation", command=lambda nid=node_id: self.rotate_node_orientation(nid))
                # --- BEGIN PATCH ---
                # Always show connection options if there is at least one other node
                other_nodes = [nid for nid in self.nodes if nid != node_id]
                if other_nodes:
                    connect_menu = tk.Menu(menu, tearoff=0)
                    from_id = self.selected_node_id if self.selected_node_id != node_id else None
                    # If no valid from_id, pick any other node as source
                    if not from_id:
                        from_id = other_nodes[0]
                    connect_menu.add_command(
                        label="Single Line",
                        command=lambda: self.add_connection(from_id, node_id, "single")
                    )
                    connect_menu.add_command(
                        label="Single Arrow →",
                        command=lambda: self.add_connection(from_id, node_id, "arrow")
                    )
                    connect_menu.add_command(
                        label="Double Line",
                        command=lambda: self.add_connection(from_id, node_id, "double")
                    )
                    connect_menu.add_command(
                        label="Double Line with Arrows ↔",
                        command=lambda: self.add_connection(from_id, node_id, "double_arrow")
                    )
                    menu.add_cascade(label="Draw connection to this node...", menu=connect_menu)
                # --- END PATCH ---
                menu.tk_popup(event.x_root, event.y_root)
                break

    def add_connection(self, from_id, to_id, line_type):
        for conn in self.connections:
            if conn["from"] == from_id and conn["to"] == to_id and conn["type"] == line_type:
                return
        self.connections.append({"from": from_id, "to": to_id, "type": line_type})
        self.update_diagram()
        self.save_history()

    def remove_connections(self, node_id):
        self.connections = [c for c in self.connections if c["from"] != node_id and c["to"] != node_id]
        self.update_diagram()
        self.save_history()

    def rotate_node_orientation(self, node_id):
        """Rotate orientation for interface/assembly node 90° clockwise."""
        node = self.nodes[node_id]
        orientations = ["TB", "LR", "BT", "RL"]
        current = node["attrs"].get("orientation", "TB")
        try:
            idx = orientations.index(current)
        except ValueError:
            idx = 0
        new_orientation = orientations[(idx + 1) % len(orientations)]
        node["attrs"]["orientation"] = new_orientation
        self.selected_node_id = node_id
        self.update_diagram()
        self.save_history()

    def on_canvas_press(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        for node_id, (x0, y0, x1, y1) in self.node_canvas_boxes.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                self.dragging_node_id = node_id
                self.selected_node_id = node_id
                node = self.nodes[node_id]
                attrs = node["attrs"]
                self.drag_offset = (x - x0, y - y0)
                self.drag_line = True
                break

    def on_canvas_drag(self, event):
        if not self.dragging_node_id:
            return
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        node_id = self.dragging_node_id
        node = self.nodes[node_id]
        attrs = node["attrs"]
        offset_x, offset_y = self.drag_offset
        attrs["manual_x"] = x - offset_x
        attrs["manual_y"] = y - offset_y
        node["attrs"] = attrs
        self.drag_line = True
        self.update_diagram()

    def on_canvas_release(self, event):
        if not self.dragging_node_id:
            return
        self.resolve_dragged_node_collision()
        self.drag_line = None
        self.update_diagram()
        self.save_history()
        self.dragging_node_id = None

    def resolve_dragged_node_collision(self):
        """If the dragged node overlaps with any other node, move it slightly until it doesn't."""
        if not self.dragging_node_id:
            return
        node_id = self.dragging_node_id
        node = self.nodes[node_id]
        attrs = node["attrs"]
        x = attrs.get("manual_x")
        y = attrs.get("manual_y")
        node_width = attrs.get("node_width", 100)
        node_height = attrs.get("node_height", 40)
        if x is None or y is None:
            return
        my_box = (x, y, x + node_width, y + node_height)
        for other_id, other in self.nodes.items():
            if other_id == node_id:
                continue
            oattrs = other["attrs"]
            ox = oattrs.get("manual_x")
            oy = oattrs.get("manual_y")
            owidth = oattrs.get("node_width", 100)
            oheight = oattrs.get("node_height", 40)
            if ox is not None and oy is not None:
                other_box = (ox, oy, ox + owidth, oy + oheight)
            else:
                continue
            if (my_box[2] > other_box[0] and my_box[0] < other_box[2] and
                my_box[3] > other_box[1] and my_box[1] < other_box[3]):
                step = 10
                while (my_box[2] > other_box[0] and my_box[0] < other_box[2] and
                       my_box[3] > other_box[1] and my_box[1] < other_box[3]):
                    x += step
                    y += step
                    my_box = (x, y, x + node_width, y + node_height)
                attrs["manual_x"] = x
                attrs["manual_y"] = y
                node["attrs"] = attrs

    def line_intersects_box(self, x1, y1, x2, y2, box):
        """Check if a line segment (x1, y1)-(x2, y2) intersects a rectangle box=(bx0, by0, bx1, by1)."""
        bx0, by0, bx1, by1 = box
        # Four sides of the box
        sides = [
            (bx0, by0, bx1, by0),  # top
            (bx1, by0, bx1, by1),  # right
            (bx1, by1, bx0, by1),  # bottom
            (bx0, by1, bx0, by0),  # left
        ]
        for sx1, sy1, sx2, sy2 in sides:
            if self.segments_intersect(x1, y1, x2, y2, sx1, sy1, sx2, sy2):
                return True
        return False

    def segments_intersect(self, x1, y1, x2, y2, x3, y3, x4, y4):
        """Check if line segments (x1,y1)-(x2,y2) and (x3,y3)-(x4,y4) intersect."""
        def ccw(a, b, c):
            return (c[1]-a[1]) * (b[0]-a[0]) > (b[1]-a[1]) * (c[0]-a[0])
        A, B, C, D = (x1, y1), (x2, y2), (x3, y3), (x4, y4)
        return (ccw(A, C, D) != ccw(B, C, D)) and (ccw(A, B, C) != ccw(A, B, D))

    def find_detour(self, start_x, start_y, end_x, end_y, from_id, to_id):
        """If a direct line collides with a node, add a waypoint to detour around it."""
        # Check for collision with all nodes except endpoints
        for node_id, box in self.node_canvas_boxes.items():
            if node_id in (from_id, to_id):
                continue
            if self.line_intersects_box(start_x, start_y, end_x, end_y, box):
                # Detour: go horizontally or vertically around the box
                bx0, by0, bx1, by1 = box
                # Try above
                if start_y < by0 and end_y < by0:
                    waypoint = (start_x, by0 - 10)
                    return [waypoint, (end_x, by0 - 10)]
                # Try below
                if start_y > by1 and end_y > by1:
                    waypoint = (start_x, by1 + 10)
                    return [waypoint, (end_x, by1 + 10)]
                # Try left
                if start_x < bx0 and end_x < bx0:
                    waypoint = (bx0 - 10, start_y)
                    return [waypoint, (bx0 - 10, end_y)]
                # Try right
                if start_x > bx1 and end_x > bx1:
                    waypoint = (bx1 + 10, start_y)
                    return [waypoint, (bx1 + 10, end_y)]
                # Default: simple dogleg
                waypoint = (start_x, end_y)
                return [waypoint]
        return []

root = tk.Tk()
root.state('zoomed')
app = DiagramApp(root)
root.mainloop()
