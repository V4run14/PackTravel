from http.client import HTTPResponse
from django.shortcuts import render,redirect
from numpy import True_, dtype
import requests
import json
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm

from publish.forms import RideForm
from utils import get_client
# from django.http import HttpResponse

# Create your views here.
client = None
db = None
userDB = None
ridesDB  = None
routesDB  = None

def intializeDB():
    global client, db, userDB, ridesDB, routesDB
    client = get_client()
    db = client.SEProject
    userDB = db.userData
    ridesDB  = db.rides
    routesDB  = db.routes

def publish_index(request):
    intializeDB()
    if not request.session.has_key('username'):
        request.session['alert'] = "Please login to create a ride."
        return redirect('index')
    return render(request, 'publish/publish.html', {"username": request.session['username'], "alert":True})

def display_ride(request, ride_id):
    intializeDB()
    print("Ride id", ride_id)
    ride = ridesDB.find_one({'_id': ride_id})
    # print(f"Ride = {ride}")
    routes = get_routes(ride)
    print(f"Route = {routes}")
    selected = routeSelect(request.session['username'], routes)
    # print(f"Routes = {selected}")
    context = {
            "username": request.session['username'],
            "ride": ride,
            "routes": routes,
            "selectedRoute": selected
        }
    return render(request, 'publish/route.html', context)

def select_route(request):
    intializeDB()
    if request.method == 'POST':
        route_id = request.POST.get("hiddenInput")
        username = request.POST.get('hiddenUser')
        ride = request.POST.get('hiddenRide')
        print("route from form: ",route_id)
        ride = ride.replace("\'", "\"")
        ride = json.loads(ride)
        ride_id = ride['_id']
        attach_user_to_route(username, route_id)
        return redirect(display_ride, ride_id=ride['_id'] )
    return render(request, 'publish/publish.html', {"username": username})


def routeSelect(username, routes):
    intializeDB()
    user = userDB.find_one({"username": username})
    if user == None or routes == None:
        print("returning NONE")
        return None


    user_routes = user['rides']
    print("User routes: ",user_routes)
    for route in routes:
        if route['_id'] in user_routes:
            print("FOUND")
            return route['_id']
    return None

def get_routes(ride):
    routes = []
    if 'route_id' not in ride:
        return None
    route_ids = ride['route_id']
    for route_id in route_ids:
        route = routesDB.find_one({'_id': route_id})
        if not route:
            pass
        # route['id'] = route.pop('_id')
        routes.append(route)
    return routes

def create_route(request):
    intializeDB()
    if request.method == 'POST':
        route = {
            "_id":
                f"""{request.POST.get('purpose')}_{request.POST.get('s_point')}_{request.POST.get('destination')}
                _{request.POST.get("date")}_{request.POST.get("hour")}_{request.POST.get("minute")}
                _{request.POST.get("ampm")}"""

            ,
                "purpose": request.POST.get('purpose'),
                "s_point": request.POST.get('s_point'),
                "destination": request.POST.get('destination'),
                "type": request.POST.get('type'),
                "date": request.POST.get("date"),
                "hour": request.POST.get("hour"),
                "minute":  request.POST.get("minute"),
                "ampm": request.POST.get("ampm"),
                "details": request.POST.get("details")
            }
        ride_id = request.POST.get('destination')
        attach_user_to_route(request.session['username'], route['_id'])
        if routesDB.find_one({'_id': route['_id']}) == None:
            routesDB.insert_one(route)
            print("Route added")
            if ridesDB.find_one({'_id': ride_id}) == None:
                ride = {
                    "_id":
                        request.POST.get('destination'),
                    "destination": request.POST.get('destination'),
                    "route_id": [route['_id']]
                }
                ridesDB.insert_one(ride)
                print("Ride Added")
            else:
                ride = ridesDB.find_one({'_id': ride_id})
                ride['route_id'].append(route['_id'])
                ridesDB.update_one({'_id': ride_id},{"$set": {"route_id": ride['route_id']}})
                print("Ride Updated")
        return redirect(display_ride, ride_id=ride_id)
    return render(request, 'publish/publish.html', {"username": request.session['username']})

# def add_route(request):
#     intializeDB()
#     if request.method == 'POST':
#
#         ride = request.POST.get('ride')
#         ride = ride.replace("\'", "\"")
#         ride = json.loads(ride)
#         ride_id = ride['_id']
#         ride = ridesDB.find_one({'_id': ride['_id']})
#         route = {
#                 "_id": str(ride_id)
#                 +"_"+request.POST.get('type')
#                 +"_"+request.POST.get('spoint')
#                 +"_"+request.POST.get("hour")
#                 +"_"+request.POST.get("minute")
#                 +"_"+request.POST.get("duration")
#                 +"_"+request.POST.get("details")
#                 +"_"+request.POST.get("ampm"),
#
#                 "type": request.POST.get('type'),
#                 "spoint": request.POST.get('spoint'),
#                 "hour": request.POST.get("hour"),
#                 "minute":  request.POST.get("minute"),
#                 "duration": request.POST.get("duration"),
#                 "details": request.POST.get("details"),
#                 "ampm": request.POST.get("ampm"),
#                 "users": [request.session['username']]
#             }
#         request.session["route"] = route
#         request.session["ride"] = ride
#         attachUserToRoute(request.session['username'], route["_id"], ride_id)
#         #check if route is unique
#         if routesDB.find_one({'_id': route["_id"]})== None:
#             routesDB.insert_one(route)
#             if 'routes' not in ride:
#                 ridesDB.update_one({"_id": ride_id}, {"$set": {"routes": [route['_id']]}})
#             else:
#                 ride['routes'].append(route['_id'])
#                 ridesDB.update_one({"_id": ride_id}, {"$set": {"routes": ride['routes']}})
#         return redirect(display_ride, ride_id=request.session['ride']['_id'] )
#
#     return render(request, 'publish/publish.html', {"username": request.session['username']})

def attach_user_to_route(username, route_id):
    intializeDB()
    user = userDB.find_one({"username": username})
    if user == None:
        return redirect('home/home.html', {"username": None})

    user['rides'].append(route_id)
    userDB.update_one({"username": username},{"$set": {"rides": user['rides']}})
    print("route added for user")

    # rides = user['rides']
    # #remove other routes for this user and ride
    # for route in rides.copy():
    #     if ride_id in route:
    #         rides.remove(route)
    #         #remove user from other routes for this ride
    #         print("foudn ride id in route")
    #         route_instance = routesDB.find_one({'_id': route})
    #         print("route inst",route_instance)
    #         if route_instance:
    #             print("found, removing user: ",username)
    #             users = route_instance['users']
    #             print("prev users: ",users)
    #             users.remove(username)
    #             print("now: ",users)
    #             routesDB.update_one({"_id": route}, {"$set": {"users": users}})
    #
    # rides.append(route_id)
    # userDB.update_one({"username": username}, {"$set": {"rides": rides}})
    # # print(rides)
    # route_instance = routesDB.find_one({'_id': route_id})
    # if route_instance:
    #     users = route_instance['users']
    #     users.append(username)
    #     routesDB.update_one({"_id": route_id}, {"$set": {"users": users}})

# Add Edit functionality

# Add Delete functionality


