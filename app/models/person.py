"""FG-038 PA-C organization-scoped Person / Worker identity.

Person is not a Platform User. Creating a Person does not create login.
Hourly wage is stored on the row but is not ordinary identity data.
"""

from datetime import datetime

from app import db


class OrganizationPerson(db.Model):
    """Org-scoped human / worker identity. Not authentication. Not access."""

    __tablename__ = "organization_people"
    __table_args__ = (
        db.CheckConstraint(
            "hourly_wage >= 0",
            name="ck_organization_people_hourly_wage_non_negative",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    full_name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.Text, nullable=False)
    mobile_number = db.Column(db.String(40), nullable=False)
    email_address = db.Column(db.String(255), nullable=False)
    hourly_wage = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    updated_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    organization = db.relationship("Organization", foreign_keys=[organization_id])
    created_by_user = db.relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user = db.relationship("User", foreign_keys=[updated_by_user_id])
    wage_events = db.relationship(
        "OrganizationPersonWageEvent",
        back_populates="person",
        order_by="OrganizationPersonWageEvent.id.asc()",
    )

    def __repr__(self):
        return (
            f"<OrganizationPerson {self.id} org={self.organization_id} "
            f"active={self.is_active}>"
        )


class OrganizationPersonWageEvent(db.Model):
    """Append-only Person wage-event persistence. S16 schema only.

    Does not write from create_person / update_person / CLI in S16.
    actor_user_id is NOT NULL following Punch List event actor and
    OrganizationPerson.created_by_user_id. organization_id ON DELETE
    RESTRICT matches OrganizationPerson.
    """

    __tablename__ = "organization_person_wage_events"
    __table_args__ = (
        db.CheckConstraint(
            "previous_hourly_wage IS NULL OR previous_hourly_wage >= 0",
            name="ck_organization_person_wage_events_previous_hourly_wage_non_negative",
        ),
        db.CheckConstraint(
            "hourly_wage >= 0",
            name="ck_organization_person_wage_events_hourly_wage_non_negative",
        ),
        db.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_organization_person_wage_events_organization_id",
            ondelete="RESTRICT",
        ),
        db.ForeignKeyConstraint(
            ["person_id"],
            ["organization_people.id"],
            name="fk_organization_person_wage_events_person_id",
            ondelete="RESTRICT",
        ),
        db.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_organization_person_wage_events_actor_user_id",
            ondelete="RESTRICT",
        ),
        db.Index(
            "ix_organization_person_wage_events_org_person_id",
            "organization_id",
            "person_id",
            "id",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), nullable=False)
    person_id = db.Column(db.Integer, nullable=False)
    previous_hourly_wage = db.Column(db.Numeric(10, 2), nullable=True)
    hourly_wage = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    actor_user_id = db.Column(db.Integer, nullable=False)

    organization = db.relationship(
        "Organization",
        foreign_keys=[organization_id],
    )
    person = db.relationship(
        "OrganizationPerson",
        back_populates="wage_events",
        foreign_keys=[person_id],
    )
    actor_user = db.relationship("User", foreign_keys=[actor_user_id])

    def __repr__(self):
        return (
            f"<OrganizationPersonWageEvent {self.id} "
            f"person={self.person_id} org={self.organization_id}>"
        )


