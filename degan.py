import os
import re
import math
from functools import reduce
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# ---------- Utilities parser ----------
BOX_CHARS = set(" \t│├└┬┴┤┐┌┘┼─")

def _leading_prefix_len(s: str) -> int:
    """Hitung panjang prefix yang hanya berisi spasi/box chars."""
    i = 0
    while i < len(s) and s[i] in BOX_CHARS:
        i += 1
    return i

def _gcd_list(nums):
    if not nums:
        return 0
    return reduce(math.gcd, nums)

def parse_structure_to_nodes(structure_text: str):
    """
    Kembalikan list of nodes: each node = dict {
      raw: original trimmed line,
      prefix_len: length of leading box chars,
      name: cleaned name (no leading '/', no trailing comment),
      is_dir: boolean,
    }
    """
    nodes = []
    lines = structure_text.splitlines()
    prefix_lengths = []

    for raw in lines:
        raw = raw.rstrip()
        if not raw.strip():
            continue

        prefix_len = _leading_prefix_len(raw)
        name_part = raw[prefix_len:].strip()

        # Hapus leading box/dash chars jika masih ada (mis: "├── __init__.py")
        name_part = re.sub(r'^[\s\-\u2500\u2502\u251C\u2514\u2510\u250C\u2518\u253C]+', '', name_part)

        # Hapus komentar
        if '#' in name_part:
            name_part = name_part.split('#', 1)[0].strip()

        if not name_part:
            continue

        # Tandai directory bila line raw diakhiri '/' atau name sendiri diakhiri '/'
        is_dir = raw.strip().endswith('/') or name_part.endswith('/')

        # Hilangkan leading slash pada nama (agar jadi relatif)
        if name_part.startswith('/'):
            name_part = name_part[1:]

        # Simpan
        nodes.append({
            "raw": raw,
            "prefix_len": prefix_len,
            "name": name_part,
            "is_dir": is_dir,
        })

        if prefix_len > 0:
            prefix_lengths.append(prefix_len)

    # Tentukan indent unit (gcd dari prefix lengths). fallback 4
    indent_unit = _gcd_list(prefix_lengths) if prefix_lengths else 0
    if indent_unit < 2:
        indent_unit = 4

    # Hitung depth untuk tiap node
    for n in nodes:
        n["depth"] = (n["prefix_len"] // indent_unit) if indent_unit else 0

    return nodes

# ---------- Create files / folders ----------
def create_from_structure(base_path: str, structure_text: str):
    nodes = parse_structure_to_nodes(structure_text)
    if not nodes:
        raise ValueError("Tidak ada baris struktur yang valid ditemukan.")

    created_dirs = []
    created_files = []
    stack = []

    for i, node in enumerate(nodes):
        depth = node["depth"]
        name = node["name"]
        is_dir = node["is_dir"]

        # Pastikan stack sesuai depth (root berada di depth 0)
        while len(stack) > depth:
            stack.pop()

        stack.append(name)

        # Build relative path by joining stack items (strip trailing slashes on parts)
        rel_parts = [p.rstrip('/') for p in stack if p != ""]
        rel_path = os.path.join(*rel_parts) if rel_parts else ""

        target_path = os.path.join(base_path, rel_path)

        if is_dir:
            os.makedirs(target_path, exist_ok=True)
            created_dirs.append(target_path)
        else:
            parent = os.path.dirname(target_path)
            if parent and not os.path.exists(parent):
                os.makedirs(parent, exist_ok=True)
                created_dirs.append(parent)
            # Create file if not exists. For __init__.py write a tiny comment to avoid empty package file ambiguity.
            if not os.path.exists(target_path):
                try:
                    with open(target_path, "w", encoding="utf-8") as f:
                        if os.path.basename(name) == "__init__.py":
                            f.write("# auto-generated __init__\n")
                        else:
                            f.write("")
                    created_files.append(target_path)
                except Exception as e:
                    # re-raise with context
                    raise RuntimeError(f"Gagal membuat file {target_path}: {e}")

    return created_dirs, created_files

# ---------- GUI ----------
def browse_path():
    folder = filedialog.askdirectory()
    if folder:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, folder)

def generate():
    base_path = entry_path.get().strip()
    structure_text = text_structure.get("1.0", tk.END).rstrip()

    log_text.delete("1.0", tk.END)

    if not base_path:
        messagebox.showerror("Error", "Pilih path project terlebih dahulu.")
        return
    if not structure_text.strip():
        messagebox.showerror("Error", "Masukkan struktur project.")
        return

    try:
        created_dirs, created_files = create_from_structure(base_path, structure_text)
        msg = f"Sukses!\nFolders dibuat: {len(created_dirs)}\nFiles dibuat: {len(created_files)}"
        messagebox.showinfo("Selesai", msg)

        log_text.insert(tk.END, "=== Direktori dibuat ===\n")
        for d in created_dirs:
            log_text.insert(tk.END, d + "\n")
        log_text.insert(tk.END, "\n=== File dibuat ===\n")
        for f in created_files:
            log_text.insert(tk.END, f + "\n")

    except Exception as e:
        messagebox.showerror("Error saat generate", str(e))
        log_text.insert(tk.END, "ERROR: " + str(e) + "\n")

root = tk.Tk()
root.title("Project Structure Generator - DEGAN")
root.geometry("820x700")

# Path frame
frame_path = tk.Frame(root)
frame_path.pack(fill="x", padx=10, pady=8)
tk.Label(frame_path, text="Base Path:").pack(side="left")
entry_path = tk.Entry(frame_path, width=70)
entry_path.pack(side="left", padx=8)
tk.Button(frame_path, text="Browse", command=browse_path).pack(side="left")

# Struktur input
tk.Label(root, text="Masukkan struktur (salin tree ASCII Anda):").pack(anchor="w", padx=10)
text_structure = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=25)
text_structure.pack(fill="both", expand=False, padx=10, pady=6)

# Tombol
btn_frame = tk.Frame(root)
btn_frame.pack(fill="x", padx=10, pady=6)
tk.Button(btn_frame, text="Generate Struktur", command=generate, bg="#4CAF50", fg="white", width=18).pack(side="left")

# Log output
tk.Label(root, text="Log:").pack(anchor="w", padx=10, pady=(6,0))
log_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=12, state=tk.NORMAL)
log_text.pack(fill="both", expand=True, padx=10, pady=(0,10))

root.mainloop()
