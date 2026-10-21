"""Settings API: partial updates keep the fields they don't mention."""


async def test_partial_settings_update_keeps_timeout(client):
    await client.put("/api/settings/settings", json={"http_timeout": 30, "auto_detect_shorts": True})
    await client.put("/api/settings/settings", json={"auto_detect_shorts": False})
    data = (await client.get("/api/settings/settings")).json()
    assert data["http_timeout"] == 30.0
    assert data["auto_detect_shorts"] is False
