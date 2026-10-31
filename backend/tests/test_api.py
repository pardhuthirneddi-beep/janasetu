import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app import main


@pytest.fixture
def client(monkeypatch):
    # Isolated in-memory SQLite only; never touches the configured shared DATABASE_URL.
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    main.Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(main, "DB", factory)

    def override_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[main.get_db] = override_db
    with TestClient(main.app) as test_client:
        yield test_client
    main.app.dependency_overrides.clear()
    main.Base.metadata.drop_all(engine)
    engine.dispose()


def seed_user(client, role="citizen", open_id="test-user"):
    db = main.DB()
    user = main.User(open_id=open_id, display_name="Test", role=role)
    db.add(user)
    db.commit()
    user_id = user.id
    raw = "opaque-test-session-" + str(user_id)
    db.add(main.UserSession(token_hash=main.token_hash(raw), user_id=user_id, expires_at=main.now() + main.timedelta(hours=1)))
    db.commit()
    db.close()
    return {"webdev_app_session": raw}


def test_health_and_summary_are_local(client):
    assert client.get("/api/v1/health").json()["status"] == "ok"
    text = "Water stopped yesterday. I reported the leaking pipeline. Please restore the supply soon."
    assert main.local_extractive_summary(text) == main.local_extractive_summary(text)
    assert main.route_topic("There is a leaking tap", None) == "water"
    assert main.route_topic("anything", None) == "general"


def test_grievance_private_fields_not_visible_to_other_citizens(client):
    cookies = seed_user(client)
    response = client.post("/api/v1/grievances", cookies=cookies, json={"title": "Water supply issue", "narrative": "Water supply has stopped for three days on my street."})
    assert response.status_code == 201, response.text
    reference = response.json()["reference"]
    other = seed_user(client, open_id="other-user")
    assert client.get(f"/api/v1/grievances/{reference}", cookies=other).status_code == 404
    assert client.get("/api/v1/grievances/mine", cookies=cookies).json()["items"][0]["reference"] == reference


def test_status_transition_and_staff_note_access(client):
    citizen = seed_user(client)
    reference = client.post("/api/v1/grievances", cookies=citizen, json={"title": "Road pothole report", "narrative": "Large pothole at the road junction needs repair."}).json()["reference"]
    assert client.post(f"/api/v1/staff/grievances/{reference}/notes", cookies=citizen, json={"content": "secret"}).status_code == 403
    staff = seed_user(client, "staff", "staff-user")
    invalid = client.post(f"/api/v1/staff/grievances/{reference}/status", cookies=staff, json={"status": "closed", "public_update": "closed"})
    assert invalid.status_code == 409
    valid = client.post(f"/api/v1/staff/grievances/{reference}/status", cookies=staff, json={"status": "acknowledged", "public_update": "Received by JanSetu staff."})
    assert valid.status_code == 200 and valid.json()["status"] == "acknowledged"
    private = client.post(f"/api/v1/staff/grievances/{reference}/notes", cookies=staff, json={"content": "internal-only"})
    assert private.status_code == 201
    public = client.get(f"/api/v1/grievances/{reference}", cookies=citizen).json()
    assert "internalNotes" not in public and "internal-only" not in str(public)


def test_assistant_never_relays_question_or_nonpublic_evidence(client, monkeypatch):
    db = main.DB()
    document = main.KnowledgeDocument(title="Public water guidance", topic="water", source_url="https://example.test", is_public=True)
    db.add(document)
    db.flush()
    db.add(main.KnowledgeChunk(document_id=document.id, topic="water", content="Water utility contact process", is_public=True))
    private_document = main.KnowledgeDocument(title="Secret", topic="water", source_url="https://private.test", is_public=False)
    db.add(private_document)
    db.flush()
    db.add(main.KnowledgeChunk(document_id=private_document.id, topic="water", content="secret credential", is_public=False))
    db.commit()
    db.close()
    monkeypatch.setattr(main.settings, "manus_api_url", "")
    response = client.post("/api/v1/assistant", json={"question": "How can I contact water utility? My phone is 99999"})
    assert response.status_code == 200
    result = response.json()
    assert result["topic"] == "water" and len(result["evidence"]) == 1
    assert "phone" not in result["answer"].lower() and "private.test" not in str(result)


def test_public_status_and_action_report_exclude_private_details(client):
    citizen = seed_user(client, open_id="report-citizen")
    reference = client.post("/api/v1/grievances", cookies=citizen, json={"title": "Road surface repair", "narrative": "A broken road section needs attention."}).json()["reference"]
    staff = seed_user(client, "staff", "report-staff")
    changed = client.post(f"/api/v1/staff/grievances/{reference}/status", cookies=staff, json={"status": "acknowledged", "public_update": "Acknowledged by JanSetu staff."})
    assert changed.status_code == 200
    report = client.post(f"/api/v1/staff/grievances/{reference}/action-reports", cookies=staff, json={"outcome": "Inspected", "details": "private field notes", "public_summary": "JanSetu reviewed the details."})
    assert report.status_code == 201
    public = client.get(f"/api/v1/grievances/{reference}", cookies=citizen).json()
    assert public["statusHistory"][1]["actor"] == "JanSetu staff"
    assert public["statusHistory"][1]["publicUpdate"] == "Acknowledged by JanSetu staff."
    assert public["actionReports"][0]["publicSummary"] == "JanSetu reviewed the details."
    assert "private field notes" not in str(public) and "details" not in public["actionReports"][0]


