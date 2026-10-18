from django.core.cache import cache

from core.forms import MAX_FAILURES

LOGIN = "/admin/login/"


def log_in(client, password, ip="203.0.113.7"):
    data = {"username": "lea", "password": password, "next": "/admin/"}
    return client.post(LOGIN, data, secure=True, HTTP_FLY_CLIENT_IP=ip)


def test_failed_logins_block_the_ip_even_for_the_right_password(client, lead):
    cache.clear()
    for _ in range(MAX_FAILURES):
        assert log_in(client, "wrong").status_code == 200  # form re-rendered with an error
    blocked = log_in(client, "x")
    assert blocked.status_code == 200 and "Too many failed logins" in blocked.content.decode()
    assert log_in(client, "x", ip="198.51.100.2").status_code == 302  # another IP still works


def test_csp_blocks_inline_and_foreign_scripts(client, db):
    csp = client.get(LOGIN, secure=True)["Content-Security-Policy"]
    script_src = next(d for d in csp.split("; ") if d.startswith("script-src"))
    assert script_src == "script-src 'self' 'unsafe-eval'"  # no 'unsafe-inline', no CDNs
    assert "frame-ancestors 'none'" in csp and "object-src 'none'" in csp
