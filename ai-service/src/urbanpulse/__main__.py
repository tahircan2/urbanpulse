"""
python -m urbanpulse — Run the UrbanPulse AI service.
"""
import uvicorn
from urbanpulse.core.config import get_settings


def main() -> None:
    s = get_settings()
    uvicorn.run(
        "urbanpulse.api.app:app",
        host=s.service_host,
        port=s.service_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
