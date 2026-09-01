from pathlib import Path


def test_service_worker_forces_open_home_screen_clients_to_refresh_on_update():
    sw = Path('public/sw.js').read_text()
    assert "self.clients.matchAll({type:'window',includeUncontrolled:true})" in sw
    assert '.navigate(' in sw
    assert "cache:'no-store'" in sw
