from api.http import create_app
from core.mock_controller import MockController
from core.system_controller import SystemController


def main():
    controller = MockController()
    # controller = SystemController()
    app = create_app(controller)

    try:
        import uvicorn
    except Exception as exc:
        raise RuntimeError("uvicorn is required to run the server directly") from exc

    uvicorn.run(app, host="localhost", port=8000)


if __name__ == "__main__":
    main()