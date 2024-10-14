from django.contrib import admin

from theatre.models import (
    TheatreHall,
    Genre,
    Actor,
    Play,
    Performance,
    Reservation,
    Ticket,
)

admin.site.register(TheatreHall)
admin.site.register(Genre)
admin.site.register(Actor)
admin.site.register(Play)
admin.site.register(Performance)
admin.site.register(Ticket)


class TicketInReservation(admin.TabularInline):
    model = Ticket
    extra = 1


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    inlines = (TicketInReservation,)
