import gradio as gr

from parser import parse_instruction
from editor import apply_tone_edit, remove_background, build_explanation
from tree_store import new_session, add_node, render_tree_markdown, node_choices, node_id_from_choice


def handle_upload(image):
    """Runs when the user drops in a new image. Starts a brand new tree."""
    if image is None:
        return {}, [], None, "_No image uploaded yet._", gr.update(choices=[], value=None)

    tree = new_session()
    root = add_node(tree, image, None, "", "Original uploaded image.")
    chat_history = [{
        "role": "assistant",
        "content": "Image uploaded. Tell me what you'd like to change, for example "
                    "'warm up the colours' or 'remove the background'.",
    }]
    choices = node_choices(tree)
    active_choice = f"{root['node_id']} - original upload"

    return (
        tree,
        chat_history,
        root["image"],
        render_tree_markdown(tree, root["node_id"]),
        gr.update(choices=choices, value=active_choice),
    )


def handle_instruction(instruction, tree_state, chat_history, active_choice):
    """Runs when the user submits an edit instruction."""
    if not tree_state:
        chat_history = chat_history + [{"role": "assistant", "content": "Please upload an image first."}]
        return tree_state, chat_history, None, "_No image uploaded yet._", gr.update(), ""

    if not instruction or not instruction.strip():
        return (
            tree_state,
            chat_history,
            None,
            render_tree_markdown(tree_state, node_id_from_choice(active_choice)),
            gr.update(),
            "",
        )

    parent_id = node_id_from_choice(active_choice)
    if parent_id not in tree_state:
        parent_id = list(tree_state.keys())[0]

    parent_node = tree_state[parent_id]
    chat_history = chat_history + [{"role": "user", "content": instruction}]

    try:
        parsed = parse_instruction(instruction)
    except Exception as e:
        chat_history = chat_history + [{"role": "assistant", "content": f"Could not reach the AI parser: {e}"}]
        return (
            tree_state,
            chat_history,
            parent_node["image"],
            render_tree_markdown(tree_state, parent_id),
            gr.update(),
            "",
        )

    op = parsed.get("op", "enhance")
    region = parsed.get("region", "full")
    params = parsed.get("params", {})
    source_image = parent_node["image"]

    try:
        if op == "remove_bg":
            new_image = remove_background(source_image)
        else:
            new_image = apply_tone_edit(source_image, params, region)
    except (Exception, SystemExit) as e:
        chat_history = chat_history + [{"role": "assistant", "content": f"Editing failed: {e}"}]
        return (
            tree_state,
            chat_history,
            source_image,
            render_tree_markdown(tree_state, parent_id),
            gr.update(),
            "",
        )

    explanation = build_explanation(op, region, params)
    new_node = add_node(tree_state, new_image, parent_id, instruction, explanation)
    chat_history = chat_history + [{"role": "assistant", "content": explanation}]

    choices = node_choices(tree_state)
    active_choice = f"{new_node['node_id']} - {instruction}"

    return (
        tree_state,
        chat_history,
        new_image,
        render_tree_markdown(tree_state, new_node["node_id"]),
        gr.update(choices=choices, value=active_choice),
        "",
    )


def handle_branch_select(active_choice, tree_state):
    """Runs when the user picks a different node from the dropdown, to
    branch off from an earlier version instead of the latest one."""
    if not tree_state or not active_choice:
        return None, "_No image uploaded yet._"
    node_id = node_id_from_choice(active_choice)
    if node_id not in tree_state:
        return None, render_tree_markdown(tree_state, None)
    node = tree_state[node_id]
    return node["image"], render_tree_markdown(tree_state, node_id)


with gr.Blocks(title="AI Image Editor") as demo:
    gr.Markdown("# AI Image Editor with Branching Edit History")
    gr.Markdown(
        "Upload an image, then describe edits in plain English. "
        "Every edit creates a new branch in the tree below, so you can always go back "
        "and try something different from any earlier version, not just undo in a straight line."
    )

    tree_state = gr.State({})

    with gr.Row():
        with gr.Column(scale=1):
            image_input = gr.Image(type="pil", label="Upload image")
            current_image = gr.Image(type="pil", label="Current version", interactive=False)
            branch_dropdown = gr.Dropdown(label="Branch from node", choices=[], interactive=True)
            tree_view = gr.Markdown("_No image uploaded yet._", label="Edit tree")

        with gr.Column(scale=1):
            chatbot = gr.Chatbot(label="Edit conversation", height=400)
            instruction_box = gr.Textbox(
                label="Describe your edit",
                placeholder="e.g. warm up the colours, remove the background, make the sky more dramatic",
            )
            send_button = gr.Button("Apply edit", variant="primary")

    image_input.change(
        handle_upload,
        inputs=[image_input],
        outputs=[tree_state, chatbot, current_image, tree_view, branch_dropdown],
    )

    send_button.click(
        handle_instruction,
        inputs=[instruction_box, tree_state, chatbot, branch_dropdown],
        outputs=[tree_state, chatbot, current_image, tree_view, branch_dropdown, instruction_box],
    )

    instruction_box.submit(
        handle_instruction,
        inputs=[instruction_box, tree_state, chatbot, branch_dropdown],
        outputs=[tree_state, chatbot, current_image, tree_view, branch_dropdown, instruction_box],
    )

    branch_dropdown.change(
        handle_branch_select,
        inputs=[branch_dropdown, tree_state],
        outputs=[current_image, tree_view],
    )

if __name__ == "__main__":
    demo.launch()
