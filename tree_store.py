import uuid
import time

# This is the "branching version history" for an image. Every edit creates a
# new node with a link back to its parent, so you can always go back to an
# earlier version and branch off in a new direction, instead of only being
# able to undo in a straight line.


def new_session():
    return {}


def add_node(tree: dict, image, parent_id, instruction, explanation):
    node_id = str(uuid.uuid4())[:8]
    node = {
        "node_id": node_id,
        "parent_id": parent_id,
        "image": image,
        "instruction": instruction,
        "explanation": explanation,
        "children": [],
        "created_at": time.strftime("%H:%M:%S"),
    }
    tree[node_id] = node
    if parent_id is not None and parent_id in tree:
        tree[parent_id]["children"].append(node_id)
    return node


def render_tree_markdown(tree: dict, active_id: str) -> str:
    """Draws the tree as indented markdown text, bolding whichever node
    is currently selected/active."""
    if not tree:
        return "_No image uploaded yet._"

    roots = [n for n in tree.values() if n["parent_id"] is None]
    lines = []

    def walk(node_id, depth):
        node = tree[node_id]
        label = node["instruction"] if node["instruction"] else "original upload"
        text = f"[{node['node_id']}] {label}"
        if node_id == active_id:
            text = f"**-> {text}**"
        else:
            text = f"- {text}"
        lines.append("  " * depth + text)
        for child_id in node["children"]:
            walk(child_id, depth + 1)

    for root in roots:
        walk(root["node_id"], 0)

    return "\n".join(lines)


def node_choices(tree: dict):
    """Returns a list of strings for the dropdown, one per node."""
    choices = []
    for node in tree.values():
        label = node["instruction"] if node["instruction"] else "original upload"
        choices.append(f"{node['node_id']} - {label}")
    return choices


def node_id_from_choice(choice: str):
    if not choice:
        return None
    return choice.split(" - ")[0].strip()
