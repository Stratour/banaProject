"""
Convert static page images to WebP and resize to 2× display dimensions.
Run once: python manage.py optimize_images
"""
from pathlib import Path
from django.core.management.base import BaseCommand
from PIL import Image

IMAGES = [
    # (source_filename, max_width, max_height)
    ("home_entraide.jpg", 1344, 756),
    ("home_yaya.jpg", 1152, 1200),
    ("home_card_trust.jpg", 1152, 768),  # landscape source, portrait display via object-cover
]

IMG_DIR = Path(__file__).resolve().parents[3] / "bana" / "static" / "bana" / "img" / "page"


class Command(BaseCommand):
    help = "Convert page images to WebP and resize to 2× display dimensions"

    def handle(self, *args, **options):
        for filename, max_w, max_h in IMAGES:
            src = IMG_DIR / filename
            if not src.exists():
                self.stdout.write(self.style.WARNING(f"Not found: {src}"))
                continue

            dst = src.with_suffix(".webp")
            with Image.open(src) as img:
                img = img.convert("RGB")
                img.thumbnail((max_w, max_h), Image.LANCZOS)
                img.save(dst, "WEBP", quality=82, method=6)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{filename} → {dst.name}  ({img.width}×{img.height}, {dst.stat().st_size // 1024} KB)"
                    )
                )
