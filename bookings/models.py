from django.db import models
from django.conf import settings

class Venue(models.Model):
    VENUE_TYPES = [
        ('wedding_hall', 'Wedding Hall'),
        ('fest', 'Fest'),
        ('dining_table', 'Dining Table'),
        ('vip_table', 'VIP Table'),
        ('conference_room', 'Conference Room'),
    ]
    
    name = models.CharField(max_length=100)
    venue_type = models.CharField(max_length=20, choices=VENUE_TYPES)
    capacity = models.PositiveIntegerField(help_text="Maximum number of guests")
    location = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='venues/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_venue_type_display()})"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('payment_pending', 'Payment Pending'),  # NEW STATUS
        ('paid', 'Paid'),                          # NEW STATUS
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHODS = [
        ('upi', 'UPI'),
        ('card', 'Credit/Debit Card'),
        ('netbanking', 'Net Banking'),
        ('cash', 'Cash on Delivery'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='bookings')
    event_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    guests = models.PositiveIntegerField()
    special_requests = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment fields
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, blank=True, null=True)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=20, default='pending')  # pending, completed
    payment_date = models.DateTimeField(blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.venue.name} on {self.event_date}"