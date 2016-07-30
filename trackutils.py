# import gpxpy.parser as parser
import matplotlib.pyplot as plt
import numpy as np
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class Activity(Base):
    __tablename__ = 'activities'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    startTime = Column(Integer)
    gpsTrack = relationship("GpsTrack", uselist=False, back_populates="activity")
    def __repr__(self):
        res = "Activity name: " + self.name + "\n"
        for gpsPoint in self.gpsTrack.gpsPoints:
            res += "Gps point at " + str(gpsPoint.lat)+ " " + str(gpsPoint.lon)+ " " + str(gpsPoint.ele) + "\n"
        return res

class ActivityFactory:
    def activityFromGpx(fileName):
        return

class GpsTrack(Base):
    __tablename__ = 'gpstracks'
    id = Column(Integer, primary_key=True)
    activityId = Column(Integer, ForeignKey('activities.id'))
    activity = relationship("Activity", back_populates="gpsTrack")
    gpsPoints = relationship("GpsPoint", back_populates="gpsTrack")


class GpsPoint(Base):
    __tablename__ = 'gpspoints'
    id = Column(Integer, primary_key=True)
    seqNumber = Column(Integer)
    lat = Column(Float)
    lon = Column(Float)
    ele = Column(Float)
    gpsTrackId = Column(Integer, ForeignKey('gpstracks.id'))
    gpsTrack = relationship("GpsTrack", back_populates="gpsPoints")
