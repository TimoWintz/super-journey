import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from trackutils import *
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class Handler:
    def onDeleteWindow(self, *args):
        Gtk.main_quit(*args)

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
    engine = create_engine('sqlite:///:memory:', echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    generateTestActivities(session)
    builder = Gtk.Builder()
    builder.add_from_file("test.glade")
    builder.connect_signals(Handler())
    win = builder.get_object("window1")
    win.show_all()
    Gtk.main()
    activity_load  = session.query(Activity).first()
    print(activity_load)
