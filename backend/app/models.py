"""Database models for the HomeServe application."""
from .database import db


professional_service_areas = db.Table(
    "professional_service_areas",
    db.Column(
        "professional_id",
        db.Integer,
        db.ForeignKey("professionals.id"),
        primary_key=True,
    ),
    db.Column(
        "service_area_id",
        db.Integer,
        db.ForeignKey("service_areas.id"),
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
    service_areas = db.relationship(
        "ServiceArea",
        secondary=professional_service_areas,
        back_populates="professionals",
    )

    user = db.relationship('User', backref=db.backref('professional', uselist=False))

    def __repr__(self):
        return f'<Professional {self.user.username}>'

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
    service_area_id = db.Column(
        db.Integer,
        db.ForeignKey("service_areas.id"),
        nullable=True,
    )
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")  # payment_pending, pending, accepted, completed, cancelled
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    completed_at = db.Column(db.DateTime, nullable=True)
    reminder_sent_at = db.Column(db.DateTime, nullable=True)
    scheduled_for=db.Column(db.DateTime, nullable=True)
    service_address=db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    service_type = db.relationship("ServiceType", backref=db.backref("service_requests", lazy=True))
    service_area = db.relationship("ServiceArea", backref=db.backref("service_requests", lazy=True))
    customer = db.relationship('Customer', backref=db.backref('service_requests', lazy=True))
    professional = db.relationship('Professional', backref=db.backref('service_requests', lazy=True))

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

class ServiceArea(db.Model):
    """Model representing a service area in the HomeServe application."""
    __tablename__ = 'service_areas'

    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pin_code = db.Column(db.String(20), nullable=False)

    professionals = db.relationship(
        "Professional",
        secondary=professional_service_areas,
        back_populates="service_areas",
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
