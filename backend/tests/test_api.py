"""API tests: auth + RBAC, simulation, traffic, emergency safe transition."""


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_health_no_auth(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["sumo_available"] is False  # SUMO not installed in this VM


def test_unauthenticated_blocked(client):
    r = client.get("/api/dashboard/summary")
    assert r.status_code == 401
    r = client.get("/api/junctions")
    assert r.status_code == 401


def test_login_wrong_password(client):
    r = client.post("/api/auth/login", json={"email": "admin@smartflow.local", "password": "wrong"})
    assert r.status_code == 401


def test_me_returns_role(client, admin_token):
    r = client.get("/api/auth/me", headers=auth_headers(admin_token))
    assert r.status_code == 200
    assert r.json()["role"] == "ADMIN"


def test_viewer_cannot_edit_settings(client, viewer_token):
    r = client.put("/api/admin/settings", json={"green_max_s": 50}, headers=auth_headers(viewer_token))
    assert r.status_code == 403
    r = client.get("/api/dashboard/summary", headers=auth_headers(viewer_token))
    assert r.status_code == 200  # viewer CAN read


def test_admin_can_edit_settings(client, admin_token):
    r = client.put("/api/admin/settings", json={"green_max_s": 55}, headers=auth_headers(admin_token))
    assert r.status_code == 200
    assert r.json()["green_max_s"] == 55
    # restore default
    client.put("/api/admin/settings", json={"green_max_s": 60}, headers=auth_headers(admin_token))


def test_simulation_start_and_dashboard(client, admin_token):
    h = auth_headers(admin_token)
    r = client.post("/api/simulation/start", json={"scenario": "rush", "engine": "simulated"}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["engine_source"] == "simulated"
    r = client.get("/api/dashboard/summary", headers=h)
    assert r.status_code == 200
    assert r.json()["source"] == "simulated"
    assert r.json()["scenario"] == "rush"
    assert r.json()["active_junctions"] == 4
    r = client.get("/api/junctions", headers=h)
    assert len(r.json()) == 4
    client.post("/api/simulation/pause", headers=h)


def test_sumo_start_blocked_with_clear_reason(client, admin_token):
    r = client.post("/api/simulation/start", json={"scenario": "normal", "engine": "sumo"},
                    headers=auth_headers(admin_token))
    assert r.status_code == 503
    assert "SUMO" in r.json()["detail"]


def test_traffic_inject_density(client, admin_token):
    h = auth_headers(admin_token)
    r = client.post("/api/traffic/inject",
                    json={"junction_id": "J1", "approach": "N", "vehicle_count": 20,
                          "queue_length": 10, "avg_wait_s": 30.0, "source": "test"},
                    headers=h)
    assert r.status_code == 201, r.text
    assert r.json()["density"] == 17.0  # 0.5*10 + 0.3*20 + 0.2*30
    assert r.json()["recommended_green_s"] == 23.6  # 10 + 0.8*17
    r = client.get("/api/traffic/current", headers=h)
    assert r.status_code == 200
    assert any(x["junction_id"] == "J1" for x in r.json()["recent_readings"])


def test_emergency_safe_transition(client, admin_token):
    h = auth_headers(admin_token)
    r = client.post("/api/emergencies",
                    json={"ambulance_id": "AMB-01", "current_junction": "J1",
                          "destination_junction": "J2", "route": ["J1", "J2"]}, headers=h)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "PRIORITY_GRANTED"
    # Safe walk must include yellow + all-red (unless already on that green).
    assert "YELLOW_NS" in body["safe_transition_steps"] or "YELLOW_EW" in body["safe_transition_steps"]
    assert "ALL_RED" in body["safe_transition_steps"]
    assert body["gps_source"] == "SIMULATED GPS"
    eid = body["id"]
    r = client.post(f"/api/emergencies/{eid}/location",
                    json={"junction_id": "J2", "progress": 0.9}, headers=h)
    assert r.status_code == 200
    assert r.json()["current_junction"] == "J2"
    r = client.post(f"/api/emergencies/{eid}/complete", headers=h)
    assert r.status_code == 200
    assert r.json()["status"] == "COMPLETED"
    # Events persisted
    r = client.get("/api/events?type=EMERGENCY_REQUESTED", headers=h)
    assert r.status_code == 200 and len(r.json()) >= 1


def test_emergency_invalid_route_rejected(client, admin_token):
    r = client.post("/api/emergencies",
                    json={"ambulance_id": "AMB-02", "current_junction": "J1",
                          "destination_junction": "J9", "route": ["J1", "J9"]},
                    headers=auth_headers(admin_token))
    assert r.status_code == 422


def test_analytics_summary_and_comparison_planned(client, admin_token):
    h = auth_headers(admin_token)
    r = client.get("/api/analytics/summary", headers=h)
    assert r.status_code == 200
    assert "mean_wait_s" in r.json()
    r = client.get("/api/analytics/comparison", headers=h)
    assert r.json()["status"] == "planned"  # no experiment runs yet — nothing invented
