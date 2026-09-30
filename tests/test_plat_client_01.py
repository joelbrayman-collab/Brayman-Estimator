"""PLAT-CLIENT-01: an existing client can be opened and corrected."""

from app import create_app, db
from app.models import Client, Estimate, Project, Proposal, ProposalTemplate
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from tests.auth_fixtures import ensure_office_user, login_office_user


def _app():
    return create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-plat-client-01",
            "WTF_CSRF_ENABLED": False,
        }
    )


def _office(application):
    ensure_default_organization()
    ensure_office_user()
    http = application.test_client()
    login_office_user(http)
    return http


def test_existing_client_opens_with_stored_fields():
    application = _app()
    with application.app_context():
        db.create_all()
        http = _office(application)
        client = Client(
            name="Maple Client",
            company="Maple Co",
            email="maple@example.com",
            phone="613-555-0101",
            address="1 Maple Street",
            notes="Call before arrival",
            organization_id=DEFAULT_ORGANIZATION_ID,
        )
        db.session.add(client)
        db.session.commit()
        client_id = client.id
        page = http.get(f"/clients/{client_id}")
        listed = http.get("/clients/").get_data(as_text=True)
        html = page.get_data(as_text=True)
        db.session.remove()
        db.drop_all()
    assert page.status_code == 200
    assert 'value="Maple Client"' in html
    assert 'value="Maple Co"' in html
    assert 'value="maple@example.com"' in html
    assert 'value="613-555-0101"' in html
    assert 'value="1 Maple Street"' in html
    assert "Call before arrival" in html
    assert f'href="/clients/{client_id}"' in listed


def test_correction_persists_without_changing_identity_or_relations():
    application = _app()
    with application.app_context():
        db.create_all()
        http = _office(application)
        client = Client(
            name="Oak Client",
            company="Oak Co",
            email="oak@example.com",
            phone="613-555-0102",
            address="2 Oak Road",
            notes="Original note",
            organization_id=DEFAULT_ORGANIZATION_ID,
        )
        other = Client(
            name="Pine Client",
            company="Pine Co",
            organization_id=DEFAULT_ORGANIZATION_ID,
        )
        db.session.add_all([client, other])
        db.session.flush()
        project = Project(
            name="Oak House",
            client_id=client.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            status="Lead",
        )
        db.session.add(project)
        db.session.flush()
        estimate = Estimate(
            organization_id=DEFAULT_ORGANIZATION_ID,
            project_id=project.id,
            estimate_number="EST-OAK",
            title="Oak estimate",
        )
        template = ProposalTemplate(
            organization_id=DEFAULT_ORGANIZATION_ID,
            name="Oak template",
        )
        db.session.add_all([estimate, template])
        db.session.flush()
        proposal = Proposal(
            organization_id=DEFAULT_ORGANIZATION_ID,
            proposal_number="P-OAK",
            estimate_id=estimate.id,
            proposal_template_id=template.id,
            title="Oak proposal",
            client_name="Oak Client",
            project_name="Oak House",
            estimate_number="EST-OAK",
            estimate_version_number=1,
        )
        db.session.add(proposal)
        db.session.commit()
        client_id = client.id
        created_at = client.created_at
        project_id = project.id
        proposal_id = proposal.id

        saved = http.post(
            f"/clients/{client_id}",
            data={
                "name": "Oak Client Revised",
                "company": "Oak Company",
                "email": "revised@example.com",
                "phone": "613-555-0199",
                "address": "9 Revised Lane",
                "notes": "Updated note",
            },
        )
        listed = http.get("/clients/").get_data(as_text=True)
        reopened = http.get(f"/clients/{client_id}").get_data(as_text=True)
        stored = db.session.get(Client, client_id)
        attached = db.session.get(Project, project_id)
        issued = db.session.get(Proposal, proposal_id)
        untouched = Client.query.filter_by(name="Pine Client").one()
        client_count = Client.query.count()
        stored_id = stored.id
        stored_created_at = stored.created_at
        stored_name = stored.name
        stored_company = stored.company
        stored_email = stored.email
        stored_phone = stored.phone
        stored_address = stored.address
        stored_notes = stored.notes
        attached_client_id = attached.client_id
        attached_client_name = attached.client.name
        issued_client_name = issued.client_name
        issued_estimate_id = issued.estimate_id
        untouched_company = untouched.company
        db.session.remove()
        db.drop_all()

    assert saved.status_code == 302
    assert saved.headers["Location"].endswith("/clients/")
    assert stored_id == client_id
    assert stored_created_at == created_at
    assert stored_name == "Oak Client Revised"
    assert stored_company == "Oak Company"
    assert stored_email == "revised@example.com"
    assert stored_phone == "613-555-0199"
    assert stored_address == "9 Revised Lane"
    assert stored_notes == "Updated note"
    assert "Oak Client Revised" in listed
    assert "Pine Client" in listed
    assert 'value="Oak Client Revised"' in reopened
    assert attached_client_id == client_id
    assert attached_client_name == "Oak Client Revised"
    assert issued_client_name == "Oak Client"
    assert issued_estimate_id is not None
    assert untouched_company == "Pine Co"
    assert client_count == 2


def test_unchanged_save_keeps_the_same_client():
    application = _app()
    with application.app_context():
        db.create_all()
        http = _office(application)
        client = Client(
            name="Same Client",
            company="Same Co",
            organization_id=DEFAULT_ORGANIZATION_ID,
        )
        db.session.add(client)
        db.session.commit()
        client_id = client.id
        saved = http.post(
            f"/clients/{client_id}",
            data={
                "name": "Same Client",
                "company": "Same Co",
                "email": "",
                "phone": "",
                "address": "",
                "notes": "",
            },
        )
        stored = db.session.get(Client, client_id)
        count = Client.query.count()
        db.session.remove()
        db.drop_all()
    assert saved.status_code == 302
    assert stored.id == client_id
    assert stored.name == "Same Client"
    assert count == 1


def test_missing_name_does_not_change_the_client():
    application = _app()
    with application.app_context():
        db.create_all()
        http = _office(application)
        client = Client(
            name="Named Client",
            company="Named Co",
            organization_id=DEFAULT_ORGANIZATION_ID,
        )
        db.session.add(client)
        db.session.commit()
        client_id = client.id
        rejected = http.post(
            f"/clients/{client_id}",
            data={"name": "   ", "company": "Should Not Save"},
        )
        stored = db.session.get(Client, client_id)
        html = rejected.get_data(as_text=True)
        db.session.remove()
        db.drop_all()
    assert rejected.status_code == 200
    assert "Client name is required." in html
    assert stored.name == "Named Client"
    assert stored.company == "Named Co"


def test_missing_client_is_not_found_and_create_still_works():
    application = _app()
    with application.app_context():
        db.create_all()
        http = _office(application)
        missing = http.get("/clients/99999")
        created = http.post(
            "/clients/new",
            data={"name": "New Client", "company": "New Co"},
        )
        stored = Client.query.filter_by(name="New Client").one()
        db.session.remove()
        db.drop_all()
    assert missing.status_code == 404
    assert created.status_code == 302
    assert stored.company == "New Co"
