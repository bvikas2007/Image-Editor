# AI Image Editor (Gradio version)

This is a working starter build of the project from your roadmap chat. It covers:

- Image upload
- Chat style instructions in plain English
- An LLM that turns instructions into structured edit commands (tone, remove background, enhance)
- Real Pillow based tone/colour editing (warmth, contrast, saturation, brightness), with a basic sky region
- AI background removal using rembg
- A real branching edit tree, shown as an indented list, with a dropdown so you can branch off any earlier version, not just the latest one

## Files

- `app.py` — the Gradio app itself, run this file
- `parser.py` — talks to the free Groq LLM to turn instructions into JSON
- `editor.py` — does the actual image editing
- `tree_store.py` — stores and renders the branching edit history
- `requirements.txt` — the list of packages to install

## Setup, step by step

### 1. Install Python

If you do not already have it, install Python 3.10 or newer from python.org. During install on Windows, tick the box that says "Add Python to PATH".

### 2. Open a terminal in this folder

On Windows, open the folder in File Explorer, then type `cmd` in the address bar and press Enter. On Mac, right click the folder and choose "New Terminal at Folder" (or open Terminal and `cd` into the folder).

### 3. Install the required packages

Run this command:

```
pip install -r requirements.txt
```

This will take a few minutes the first time, especially rembg since it downloads a small AI model the first time you use it.

### 4. Get a free Groq API key

Go to console.groq.com, sign up for free, and create an API key. This is what powers the "understand my instruction" part of the app. It costs nothing and the free tier is generous enough for this project.

### 5. Set the API key

**On Mac or Linux**, in your terminal:
```
export GROQ_API_KEY="your-key-here"
```

**On Windows (Command Prompt)**:
```
set GROQ_API_KEY=your-key-here
```

**On Windows (PowerShell)**:
```
$env:GROQ_API_KEY="your-key-here"
```

Do this every time you open a new terminal, or look up how to set a permanent environment variable on your system.

### 6. Run the app

```
python app.py
```

A link like `http://127.0.0.1:7860` will appear in the terminal. Open it in your browser.

## How to use it

1. Upload an image using the box on the left.
2. Type an instruction in the text box, for example:
   - "warm up the colours"
   - "make the sky more dramatic"
   - "remove the background"
   - "make it darker and less saturated"
3. Press Enter or click "Apply edit". The edited image appears, and a new entry shows up in the tree.
4. To branch off an earlier version instead of the latest one, pick it from the "Branch from node" dropdown, then type a new instruction. This creates a second branch from that point, so nothing you have made gets overwritten or lost.

## What to build next, based on your original roadmap

- **Optional extra ops**: sharpening, inpainting, or style transfer, following the same pattern as `apply_tone_edit` in `editor.py`.
- **Tree visualization upgrade**: right now the tree is shown as indented markdown text. If you want the visual graph version mentioned in your original chat, you can inject a small vis.js snippet using `gr.HTML()` instead of `gr.Markdown()` in `app.py`.
- **Latency logging**: wrap each edit call in `time.time()` before and after, and print or log the duration, this is useful for your technical report.
- **Demo recording**: once this is working, record a 2 to 3 minute screen capture showing an upload, two edits, then a branch from an earlier node, using OBS or Loom, both free.

## Troubleshooting

- **"GROQ_API_KEY environment variable is not set"**: you skipped step 5, or opened a new terminal without repeating it.
- **"No onnxruntime backend found" or the app crashes when you try to remove a background**: run `pip install onnxruntime` on its own, then restart the app. This is now also listed in `requirements.txt`, but if you installed dependencies before this fix, you'll need to run it manually once.
- **rembg is slow the first time you remove a background**: this is normal, it is downloading a ~176MB model file the first time it runs. It will be fast on every run after that.
- **`Chatbot.__init__() got an unexpected keyword argument 'type'`**: this means you have a newer Gradio version (6.x) that removed the `type` argument since it now uses the message format by default. This is already fixed in the current `app.py`.
- **The parser gives a weird result**: the fallback in `parser.py` will apply a small generic enhancement rather than crash, so the app keeps working even if the LLM output is not perfectly formed JSON.
