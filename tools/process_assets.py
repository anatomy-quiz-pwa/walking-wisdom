from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
GEN = Path("/Users/baobaoc/.codex/generated_images/019dd95f-5660-7581-9602-bcd818b38d0f")

WORLD_SRC = GEN / "ig_03f979aece1424290169f21184569c8191aa5f7ce88ed1b84f.png"
CAFE_SRC = GEN / "ig_03f979aece1424290169f211d74c108191b19c320bbaf0095f.png"
PLAYER_SRC = GEN / "ig_03f979aece1424290169f2122fd108819194baccab55c71260.png"
NPC_SRC = GEN / "ig_03f979aece1424290169f212813a0c8191bbf748f459f483ab.png"
BOOKSHELF_SRC = GEN / "ig_03f979aece1424290169f212c9ba3c8191ba9fe91c79ff25f5.png"

MASTERS = ["lieberman", "cavagna", "roberts", "perry", "bernstein", "studenski"]


def resize_cover(src: Path, dst: Path, size=(1024, 768)) -> None:
    img = Image.open(src).convert("RGBA")
    scale = max(size[0] / img.width, size[1] / img.height)
    resized = img.resize((round(img.width * scale), round(img.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - size[0]) // 2
    top = (resized.height - size[1]) // 2
    resized.crop((left, top, left + size[0], top + size[1])).save(dst)


def magenta_to_alpha(img: Image.Image, tolerance=58) -> Image.Image:
    img = img.convert("RGBA")
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if r > 180 and b > 150 and g < 100 and abs(r - b) < tolerance:
                px[x, y] = (r, g, b, 0)
    return img


def trim_alpha(img: Image.Image, padding=6) -> Image.Image:
    alpha = img.getchannel("A")
    box = alpha.getbbox()
    if not box:
        return img
    left = max(0, box[0] - padding)
    top = max(0, box[1] - padding)
    right = min(img.width, box[2] + padding)
    bottom = min(img.height, box[3] + padding)
    return img.crop((left, top, right, bottom))


def split_grid(src: Path, out_dir: Path, names: list[str], cols: int, rows: int, trim=True) -> None:
    img = magenta_to_alpha(Image.open(src))
    cell_w = img.width // cols
    cell_h = img.height // rows
    for i, name in enumerate(names):
        col = i % cols
        row = i // cols
        cell = img.crop((col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h))
        if trim:
            cell = trim_alpha(cell)
        cell.save(out_dir / f"{name}.png")


def process_player(src: Path, dst: Path) -> None:
    img = magenta_to_alpha(Image.open(src))
    # Crop to the generated 4x4 sheet bounds, preserving equal cells.
    alpha_box = img.getchannel("A").getbbox()
    if alpha_box:
        left, top, right, bottom = alpha_box
        pad = 24
        left = max(0, left - pad)
        top = max(0, top - pad)
        right = min(img.width, right + pad)
        bottom = min(img.height, bottom + pad)
        w = right - left
        h = bottom - top
        cell = max(w // 4, h // 4)
        cx = (left + right) // 2
        cy = (top + bottom) // 2
        size = cell * 4
        left = max(0, cx - size // 2)
        top = max(0, cy - size // 2)
        img = img.crop((left, top, left + size, top + size))
    sheet = img.resize((256, 256), Image.Resampling.NEAREST)
    sheet.save(dst)
    frames_dir = dst.parent / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    for row in range(4):
        for col in range(4):
            frame = sheet.crop((col * 64, row * 64, (col + 1) * 64, (row + 1) * 64))
            frame.save(frames_dir / f"traveler_{row}_{col}.png")


def process_bookshelf(src: Path, out_dir: Path) -> None:
    img = magenta_to_alpha(Image.open(src))
    cell_w = img.width // 7
    for i in range(7):
        cell = img.crop((i * cell_w, 0, (i + 1) * cell_w, img.height))
        cell = trim_alpha(cell, padding=4)
        target_h = 176
        scale = target_h / cell.height
        resized = cell.resize((round(cell.width * scale), target_h), Image.Resampling.NEAREST)
        name = "bookshelf-empty.png" if i == 0 else f"bookshelf-books-{i}.png"
        resized.save(out_dir / name)


def main() -> None:
    resize_cover(WORLD_SRC, ROOT / "assets/maps/world-map.png")
    resize_cover(CAFE_SRC, ROOT / "assets/maps/cafe-base.png")
    resize_cover(CAFE_SRC, ROOT / "assets/maps/cafe-layered-preview.png")
    process_player(PLAYER_SRC, ROOT / "assets/sprites/player/traveler-walk-4x4.png")
    split_grid(NPC_SRC, ROOT / "assets/sprites/masters", MASTERS, cols=3, rows=2)
    process_bookshelf(BOOKSHELF_SRC, ROOT / "assets/sprites/props")


if __name__ == "__main__":
    main()
