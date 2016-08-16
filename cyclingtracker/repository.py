import time, callback, gpxpy, datetime, math, sys
from enum import Enum
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, subqueryload
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class Activity(Base):
    __tablename__ = 'activities'
    id = Column(Integer, primary_key = True)
    name = Column(String)
    start_timestamp = Column(Integer)
    duration = Column(Integer)
    length = Column(Float)
    total_ascent = Column(Integer)
    gps_track = relationship("GpsTrack", uselist=False, back_populates="activity",
        cascade="all, delete, delete-orphan")

    def to_markup(self):
        return "<big><b>" + self.name + "</b></big>\n" +\
            "<b>Départ</b> : " + (datetime.datetime.fromtimestamp(self.start_timestamp)).ctime() + "\n" +\
            "<b>Longueur</b> : " + str(round(self.length/1000, 1)) + "km\n" +\
            "<b>Dénivelé pos.</b> : " + str(self.total_ascent) + "m\n" +\
            "<b>Durée totale</b> : " + str(math.floor(self.duration/3600)) + "h " + str(math.floor(self.duration/60)%60) + "m";

class GpsPoint(Base):
    __tablename__ = 'gpspoints'
    id = Column(Integer, primary_key=True)
    seq_number = Column(Integer)
    timestamp = Column(Integer)
    latitude = Column(Float)
    longitude = Column(Float)
    elevation = Column(Float)
    cumulative_length = Column(Float)
    gps_track_id = Column(Integer, ForeignKey('gpstracks.id'))
    gps_track = relationship("GpsTrack", back_populates="gps_points")

class GpsTrack(Base):
    __tablename__ = 'gpstracks'
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey('activities.id'))
    activity = relationship("Activity", back_populates="gps_track")
    gps_points = relationship("GpsPoint", back_populates="gps_track",
        cascade="all, delete, delete-orphan")
    
    elevation_min = Column(Float)
    elevation_max = Column(Float)

    def __init__(self):
        self.gps_points = []

    def add_point(self, gps_point: GpsPoint):
        self.gps_points.append(gps_point)

    def compute_average_speed():
        raise NotImplementedError
    
    def compute_distance():
        raise NotImplementedError

    def compute_duration():
        raise NotImplementedError

class FileType(Enum):
    fit = 1
    gpx = 2

class Repository(object):
    
    def init_database(self):
        engine = create_engine('sqlite:///db/tracker.db', echo=False, connect_args={'check_same_thread':False})
        Base.metadata.create_all(engine)
        self.session_maker = sessionmaker(bind=engine)

    def import_activity(self, args: callback.ImportActivityMethodArgs, handler: callback.ActivityImportedHandler):
        if args.file_type == FileType.gpx:
            activity = self._import_gpx(args.file_name)
            handler.on_activity_imported(activity)
        else:
            handler.on_activity_imported(activity=None, problem="Opération non supportée")

    def _import_gpx(self, filename):
        gpx_file = open(filename, 'r')
        gpx = gpxpy.parse(gpx_file)

        seq = 0
        start_time = 0
        end_time = 0
        length = 0
        last_location = None

        elevation_min = math.inf
        elevation_max = -math.inf
        db_track = GpsTrack()

        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    if seq == 0:
                        start_time = point.time.timestamp()
                    db_point = GpsPoint()
                    db_point.seq_number = seq
                    db_point.timestamp = point.time.timestamp()
                    db_point.elevation = point.elevation
                    db_point.latitude = point.latitude
                    db_point.longitude = point.longitude
                    
                    end_time = db_point.timestamp
                    location = gpxpy.geo.Location(point.latitude, point.longitude, point.elevation)

                    if last_location:
                        length += last_location.distance_3d(location)
                    
                    db_point.cumulative_length = length
                    db_point.gps_track = db_track
                    db_track.add_point(db_point)

                    if point.elevation < elevation_min:
                        elevation_min = point.elevation
                    if point.elevation > elevation_max:
                        elevation_max = point.elevation

                    seq += 1
                    last_location = location

        db_track.elevation_min = elevation_min
        db_track.elevation_max = elevation_max
        
        db_activity = Activity(name= "Activité de " + str(math.floor(length/1000+0.5)) + " km", start_timestamp= start_time,
            duration= end_time-start_time, length= length, total_ascent= 0)
        db_activity.gps_track = db_track
        db_track.activity = db_activity

        activity = self.save_activity(db_activity)
        return activity

    def save_activity(self, activity: Activity):
        session = self.session_maker()
        session.add(activity)
        session.commit()
        loaded_activity = session.query(Activity)\
            .options(subqueryload(Activity.gps_track).subqueryload(GpsTrack.gps_points))\
            .order_by(Activity.id.desc())\
            .first()
        session.close()
        return loaded_activity

    def get_all_activities(self, args, handler: callback.ActivitiesLoadedHandler):
        #time.sleep(1)
        session = self.session_maker()
        activities = session.query(Activity)\
            .options(subqueryload(Activity.gps_track).subqueryload(GpsTrack.gps_points))\
            .all()
        session.close()

        handler.on_activities_loaded(activities)

    def delete_activity(self, args, handler: callback.ActivityDeletedHandler):
        activity = args
        session = self.session_maker()
        session.delete(activity)
        session.commit()
        session.close()
        handler.on_activity_deleted(activity)
    
    def populate_activities(self):
        activities = \
            [Activity("Grand Ballon", "9/8/2016 08:40", "2:55", 74325, 1225), \
             Activity("Hundsrück", "3/8/2016 15:12", "1:45", 39192, 623), \
             Activity("Ballon d'Alsace", "28/7/2016 07:55", "3:23", 90467, 1336)]

        session = self.session_maker()

        for act in activities:
            session.add(act)

        session.commit()
        