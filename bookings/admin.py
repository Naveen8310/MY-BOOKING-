from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Venue, Booking

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'venue_type', 'capacity', 'location', 'price_per_hour', 'is_available')
    list_filter = ('venue_type', 'is_available')
    search_fields = ('name', 'location')
    ordering = ('name',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'venue', 'event_date', 'start_time', 'end_time', 'guests', 'status', 'created_at')
    list_filter = ('status', 'event_date', 'venue__venue_type')
    search_fields = ('user__email', 'user__name', 'venue__name')
    ordering = ('-created_at',)
    date_hierarchy = 'event_date'