from pathlib import Path


def test_static_dashboard_assets_exist() -> None:
    dashboard_dir = Path("static/dashboard")

    assert (dashboard_dir / "index.html").is_file()
    assert (dashboard_dir / "styles.css").is_file()
    assert (dashboard_dir / "app.js").is_file()


def test_static_dashboard_is_wired_to_real_api_endpoints() -> None:
    app_js = Path("static/dashboard/app.js").read_text()
    index_html = Path("static/dashboard/index.html").read_text()

    assert "Run Full Judge Demo" in index_html
    assert "/simulate-crisis" in app_js
    assert "/optimize-response?mode=quantum_inspired" in app_js
    assert "/generate-plan" in app_js
    assert "/incidents" in app_js
    assert "runFullJudgeDemo" in app_js