def test_invalid_attachment_signature_is_rejected_before_storage(client):
    citizen = seed_user(client, open_id="file-owner")
    reference = client.post("/api/v1/grievances", cookies=citizen, json={"title": "Water interruption", "narrative": "The water line is interrupted."}).json()["reference"]
    response = client.post(f"/api/v1/grievances/{reference}/attachments", cookies=citizen, files={"file": ("spoof.pdf", b"not a PDF", "application/pdf")})
    assert response.status_code == 415


def test_independent_appeal_review_and_feedback_are_local(client):
    citizen = seed_user(client, open_id="appeal-citizen")
    reference = client.post("/api/v1/grievances", cookies=citizen, json={"title": "Streetlight repair", "narrative": "The streetlight is not working."}).json()["reference"]
    staff = seed_user(client, "staff", "appeal-staff")
    for status in ("acknowledged", "resolved"):
        response = client.post(f"/api/v1/staff/grievances/{reference}/status", cookies=staff, json={"status": status, "public_update": f"JanSetu status: {status}."})
        assert response.status_code == 200
    appeal = client.post(f"/api/v1/grievances/{reference}/appeals", cookies=citizen, json={"reason": "Please review this local JanSetu decision."})
    assert appeal.status_code == 201
    appeal_id = appeal.json()["id"]
    handler = seed_user(client, "admin", "appeal-admin")
    db = main.DB()
    handler_id = db.scalar(select(main.User).where(main.User.open_id == "appeal-admin")).id
    db.close()
    assigned = client.post(f"/api/v1/staff/grievances/{reference}/assign", cookies=handler, json={"staff_user_id": handler_id})
    assert assigned.status_code == 200
    conflict = client.post(f"/api/v1/staff/appeals/{appeal_id}/review", cookies=handler, json={"decision": "upheld", "note": "self-assigned review"})
    assert conflict.status_code == 403
    reviewer = seed_user(client, "reviewer", "appeal-reviewer")
    reviewed = client.post(f"/api/v1/staff/appeals/{appeal_id}/review", cookies=reviewer, json={"decision": "varied", "note": "Independent JanSetu review."})
    assert reviewed.status_code == 200 and reviewed.json()["decision"] == "varied"
    feedback = client.post(f"/api/v1/grievances/{reference}/feedback", cookies=citizen, json={"rating": 4, "comment": "The JanSetu steps were clear."})
    assert feedback.status_code == 201


def test_oauth_login_binds_callback_to_browser_origin_and_preview_cookie(client, monkeypatch):
    monkeypatch.setattr(main.settings, "manus_oauth_authorize_url", "https://oauth.example.test")
    monkeypatch.setattr(main.settings, "manus_oauth_client_id", "project-test-id")
    origin = "https://preview.example.test"
    response = client.get("/api/v1/auth/login", params={"origin": origin}, headers={"origin": origin}, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"].startswith("https://oauth.example.test/app-auth?")
    cookie = response.headers["set-cookie"].lower()
    assert "webdev_app_session" not in cookie and "jansetu_oauth_nonce=" in cookie
    assert "secure" in cookie and "samesite=none" in cookie
    from urllib.parse import parse_qs, urlparse
    query = parse_qs(urlparse(response.headers["location"]).query)
    assert query["redirectUri"] == [origin + "/api/v1/auth/callback"]


def test_managed_mysql_ssl_json_becomes_verified_pymysql_options():
    url, connect_args = main.normalize_database_url("mysql://user:secret@db.example.test/jansetudb?ssl=%7B%22rejectUnauthorized%22%3Atrue%7D")
    assert url.drivername == "mysql+pymysql"
    assert "ssl" not in url.query
    assert connect_args["ssl"]["verify_mode"] == "required"
    assert connect_args["ssl"]["check_hostname"] is True
    assert connect_args["ssl"]["ca"].endswith("cacert.pem")


def test_service_directory_api_returns_verified_source_metadata(client):
    db = main.DB()
    jurisdiction = main.Jurisdiction(name="Example review scope", level="source_scope")
    db.add(jurisdiction)
    db.flush()
    service = main.Service(slug="test-service", name="Test public service", category="Education", summary="A sourced example.", verification_status="partially_verified", jurisdiction_id=jurisdiction.id)
    db.add(service)
    db.flush()
    db.add(main.ServiceSource(service_id=service.id, title="Official service source", url="https://example.test/official", source_type="official"))
    db.commit()
    db.close()
    response = client.get("/api/v1/services?q=Test%20public%20service")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["verificationStatus"] == "partially_verified"
    assert items[0]["jurisdiction"] == "Example review scope"
    assert items[0]["sources"][0]["url"] == "https://example.test/official"
