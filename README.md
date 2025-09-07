<img src="images/Logical_View.png" />
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

# Diagram Assistant

**Diagram Assistant** is an interactive node diagram editor built with Tkinter. It lets you create, edit, and visualize hierarchical diagrams with ease.

## Features

- Add/delete nodes to build hierarchies
- Change node color, shape, orientation, and size
- Undo/redo actions
- Edit node label and style
- Export diagram as PNG
- Save/load diagrams

## Getting Started

1. **Install Requirements**  
   Make sure you have Python 3 and [Pillow](https://pypi.org/project/Pillow/) installed:
   ```sh
   pip install pillow
   ```

2. **Run the Script**  
   Open a terminal and run:
   ```sh
   python diagram_assistant.py
   ```

## Usage

### Building Your Diagram

- **Add Child Node:**  
  Select a node (or the root) in the tree on the left, then click **Add Child** to add a new child node.

- **Delete Node:**  
  Select a node and click **Delete Node** to remove it (root cannot be deleted).

### Customizing Nodes

- **Change Color:**  
  Select a node, click **Pick** next to "Node Color" and choose a color.

- **Change Shape:**  
  Use the **Shape** dropdown to select shapes like ellipse, box, record, diamond, etc.

- **Change Orientation:**  
  Use the **Orientation** dropdown to switch between Top-Bottom (TB), Left-Right (LR), or Right-Left (RL) layouts.

- **Edit Label & Size:**  
  Double-click a node in the tree to open a dialog where you can change its label, font size/style, width, and height.

### Undo/Redo

- Click **Undo** or **Redo** to revert or reapply changes.
- Keyboard shortcuts:  
  - Undo: `Ctrl+Z`  
  - Redo: `Ctrl+Y`

### Center Diagram

- Click **Center** to center the diagram in the canvas view.

### Save/Load Diagram

- Use the **File** menu to **Save** your diagram to a `.diagram` file or **Load** a previously saved diagram.

### Export as PNG

- Use **File > Export as PNG** to save your diagram as a PNG image.

## Example Workflow

1. Run the script.
2. Click "Add Child" to add nodes under "Root".
3. Select nodes to change color, shape, or orientation.
4. Double-click nodes to edit their label and size.
5. Use Undo/Redo as needed.
6. Save your diagram or export it as PNG.



---

Enjoy creating beautiful hierarchical diagrams!
