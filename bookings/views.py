from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
import random
import string
from django.db.models import Q
from .models import Venue, Booking

# QR code imports
import qrcode
from io import BytesIO
from django.http import HttpResponse


def home(request):
    """
    Home page - Show ALL venues that are available.
    Venue is available if is_available=True AND no confirmed booking.
    """
    venues = Venue.objects.filter(is_available=True).order_by('name')
    context = {'venues': venues}
    return render(request, 'home.html', context)


# ==================== VENUE LIST VIEW ====================
def venue_list(request):
    """Display all available venues with search, filter, and sorting."""
    venues = Venue.objects.filter(is_available=True)
    search_query = request.GET.get('search', '')
    selected_type = request.GET.get('type', '')
    sort_by = request.GET.get('sort', 'name')

    if search_query:
        venues = venues.filter(
            Q(name__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if selected_type:
        venues = venues.filter(venue_type=selected_type)
    
    allowed_sorts = ['name', 'capacity', 'price_per_hour', '-capacity', '-price_per_hour']
    if sort_by in allowed_sorts:
        venues = venues.order_by(sort_by)
    else:
        venues = venues.order_by('name')

    context = {
        'venues': venues,
        'venue_types': Venue.VENUE_TYPES,
        'selected_type': selected_type,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'bookings/venue_list.html', context)


def venue_detail(request, pk):
    """Display venue details."""
    venue = get_object_or_404(Venue, pk=pk)
    context = {'venue': venue}
    return render(request, 'bookings/venue_detail.html', context)


@login_required(login_url='login')
def create_booking(request, venue_id):
    """Create booking - Venue stays available until admin confirms."""
    venue = get_object_or_404(Venue, pk=venue_id)
    
    if not venue.is_available:
        messages.error(request, 'This venue is currently unavailable.')
        return redirect('home')
    
    if request.method == 'POST':
        event_date = request.POST.get('event_date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        guests = request.POST.get('guests')
        special_requests = request.POST.get('special_requests', '')
        
        has_error = False
        
        if not event_date:
            messages.error(request, 'Event date is required.')
            has_error = True
        else:
            try:
                event_date_obj = datetime.strptime(event_date, '%Y-%m-%d').date()
                if event_date_obj < timezone.now().date():
                    messages.error(request, 'Cannot book a past date.')
                    has_error = True
            except ValueError:
                messages.error(request, 'Invalid date format.')
                has_error = True
        
        if not start_time:
            messages.error(request, 'Start time is required.')
            has_error = True
        
        if not end_time:
            messages.error(request, 'End time is required.')
            has_error = True
        
        if start_time and end_time and start_time >= end_time:
            messages.error(request, 'End time must be after start time.')
            has_error = True
        
        if not guests:
            messages.error(request, 'Number of guests is required.')
            has_error = True
        else:
            try:
                guests = int(guests)
                if guests < 1:
                    messages.error(request, 'Minimum 1 guest required.')
                    has_error = True
                elif guests > venue.capacity:
                    messages.error(request, f'Maximum capacity is {venue.capacity} guests.')
                    has_error = True
            except ValueError:
                messages.error(request, 'Invalid number of guests.')
                has_error = True
        
        if not has_error:
            try:
                # Calculate payment
                start_dt = datetime.strptime(start_time, '%H:%M')
                end_dt = datetime.strptime(end_time, '%H:%M')
                hours = (end_dt - start_dt).seconds / 3600
                if hours <= 0:
                    hours = 1
                
                payment_amount = float(venue.price_per_hour) * hours
                
                # Create booking - DO NOT change venue availability
                booking = Booking.objects.create(
                    user=request.user,
                    venue=venue,
                    event_date=event_date,
                    start_time=start_time,
                    end_time=end_time,
                    guests=guests,
                    special_requests=special_requests,
                    status='payment_pending',
                    payment_amount=payment_amount,
                    payment_status='pending'
                )
                
                messages.success(request, f'Booking created! Complete payment of ${payment_amount:.2f}.')
                return redirect('payment_page', booking_id=booking.pk)
                
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        
        context = {
            'venue': venue,
            'form_data': {'event_date': event_date, 'start_time': start_time, 
                         'end_time': end_time, 'guests': guests, 
                         'special_requests': special_requests}
        }
        return render(request, 'bookings/booking_form.html', context)
    
    return render(request, 'bookings/booking_form.html', {'venue': venue})


# ==================== QR CODE GENERATION ====================
@login_required(login_url='login')
def generate_payment_qr(request, booking_id):
    """Generate UPI QR code with amount pre-filled."""
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    
    # UPI payment details – CHANGE THESE TO YOUR ACTUAL UPI ID
    upi_id = "eventbooker@upi"      # Replace with your UPI ID
    amount = str(booking.payment_amount)
    payee_name = "EventBooker"
    currency = "INR"                # Change to USD if needed
    
    # Standard UPI intent URI
    upi_url = f"upi://pay?pa={upi_id}&am={amount}&cu={currency}&pn={payee_name}"
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(upi_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#000000", back_color="white")
    
    # Return image response
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return HttpResponse(buffer, content_type="image/png")


@login_required(login_url='login')
def payment_page(request, booking_id):
    """Payment page."""
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    
    if booking.status in ['paid', 'confirmed']:
        messages.info(request, 'Payment already completed.')
        return redirect('my_bookings')
    
    if booking.status == 'cancelled':
        messages.error(request, 'This booking has been cancelled.')
        return redirect('my_bookings')
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        action = request.POST.get('action', 'pay')
        
        if action == 'cancel':
            booking.status = 'cancelled'
            booking.save()
            messages.warning(request, 'Booking cancelled.')
            return redirect('home')
        
        if payment_method in ['upi', 'card', 'netbanking', 'cash']:
            booking.payment_method = payment_method
            
            if payment_method == 'cash':
                booking.save()
                messages.success(request, 'Cash on delivery selected.')
            else:
                booking.payment_status = 'completed'
                booking.payment_date = timezone.now()
                booking.status = 'paid'
                booking.transaction_id = 'TXN' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                booking.save()
                messages.success(request, 'Payment successful! Awaiting admin confirmation.')
            
            return redirect('payment_success', booking_id=booking.pk)
        else:
            messages.error(request, 'Please select a payment method.')
    
    return render(request, 'bookings/payment_page.html', {
        'booking': booking,
        'payment_amount': booking.payment_amount
    })


@login_required(login_url='login')
def payment_success(request, booking_id):
    """Payment success page."""
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    return render(request, 'bookings/payment_success.html', {'booking': booking})


@login_required(login_url='login')
def my_bookings(request):
    """User's bookings."""
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})


@login_required(login_url='login')
def cancel_booking(request, pk):
    """Cancel booking."""
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    
    if booking.status == 'cancelled':
        messages.warning(request, 'Already cancelled.')
        return redirect('my_bookings')
    
    if booking.status == 'confirmed':
        messages.error(request, 'Cannot cancel confirmed booking.')
        return redirect('my_bookings')
    
    # If booking was confirmed, make venue available again
    if booking.status == 'confirmed':
        booking.venue.is_available = True
        booking.venue.save()
    
    booking.status = 'cancelled'
    booking.save()
    
    messages.success(request, 'Booking cancelled.')
    return redirect('my_bookings')


@login_required(login_url='login')
def retry_payment(request, booking_id):
    """Retry payment."""
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    
    if booking.status != 'payment_pending':
        messages.info(request, 'Payment not needed.')
        return redirect('my_bookings')
    
    return redirect('payment_page', booking_id=booking.pk)


# ==================== ADMIN ====================

@staff_member_required(login_url='login')
def admin_dashboard(request):
    """Admin dashboard."""
    total_venues = Venue.objects.count()
    available_venues = Venue.objects.filter(is_available=True).count()
    total_bookings = Booking.objects.count()
    paid_bookings = Booking.objects.filter(status='paid').count()
    confirmed_bookings = Booking.objects.filter(status='confirmed').count()
    cancelled_bookings = Booking.objects.filter(status='cancelled').count()
    
    from django.db.models import Sum
    revenue = Booking.objects.filter(status='confirmed').aggregate(
        total=Sum('payment_amount')
    )['total'] or 0
    
    needs_confirmation = Booking.objects.filter(status='paid').order_by('-created_at')
    recent_bookings = Booking.objects.select_related('user', 'venue').order_by('-created_at')[:10]
    venues = Venue.objects.all().order_by('-created_at')
    
    context = {
        'total_venues': total_venues,
        'available_venues': available_venues,
        'total_bookings': total_bookings,
        'paid_bookings': paid_bookings,
        'confirmed_bookings': confirmed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'total_revenue': revenue,
        'needs_confirmation': needs_confirmation,
        'recent_bookings': recent_bookings,
        'venues': venues,
    }
    
    return render(request, 'bookings/admin_dashboard.html', context)


@staff_member_required(login_url='login')
def confirm_payment(request, pk):
    """
    Admin confirms booking.
    ONLY NOW the venue becomes unavailable.
    """
    booking = get_object_or_404(Booking, pk=pk)
    
    if booking.status in ['paid', 'payment_pending']:
        booking.status = 'confirmed'
        booking.payment_status = 'completed'
        booking.payment_date = timezone.now()
        booking.save()
        
        # NOW make venue unavailable
        booking.venue.is_available = False
        booking.venue.save()
        
        messages.success(request, f'✅ Booking #{booking.pk} confirmed! Venue "{booking.venue.name}" is now booked.')
    else:
        messages.warning(request, f'Booking is already {booking.status}.')
    
    return redirect('admin_dashboard')


@staff_member_required(login_url='login')
def reject_booking(request, pk):
    """Admin rejects booking - venue stays/becomes available."""
    booking = get_object_or_404(Booking, pk=pk)
    
    if booking.status != 'cancelled':
        booking.status = 'cancelled'
        booking.save()
        
        # Make venue available
        booking.venue.is_available = True
        booking.venue.save()
        
        messages.warning(request, f'❌ Booking #{booking.pk} rejected.')
    
    return redirect('admin_dashboard')


@staff_member_required(login_url='login')
def add_venue(request):
    """Add venue."""
    if request.method == 'POST':
        try:
            venue = Venue.objects.create(
                name=request.POST.get('name'),
                venue_type=request.POST.get('venue_type'),
                capacity=int(request.POST.get('capacity', 0)),
                location=request.POST.get('location'),
                description=request.POST.get('description', ''),
                price_per_hour=float(request.POST.get('price_per_hour', 0)),
                is_available=True,  # Always available when created
                image=request.FILES.get('image')
            )
            messages.success(request, f'Venue "{venue.name}" added!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('admin_dashboard')


@staff_member_required(login_url='login')
def edit_venue(request, pk):
    """Edit venue."""
    venue = get_object_or_404(Venue, pk=pk)
    
    if request.method == 'POST':
        venue.name = request.POST.get('name', venue.name)
        venue.venue_type = request.POST.get('venue_type', venue.venue_type)
        venue.capacity = int(request.POST.get('capacity', venue.capacity))
        venue.location = request.POST.get('location', venue.location)
        venue.description = request.POST.get('description', venue.description)
        venue.price_per_hour = float(request.POST.get('price_per_hour', venue.price_per_hour))
        venue.is_available = request.POST.get('is_available') == 'on'
        
        if request.FILES.get('image'):
            venue.image = request.FILES.get('image')
        
        venue.save()
        messages.success(request, 'Venue updated!')
        return redirect('admin_dashboard')
    
    return render(request, 'bookings/edit_venue.html', {'venue': venue})


@staff_member_required(login_url='login')
def delete_venue(request, pk):
    """Delete venue."""
    venue = get_object_or_404(Venue, pk=pk)
    venue_name = venue.name
    venue.delete()
    messages.success(request, f'Venue "{venue_name}" deleted!')
    return redirect('admin_dashboard')


@staff_member_required(login_url='login')
def manage_bookings(request):
    """Manage all bookings."""
    bookings = Booking.objects.select_related('user', 'venue').all().order_by('-created_at')
    return render(request, 'bookings/manage_bookings.html', {'bookings': bookings})


@staff_member_required(login_url='login')
def update_booking_status(request, pk, status):
    """Update booking status."""
    booking = get_object_or_404(Booking, pk=pk)
    
    valid_statuses = ['pending', 'payment_pending', 'paid', 'confirmed', 'cancelled']
    if status not in valid_statuses:
        messages.error(request, 'Invalid status.')
        return redirect('manage_bookings')
    
    # Update venue availability based on new status
    if status == 'confirmed':
        booking.venue.is_available = False
        booking.venue.save()
        booking.payment_status = 'completed'
        booking.payment_date = timezone.now()
    elif status == 'cancelled':
        booking.venue.is_available = True
        booking.venue.save()
    elif status in ['pending', 'payment_pending', 'paid']:
        # Venue should be available for these statuses
        booking.venue.is_available = True
        booking.venue.save()
    
    booking.status = status
    booking.save()
    
    messages.success(request, f'Booking #{booking.pk} → {status}.')
    return redirect('manage_bookings')