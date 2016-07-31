import sys
import time
import asyncio
import threading
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from trackutils import *
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject

class Controller:
    def __init__(self, viewHandler):
        self.viewHandler = viewHandler

    def initDatabase(self, callback):
        work_thread = threading.Thread(target=self.run_initDatabase, args=(callback,))
        work_thread.start()

    def run_initDatabase(self, callback):
        self.engine = create_engine('sqlite:///tracker.db', echo=True)
        Base.metadata.create_all(self.engine)
        sessionMaker = sessionmaker(bind=self.engine)
        session = sessionMaker()
        generateTestActivities(session)
        session.commit()
        GLib.idle_add(callback)
    
    def loadActivities(self, callback):
        work_thread = threading.Thread(target=self.run_loadActivities, args=(callback,))
        work_thread.start()

    def run_loadActivities(self, callback):
        sessionMaker = sessionmaker(bind=self.engine)
        session = sessionMaker()
        activities  = session.query(Activity).all()
        GLib.idle_add(self.viewHandler.showActivities, activities)
        return
        
class Handler:
    def __init__(self, controller):
        self.controller = controller
    def onWindowCreated(self, *args):
        self.controller.initDatabase(self.onDatabaseLoaded)
    def onDeleteWindow(self, *args):
        Gtk.main_quit(*args)
    def onButtonClicked(self, *args):
        print("coucou")
    def onDatabaseLoaded(self, *args):
        self.controller.loadActivities(self.onActivitiesLoaded)
    def onActivitiesLoaded(self, *args):
        return

class ViewHandler:
    def __init__(self):
        return
    def start(self, handler):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("test.glade")
        self.builder.connect_signals(handler)
        self.win = self.builder.get_object("window1")
        self.win.show_all()
        handler.onWindowCreated()

    def showActivities(self, activities):
        activityList = self.builder.get_object("activityList")
        print(activities)
        for activity in activities:
            activityList.add(ActivityListItem(activity))
        
class ActivityListItem(Gtk.ListBoxRow):
    def __init__(self, activity):
        Gtk.ListBoxRow.__init__(self)
        label = Gtk.Label(activity.name)
        self.add(label)

def generateTestActivities(session):
    activity0 = Activity(name="Test activity 0", startTime =1469889840)
    gpsTrack0 = GpsTrack()
    gpsPoint0 = GpsPoint(seqNumber=0, lat=0.0, lon=0.0, ele=300.0)
    gpsPoint1 = GpsPoint(seqNumber=1, lat=0.1, lon=0.0, ele=300.0)
    activity1 = Activity(name="Test activity 1", startTime =1469889840)
    gpsTrack0.gpsPoints = [gpsPoint0, gpsPoint1]
    gpsTrack1 = GpsTrack()
    activity0.gpsTrack = gpsTrack0
    activity1.gpsTrack = gpsTrack1
    gpsTrack0.activity = activity0
    gpsTrack1.activity = activity1
    session.add(activity0)
    session.add(activity1)

if __name__ == "__main__":
    viewHandler = ViewHandler()
    controller = Controller(viewHandler)
    handler = Handler(controller)
    viewHandler.start(handler)
    
    # activity_load  = session.query(Activity).first()
    # print(activity_load)
    Gtk.main()
