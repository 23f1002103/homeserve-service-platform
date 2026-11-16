"""Database models for the HomeServe application."""
from .database import db


service_package_services = db.Table(
    "service_package_services",
    db.Column(
        "service_package_id",
        db.Integer,
        db.ForeignKey("service_packages.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "service_type_id",
        db.Integer,
        db.ForeignKey("service_types.id"),
        primary_key=True,
    ),
)


class User(db.Model):
    """Model representing a user in the HomeServe application."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    google_subject = db.Column(db.String(255), unique=True, nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    # Supported roles: customer, professional, admin.
    role = db.Column(db.String(20), nullable=False, default="customer")


    def __repr__(self):
        return f'<User {self.username}>'

class Customer(db.Model):
    """Model representing a customer in the HomeServe application."""
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pinCode = db.Column(db.String(20), nullable=False)

    user = db.relationship('User', backref=db.backref('customer', uselist=False))

    def is_complete(self):
        """Return whether this customer can safely create a booking."""
        return all(
            (
                self.user.phone_number,
                self.address,
                self.city,
                self.state,
                self.pinCode,
            )
        )

    def __repr__(self):
        return f'<Customer {self.user.username}>'

class Professional(db.Model):
    """Model representing a professional in the HomeServe application."""
    __tablename__ = 'professionals'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    # Application states: pending, approved, blocked.
    approval_status = db.Column(db.String(20), nullable=False, default="pending")
    block_reason = db.Column(db.Text, nullable=True)
    experience_years = db.Column(db.Integer, nullable=True)
    pin_code = db.Column(db.String(20), nullable=False)
    service_type_id = db.Column(
        db.Integer,
        db.ForeignKey("service_types.id"),
        nullable=False,
    )
    service_type = db.relationship(
        "ServiceType",
        backref=db.backref("professionals", lazy=True),
    )
    active_service_area_id = db.Column(
        db.Integer,
        db.ForeignKey("service_areas.id"),
        nullable=True,
    )
    location_verified_at = db.Column(db.DateTime, nullable=True)
    active_service_area = db.relationship(
        "ServiceArea",
        back_populates="active_professionals",
    )

    user = db.relationship('User', backref=db.backref('professional', uselist=False))
    photo = db.relationship(
        "ProfessionalPhoto",
        back_populates="professional",
        cascade="all, delete-orphan",
        uselist=False,
    )

    def __repr__(self):
        return f'<Professional {self.user.username}>'


class ProfessionalPhoto(db.Model):
    """A professional's customer-facing profile photo."""
    __tablename__ = "professional_photos"

    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(
        db.Integer,
        db.ForeignKey("professionals.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    image_data = db.Column(db.LargeBinary, nullable=False)
    mime_type = db.Column(db.String(50), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    professional = db.relationship("Professional", back_populates="photo")

class ServiceRequest(db.Model):
    """Model representing a service request in the HomeServe application."""
    __tablename__ = 'service_requests'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=True)
    service_type_id = db.Column(
        db.Integer,
        db.ForeignKey("service_types.id"),
        nullable=False,
    )
    service_package_id = db.Column(
        db.Integer,
        db.ForeignKey("service_packages.id"),
        nullable=True,
    )
    package_order_id = db.Column(
        db.Integer,
        db.ForeignKey("package_orders.id"),
        nullable=True,
    )
    service_area_id = db.Column(
        db.Integer,
        db.ForeignKey("service_areas.id"),
        nullable=True,
    )
    description = db.Column(db.Text, nullable=True)
    booking_for = db.Column(db.String(20), nullable=False, default="self")
    recipient_name = db.Column(db.String(100), nullable=True)
    recipient_phone = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")  # payment_pending, pending, accepted, completed, cancelled
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    completed_at = db.Column(db.DateTime, nullable=True)
    review_prompted_at = db.Column(db.DateTime, nullable=True)
    reminder_sent_at = db.Column(db.DateTime, nullable=True)
    scheduled_for=db.Column(db.DateTime, nullable=True)
    service_address=db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    service_type = db.relationship("ServiceType", backref=db.backref("service_requests", lazy=True))
    service_area = db.relationship("ServiceArea", backref=db.backref("service_requests", lazy=True))
    customer = db.relationship('Customer', backref=db.backref('service_requests', lazy=True))
    professional = db.relationship('Professional', backref=db.backref('service_requests', lazy=True))
    service_package = db.relationship(
        "ServicePackage",
        back_populates="bookings",
    )
    package_order = db.relationship("PackageOrder", back_populates="jobs")

    @property
    def service_name(self):
        """Use the package name in customer-facing booking descriptions."""
        if self.service_package:
            return f"{self.service_package.name} · {self.service_type.name}"
        return self.service_type.name

    def __repr__(self):
        return f'<ServiceRequest {self.id} - {self.status}>'


class Review(db.Model):
    """Model representing a review in the HomeServe application."""
    __tablename__ = 'reviews'
    __table_args__ = (
        db.UniqueConstraint(
            'service_request_id',
            name='uq_reviews_service_request_id',
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(
        db.Integer,
        db.ForeignKey('service_requests.id'),
        nullable=False,
    )
    rating = db.Column(db.Integer, nullable=False)  # Assuming rating is an integer value
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    service_request = db.relationship('ServiceRequest', backref=db.backref('reviews', lazy=True))

    def __repr__(self):
        return f'<Review {self.id} - Rating: {self.rating}>'

class Payment(db.Model):
    """Model representing a payment in the HomeServe application."""
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_requests.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    commission_rate = db.Column(db.Numeric(5, 2), nullable=False)
    platform_fee = db.Column(db.Numeric(10, 2), nullable=False)
    professional_earning = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # e.g., credit_card, paypal, etc.
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending, completed, failed, refunded, cancelled
    provider_order_id = db.Column(db.String(100), unique=True, nullable=True)
    provider_payment_id = db.Column(db.String(100), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    service_request = db.relationship('ServiceRequest', backref=db.backref('payments', lazy=True))

    def __repr__(self):
        return f'<Payment {self.id} - Amount: {self.amount} - Status: {self.status}>'

class Notification(db.Model):
    """Model representing a notification in the HomeServe application."""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship('User', backref=db.backref('notifications', lazy=True))

    def __repr__(self):
        return f'<Notification {self.id} - User: {self.user.username} - Read: {self.is_read}>'

class ServiceType(db.Model):
    """Model representing a service type in the HomeServe application."""
    __tablename__ = 'service_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<ServiceType {self.name}>'


class ServicePackage(db.Model):
    """A discounted bundle containing two or more service categories."""
    __tablename__ = "service_packages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.String(500), nullable=True)
    regular_price = db.Column(db.Numeric(10, 2), nullable=False)
    package_price = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    service_types = db.relationship(
        "ServiceType",
        secondary=service_package_services,
        backref=db.backref("packages", lazy=True),
        order_by="ServiceType.name",
    )
    bookings = db.relationship("ServiceRequest", back_populates="service_package")

    def __repr__(self):
        return f"<ServicePackage {self.name}>"


class PackageOrder(db.Model):
    """One customer-facing package order containing several professional jobs."""
    __tablename__ = "package_orders"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id"),
        nullable=False,
    )
    service_package_id = db.Column(
        db.Integer,
        db.ForeignKey("service_packages.id"),
        nullable=False,
    )
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="payment_pending")
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    customer = db.relationship(
        "Customer",
        backref=db.backref("package_orders", lazy=True),
    )
    service_package = db.relationship(
        "ServicePackage",
        backref=db.backref("orders", lazy=True),
    )
    jobs = db.relationship(
        "ServiceRequest",
        back_populates="package_order",
        order_by="ServiceRequest.id",
    )

    def refresh_status(self):
        """Derive the customer-facing package state from all child jobs."""
        if self.status == "cancelled" or not self.jobs:
            return self.status
        statuses = [job.status for job in self.jobs]
        if all(status == "payment_pending" for status in statuses):
            self.status = "payment_pending"
        elif all(status == "completed" for status in statuses):
            self.status = "completed"
        elif any(status == "completed" for status in statuses):
            self.status = "partially_completed"
        elif all(status == "accepted" for status in statuses):
            self.status = "assigned"
        elif any(status == "accepted" for status in statuses):
            self.status = "partially_assigned"
        else:
            self.status = "pending"
        return self.status

    def __repr__(self):
        return f"<PackageOrder {self.id} - {self.status}>"

class ServiceArea(db.Model):
    """Model representing a service area in the HomeServe application."""
    __tablename__ = 'service_areas'

    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pin_code = db.Column(db.String(20), nullable=False)
    center_latitude = db.Column(db.Float, nullable=True)
    center_longitude = db.Column(db.Float, nullable=True)
    radius_km = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    @property
    def has_geo_zone(self):
        return all(
            value is not None
            for value in (self.center_latitude, self.center_longitude, self.radius_km)
        )

    active_professionals = db.relationship(
        "Professional",
        back_populates="active_service_area",
    )

    def __repr__(self):
        return f'<ServiceArea {self.city}, {self.state} - PinCode: {self.pin_code}>'

class ServicePricing(db.Model):
    """Model representing service pricing in the HomeServe application."""
    __tablename__ = 'service_pricing'

    id = db.Column(db.Integer, primary_key=True)
    service_type_id = db.Column(db.Integer, db.ForeignKey('service_types.id'), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    service_type = db.relationship('ServiceType', backref=db.backref('pricing', lazy=True))

    def __repr__(self):
        return f'<ServicePricing {self.service_type.name} - Price: {self.price}>'
