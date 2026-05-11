from pathlib import Path

from core.settings import settings

service_dir = getattr(settings, "root_dir", Path(__file__).resolve().parents[2]) / "service"

public_dir = service_dir / 'public'

upload_dir = public_dir / 'uploads'
