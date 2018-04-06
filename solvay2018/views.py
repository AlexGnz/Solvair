from django.shortcuts import render, redirect
from solvay2018.models import *

import datetime
import pytz
from random import randint

utc = pytz.UTC


def index(request):
    if 'user_id' in request.session:
        return redirect(home)
    else:
        return redirect(login)


def signup(request):
    if 'user_id' in request.session:
        return redirect(home)
    else:
        if 'username' in request.GET:
            errors = []
            if len(User.objects.filter(username=request.GET['username'])) == 0:
                if request.GET['password'] == request.GET['password_confirm']:
                    user = User(username=request.GET['username'],
                                password=request.GET['password'],
                                type=request.GET['type'])
                    user.save()
                    request.session['user_id'] = user.id
                    return redirect(home)
                else:
                    errors.append('Password and password confirmation does not match!')
                    return render(request, 'signup.html', {'errors': errors})
            else:
                errors.append('Username already in use...')
                return render(request, 'signup.html', {'errors': errors})
        else:
            return render(request, 'signup.html')


def logout(request):
    if 'user_id' in request.session:
        del request.session['user_id']
        request.session['message'] = 'You were successfully disconnected'
        return redirect(login)
    else:
        return redirect(login)


def login(request):
    errors = []
    if 'user_id' in request.session:
        return redirect(home)
    else:
        if 'message' in request.session:
            errors.append(request.session['message'])
            del request.session['message']
        if 'username' in request.session:
            username = request.session['username']
            del request.session['username']
            password = request.session['password']
            del request.session['password']
            if len(User.objects.all().filter(username=username, password=password)) == 1:
                user = User.objects.get(username=username)
                request.session['user_id'] = user.id
                return redirect(home)
            elif len(User.objects.all().filter(username=username)) == 0:
                errors.append('Username not found')
                return render(request, 'login.html', {'errors': errors})
            else:
                errors.append('Password not correct')
                return render(request, 'login.html', {'errors': errors})

        if 'username' in request.GET:
            if len(User.objects.all().filter(username=request.GET['username'], password=request.GET['password'])) == 1:
                user = User.objects.get(username=request.GET['username'])
                request.session['user_id'] = user.id
                return redirect(home)
            elif len(User.objects.all().filter(username=request.GET['username'])) == 0:
                errors.append('Username not found')
                return render(request, 'login.html', {'errors': errors})
            else:
                errors.append('Password not correct')
                return render(request, 'login.html', {'errors': errors})
        else:
            return render(request, 'login.html', {'errors': errors})