class OrganizationPersonCostProfile(db.Model):
    """Append-only employee cost profile and its Loaded Labour Rate (Joel, 2 Nov 2026).

    One row per save: the inputs, the statutory year used, the working hours, the annual cost and the LLR, with the
    line-by-line breakdown. Never updated or deleted (model guard here; insert-only triggers in the migration). The
    newest row is the employee's current profile; the history is kept.
    """

    __tablename__ = "organization_person_cost_profiles"
    __table_args__ = (
        db.CheckConstraint("hourly_wage > 0", name="ck_person_cost_profiles_wage_positive"),
        db.CheckConstraint("working_hours > 0", name="ck_person_cost_profiles_working_hours_positive"),
        db.Index("ix_person_cost_profiles_org_person", "organization_id", "person_id", "id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey("organization_people.id", ondelete="RESTRICT"), nullable=False)
    hourly_wage = db.Column(db.Numeric(10, 2), nullable=False)
    paid_hours_per_year = db.Column(db.Numeric(8, 2), nullable=False)
    vacation_weeks = db.Column(db.Numeric(6, 2), nullable=False)
    paid_holidays = db.Column(db.Numeric(6, 2), nullable=False)
    truck_monthly = db.Column(db.Numeric(10, 2), nullable=False)
    fuel_monthly = db.Column(db.Numeric(10, 2), nullable=False)
    tool_allowance_annual = db.Column(db.Numeric(10, 2), nullable=False)
    rrsp_percent = db.Column(db.Numeric(6, 3), nullable=False)
    health_premium_monthly = db.Column(db.Numeric(10, 2), nullable=False)
    wsib_rate_per_100 = db.Column(db.Numeric(6, 3), nullable=False)
    wsib_is_override = db.Column(db.Boolean, nullable=False, default=False)
    statutory_year = db.Column(db.Integer, nullable=False)
    working_hours = db.Column(db.Numeric(8, 2), nullable=False)
    annual_cost = db.Column(db.Numeric(12, 2), nullable=False)
    loaded_rate = db.Column(db.Numeric(10, 2), nullable=False)
    breakdown_json = db.Column(db.Text, nullable=False)
    reason = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    actor_name = db.Column(db.String(150), nullable=False)

    person = db.relationship("OrganizationPerson", foreign_keys=[person_id])

    def __repr__(self):
        return f"<OrganizationPersonCostProfile {self.id} person={self.person_id} llr={self.loaded_rate}>"


class OrganizationLabourCostSetting(db.Model):
    """Append-only company labour-cost setting: the WSIB rate per $100 (Joel, 2 Nov 2026). Newest row applies."""

    __tablename__ = "organization_labour_cost_settings"
    __table_args__ = (
        db.CheckConstraint("wsib_rate_per_100 >= 0", name="ck_labour_cost_settings_wsib_non_negative"),
        db.Index("ix_labour_cost_settings_org", "organization_id", "id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    wsib_rate_per_100 = db.Column(db.Numeric(6, 3), nullable=False)
    wsib_class_label = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    actor_name = db.Column(db.String(150), nullable=False)


class EstimateCrewMember(db.Model):
    """An employee on an estimate's crew, with their share of the labour hours (Joel, 2 Nov 2026).

    Real labour cost = hours x each crew member's Loaded Labour Rate x their share. Only an employee with a complete
    cost profile can be assigned (labour_cost_profile.assignable_employees). A change ends the earlier rows
    (removed_at) and adds new ones, so who was on the crew when is kept. The figures used at approval are frozen in
    the estimate's approval record.
    """

    __tablename__ = "estimate_crew_members"
    __table_args__ = (
        db.CheckConstraint("share > 0", name="ck_estimate_crew_members_share_positive"),
        db.Index("ix_estimate_crew_members_estimate", "organization_id", "estimate_id", "removed_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    estimate_id = db.Column(db.Integer, db.ForeignKey("estimates.id", ondelete="RESTRICT"), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey("organization_people.id", ondelete="RESTRICT"), nullable=False)
    share = db.Column(db.Numeric(8, 4), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    assigned_by_name = db.Column(db.String(150), nullable=False)
    removed_at = db.Column(db.DateTime, nullable=True)
    removed_by_name = db.Column(db.String(150), nullable=True)

    person = db.relationship("OrganizationPerson", foreign_keys=[person_id])


def _refuse_change(mapper, connection, target):
    raise ValueError("Cost profiles and company labour-cost settings are append-only: save a new one instead.")


for _model in (OrganizationPersonCostProfile, OrganizationLabourCostSetting):
    db.event.listen(_model, "before_update", _refuse_change)
    db.event.listen(_model, "before_delete", _refuse_change)
