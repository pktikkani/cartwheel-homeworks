import pytest
from fastapi import HTTPException

import server.app as server_app


def test_create_session_rejects_role_mismatch(
    world: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(server_app, "_SESSIONS", {})

    with pytest.raises(HTTPException) as error:
        server_app.create_session(
            server_app.SessionCreate(user_id=9002, role="shopper")
        )

    assert error.value.status_code == 403
    assert server_app._SESSIONS == {}


def test_token_cannot_authorize_another_session(
    world: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(server_app, "_SESSIONS", {})
    first = server_app.create_session(
        server_app.SessionCreate(user_id=1, role="shopper")
    )
    second = server_app.create_session(
        server_app.SessionCreate(user_id=2, role="shopper")
    )
    authorization = f"Bearer {first['token']}"

    assert server_app._authorize(first["session_id"], authorization).user_id == 1
    with pytest.raises(HTTPException) as error:
        server_app._authorize(second["session_id"], authorization)

    assert error.value.status_code == 403