def home(request):
    if 'user_id' in request.session:
        user = User.objects.get(id=request.session['user_id'])
        errors = []
        if 'error' in request.session:
            errors.append(request.session['error'])
            del request.session['error']
        if user.type == 'E':
            turnover = 0
            for r in Reservation.objects.all():
                turnover += r.nombre_places * r.prix
            if 'form_add_aircraft' in request.GET:
                aircraft = Avion(
                    nom=request.GET['name'],
                    compagnie=request.GET['company'],
                    capacite=request.GET['capacite'])
                aircraft.save()
            if 'form_add_flight' in request.GET:
                avion = Avion.objects.get(id=request.GET['aircraft_id'])
                date_init = request.GET['date_init']
                date_finale = request.GET['date_final']
                date_init = date_init.replace('-', '')
                date_finale = date_finale.replace('-', '')
                datetime_init = datetime.datetime.strptime(date_init, "%Y%m%d %H:%M")
                datetime_finale = datetime.datetime.strptime(date_finale, "%Y%m%d %H:%M")
                datetime_init = utc.localize(datetime_init)
                datetime_finale = utc.localize(datetime_finale)
                datetime_now = utc.localize(datetime.datetime.now())
                if datetime_init < datetime_now:
                    errors.append('You can\'t add a flight with a past date')
                if datetime_init >= datetime_finale:
                    errors.append("You are not in 'Back to the future'... ")

                vols = Vol.objects.filter(avion=avion)
                pas_ok = []
                for v in vols:
                    if v.datetime_depart <= datetime_init and v.datetime_arrivee >= datetime_init or v.datetime_depart <= datetime_finale and datetime_finale <= v.datetime_arrivee:
                        pas_ok.append(v)
                if len(pas_ok) > 0 or len(errors) > 0:
                    errors.append('The aircraft is already in use during this timing')
                else:
                    ville_i = request.GET['city_init'].lower()
                    if len(Ville.objects.all().filter(nom=ville_i)) == 0:
                        ville_init = Ville(nom=ville_i, prefixe=ville_i[0:3].upper())
                        ville_init.save()
                    else:
                        ville_init = Ville.objects.get(nom=ville_i)
                    ville_f = request.GET['city_final'].lower()
                    if len(Ville.objects.all().filter(nom=ville_f)) == 0:
                        ville_finale = Ville(nom=ville_f, prefixe=ville_f[0:3].upper())
                        ville_finale.save()
                    else:
                        ville_finale = Ville.objects.get(nom=ville_f)

                    trajet = Trajet(
                        ville_init=ville_init,
                        ville_finale=ville_finale)
                    trajet.save()

                    vol = Vol(
                        trajet=trajet,
                        prix=request.GET['price'],
                        avion=avion,
                        reference=request.GET['reference'],
                        datetime_depart=request.GET['date_init'],
                        datetime_arrivee=request.GET['date_final'])
                    vol.save()
                    vols = Vol.objects.all()
                    aircrafts = Avion.objects.all()
            vols = Vol.objects.all().order_by('datetime_depart')

            vol_et_nb = []
            for v in vols:
                reservations = Reservation.objects.filter(vol=v)
                nb = 0
                for r in reservations:
                    nb += r.nombre_places
                nb_restantes = v.avion.capacite - nb
                vol_et_nb.append([v, nb_restantes])

            aircrafts = Avion.objects.all()
            return render(request, 'home.html',
                          {'user': user, 'aircrafts': aircrafts, 'vols': vols, 'vol_et_nb': vol_et_nb, 'errors': errors,
                           'turnover': turnover})
        else:
            stops = False
            vols_dispos = []
            vols_searched = []
            escales = []
            escales_potentielles = []
            match_v_init = []
            match_v_finale = []
            vols = Vol.objects.all()
            villes = Ville.objects.all().order_by('nom')
            user = User.objects.get(id=request.session['user_id'])
            reservations = Reservation.objects.filter(user=user).order_by('vol__datetime_depart')
            for v in vols:
                reservations_vol = Reservation.objects.filter(vol=v)
                nb = 0
                for r in reservations_vol:
                    nb += r.nombre_places
                if nb < v.avion.capacite:
                    vols_dispos.append(v)

            if 'search_for_a_flight' in request.GET:
                ville_init = Ville.objects.get(id=request.GET['id_ville_depart'])
                ville_finale = Ville.objects.get(id=request.GET['id_ville_arrivee'])
                date = request.GET['date']
                date = date.replace('-', ' ')
                datetime_object = datetime.datetime.strptime(date, "%Y %m %d %H:%M")
                time_delta = int(request.GET['timedelta'])
                date_max = datetime_object + datetime.timedelta(days=time_delta)
                date_min = datetime_object - datetime.timedelta(days=time_delta)
                date_max = utc.localize(date_max)
                date_min = utc.localize(date_min)

                if 'escale' in request.GET:
                    stops = True
                    for v in vols:
                        if v.trajet.ville_init.id == ville_init.id:
                            match_v_init.append(v)
                        if v.trajet.ville_finale.id == ville_finale.id:
                            match_v_finale.append(v)

                    for i in match_v_init:
                        for f in match_v_finale:
                            if f.trajet.ville_init.id == i.trajet.ville_finale.id and i.datetime_arrivee < f.datetime_depart:
                                escales_potentielles.append(i.trajet.ville_finale)

                for e in escales_potentielles:
                    escales.append([ville_init, e, ville_finale])

                for v in Vol.objects.filter(trajet__ville_init=ville_init, trajet__ville_finale=ville_finale):
                    if v.datetime_depart >= date_min and v.datetime_depart <= date_max:
                        vols_searched.append(v)

            if 'random_flight_form' in request.GET:
                ville_init = Ville.objects.get(id=request.GET['id_ville_depart'])
                vols = Vol.objects.filter(trajet__ville_init=ville_init)
                if len(vols) > 0:
                    random = randint(0, len(vols) - 1)
                    vols_searched.append(vols[random])

            return render(request, 'home.html',
                          {'user': user, 'villes': villes, 'vols_searched': vols_searched, 'escales': escales,
                           'reservations': reservations, 'stops': stops, 'errors': errors})
    else:
        return redirect(login)


def delete(request):
    if 'delete_flight' in request.GET:
        flight = Vol.objects.get(id=request.GET['vol_id'])
        flight.delete()

    if 'delete_reservation' in request.GET:
        reservation = Reservation.objects.get(id=request.GET['resa_id'])
        reservation.delete()
    return redirect(home)


def reservation(request):
    errors = []
    colonnes = ['A', 'B', 'C', 'D', 'E', 'F']
    lignes = []
    for x in range(1, 31):
        lignes.append(x)

    places_un = []
    for c in colonnes:
        for i in lignes:
            places_un.append(c + str(i))
    places_deux = []
    for c in colonnes:
        for i in lignes:
            places_deux.append(c + str(i))
    places_prises_un = []
    places_prises_deux = []

    if 'user_id' in request.session:
        user = User.objects.get(id=request.session['user_id'])

        if 'book_form' in request.GET:
            vol = Vol.objects.get(id=request.GET['vol_id'])

            reservations = Reservation.objects.filter(vol=vol)
            nb = 0
            for r in reservations:
                nb += r.nombre_places
            if nb + int(request.GET['nombre']) <= vol.avion.capacite:
                prix = vol.prix
                first = False

                if 'first_class_service' in request.GET:
                    prix = vol.prix * 2
                    first = True

                reservation = Reservation(user=user,
                                          vol=vol,
                                          prix=prix,
                                          nombre_places=request.GET['nombre'],
                                          first_class=first
                                          )
                reservation.save()
                for r in Reservation.objects.filter(vol=vol):
                    for p in Place.objects.filter(reservation=r):
                        places_prises_un.append(p.emplacement)
                for p in places_prises_un:
                    places_un.remove(p)
                nombre = int(request.GET['nombre'])
                nb_places = []
                for x in range(1, nombre + 1):
                    nb_places.append(x)

                return render(request, 'reservation.html',
                              {'nb': nb_places, 'reserved': True, 'places_un': places_un, 'reservation': reservation,
                               'no_stops': True})
            else:
                errors.append('That number of seats is not available... Sorry... or not sorry')
                return render(request, 'reservation.html', {'errors': errors, 'vol': vol})
        elif 'book_with_stops' in request.GET:
            ville_init = Ville.objects.get(id=request.GET['id_ville_init'])
            ville_escale = Ville.objects.get(id=request.GET['id_ville_escale'])
            ville_finale = Ville.objects.get(id=request.GET['id_ville_finale'])
            vols_un = Vol.objects.filter(trajet__ville_init=ville_init, trajet__ville_finale=ville_escale)
            vols_deux = Vol.objects.filter(trajet__ville_init=ville_escale, trajet__ville_finale=ville_finale)
            vols_un_ok = []
            vols_deux_ok = []
            nb_un = 0
            nb_deux = 0
            nb = []
            if len(vols_un) > 0 and len(vols_deux) > 0:
                for v in vols_un:
                    for x in vols_deux:
                        if v.datetime_arrivee < x.datetime_depart:
                            vols_un_ok.append(v)
                            vols_deux_ok.append(x)
            else:
                errors.append("please choose another flight")
            if len(errors) == 0:
                vol_un = vols_un_ok[0]
                reservations_vol_un = Reservation.objects.filter(vol=vol_un)

                for r in reservations_vol_un:
                    nb_un += r.nombre_places

                vol_deux = vols_deux_ok[0]
                reservations_vol_deux = Reservation.objects.filter(vol=vol_deux)

                for r in reservations_vol_deux:
                    nb_deux += r.nombre_places

                if nb_un + int(request.GET['nombre']) <= vol_un.avion.capacite and nb_deux + int(
                        request.GET['nombre']) <= vol_deux.avion.capacite:
                    prix_un = vol_un.prix
                    prix_deux = vol_deux.prix
                    first = False

                    if 'first_class_service' in request.GET:
                        prix_un = prix_un * 2
                        prix_deux = prix_deux * 2
                        first = True

                    reservation_un = Reservation(
                        vol=vol_un,
                        user=user,
                        prix=prix_un,
                        nombre_places=request.GET['nombre'],
                        first_class=first)
                    reservation_un.save()

                    reservation_deux = Reservation(
                        vol=vol_deux,
                        user=user,
                        prix=prix_deux,
                        nombre_places=request.GET['nombre'],
                        first_class=first)
                    reservation_deux.save()

                    nombre = int(request.GET['nombre'])
                    for x in range(1, nombre + 1):
                        nb.append(x)

                    for r in Reservation.objects.filter(vol=vol_un):
                        for p in Place.objects.filter(reservation=r):
                            places_prises_un.append(p.emplacement)

                    for p in places_prises_un:
                        places_un.remove(p)

                    for r in Reservation.objects.filter(vol=vol_deux):
                        for p in Place.objects.filter(reservation=r):
                            places_prises_deux.append(p.emplacement)

                    for p in places_prises_deux:
                        places_deux.remove(p)

                    return render(request, 'reservation.html',
                                  {'nb': nb, 'reserved': True, 'places_un': places_un, 'places_deux': places_deux,
                                   'reservation_un': reservation_un, 'reservation_deux': reservation_deux})
                else:
                    errors.append('That number of seats is not available... Sorry... or not sorry')
                    return render(request, 'reservation.html', {'errors': errors})
            else:
                return render(request, 'reservation.html', {'errors': errors})
        elif 'book_places' in request.GET:
            nb = int(request.GET['nb'])
            nb_resa = int(request.GET['nb_resa'])
            for x in range(1, nb_resa + 1):
                for i in range(1, nb + 1):
                    place = Place(reservation=Reservation.objects.get(id=request.GET['reservation_' + str(x)]),
                                  emplacement=request.GET['place_' + str(i)])
                    if len(Place.objects.filter(reservation=place.reservation, emplacement=place.emplacement)) == 0:
                        place.save()
                    else:
                        request.session[
                            'error'] = 'You selected the same place two times (or more) so we will choose your places by ourself...'
                        return redirect(home)
            return redirect(home)
        else:
            if 'id_ville_init' in request.GET:
                stops = True
                ville_init = Ville.objects.get(id=request.GET['id_ville_init'])
                ville_escale = Ville.objects.get(id=request.GET['id_ville_escale'])
                ville_finale = Ville.objects.get(id=request.GET['id_ville_finale'])
                villes = [ville_init, ville_escale, ville_finale]
                return render(request, 'reservation.html', {'villes': villes, 'stops': stops})
            elif 'vol_id' in request.GET:
                vol = Vol.objects.get(id=request.GET['vol_id'])
                return render(request, 'reservation.html', {'vol': vol})
            else:
                return redirect(home)
    else:
        return redirect(login)


def demo(request):
    errors = []
    if 'verif' in request.GET and request.GET['verif'] == 'laissemoientrer':
        request.session['username'] = request.GET['username']
        request.session['password'] = request.GET['password']
        return redirect(login)
    elif 'verif' in request.GET:
        errors.append('The verification input is not ok..')
        return render(request, 'login.html', {'secret': True, 'errors': errors})
    else:
        return render(request, 'login.html', {'secret': True})

