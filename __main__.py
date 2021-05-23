import argparse
import sys
import pathlib

from concurrent import futures
import logging

import grpc
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2

import PythonServer_pb2
import PythonServer_pb2_grpc

empty = google_dot_protobuf_dot_empty__pb2.Empty()

def validLocation(stub,location):
    response_iterator = stub.GetLocations(empty)
    locations = [ location.Location for location in response_iterator ]
    return location in locations

def printEvent(e):
    print(f"{e.DateTime} {e.Location}:{e.MeasType}={e.MeasValue}")

def getLatest(stub):
    response_iterator = stub.GetLatestEvents(empty)
    for response in response_iterator:
        printEvent(response)

def getMinimumEvents(stub):
    response_iterator = stub.GetMinimumEvents(empty)
    for response in response_iterator:
        printEvent(response)

def getMaximumEvents(stub):
    response_iterator = stub.GetMaximumEvents(empty)
    for response in response_iterator:
        printEvent(response)

def getUnknownEvents(stub):
    response_iterator = stub.GetUnknownEvents(empty)
    for response in response_iterator:
        printEvent(response)

def getLocations(stub):
    response_iterator = stub.GetLocations(empty)
    for location in response_iterator:
        print(f"{location.Location}:{location.MeasType}")

def getLocationEvents(stub,locationDesc):
    if ':' in locationDesc:
        (location,measType)=locationDesc.split(':')
    else:
        (location,measType) = (locationDesc,"")

    if not validLocation(stub,location):
        raise RuntimeError(f"Location {location} not found")

    request = PythonServer_pb2.Location(
                    Location = location,
                    MeasType = measType)
    response_iterator = stub.GetLocationEvents(request)
    for response in response_iterator:
        printEvent(response)

def getAllEvents(stub):
    response_iterator = stub.GetAllEvents(empty)
    for response in response_iterator:
        printEvent(response)

def getSummaryEvents(stub):
    response_iterator = stub.GetSummaryEvents(empty)
    for response in response_iterator:
        printEvent(response)

def configSensor(stub,config):
    if config.count('=') != 1:
        raise RuntimeError("Configuration should be of form ID=LOCATION")

    (location,sensorId)=config.split(':')
    if (len(location) == 0) or (len(sensorId)==0):
        raise RuntimeError("Configuration should be of form ID=LOCATION")

    if not validLocation( stub, location ):
        raise RuntimeError(f"Location {location} not found")

    request = PythonServer_pb2.SensorConfig(SensorId = sensorId, Location = location)
    stub.ConfigSensor( request )

def deleteSensor(stub,sensorId):
    request = PythonServer_pb2.SensorId(SensorId = sensorId)
    stub.DeleteSensor( request )

def getSensorInfo(stub):
    for r in stub.GetSensorInfo(empty):
        print(f"{r.SensorId},{r.Location},{r.LastSeen}")

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-S", "--server", help="Server Name", default="webpi2")
    parser.add_argument("-P", "--port", type=int, help="Server Port", default=50051)

    cmdGroup = parser.add_mutually_exclusive_group(required=True)
    cmdGroup.add_argument("-l","--latest",action='store_true',default=False,help="Get latest events")
    cmdGroup.add_argument("-m","--minimum",action='store_true',default=False,help="Get minimum events")
    cmdGroup.add_argument("-M","--maximum",action='store_true',default=False,help="Get maximum events")
    cmdGroup.add_argument("-u","--unknown",action='store_true',default=False,help="Get unkown events")
    cmdGroup.add_argument("-L","--locations",action='store_true',default=False,help="Get location list")
    cmdGroup.add_argument("-E","--location_events",action='store',type=str,default=None,help="Get events for location")
    cmdGroup.add_argument("-s","--summary",action='store_true',default=False,help="Get summary of events")
    cmdGroup.add_argument("-a","--all",action='store_true',default=False,help="Get all cached events")
    cmdGroup.add_argument("-f","--config_sensor",action='store',type=str,default=None,help="Config sensor; ID=LOCATION")
    cmdGroup.add_argument("-d","--delete_sensor",action='store',type=str,default=None,help="Delete sensor")
    cmdGroup.add_argument("-D","--delete_climemet",action='store_true',default=False,help="Delete ClimeMet sensors")
    cmdGroup.add_argument("-U","--delete_unseen",action='store_true',default=False,help="Delete sensors for which no events have been seen.")
    cmdGroup.add_argument("-i","--sensor_info",action='store_true',default=False,help="Get sensor info for all sensors.")

    parser.add_argument("-c","--clear_unknown",action='store_true',default=False,help="Clear unknown events")

    args = parser.parse_args()


    with grpc.insecure_channel(target="{}:{}".format(args.server, args.port),
                            options=[('grpc.lb_policy_name', 'pick_first'),
                                    ('grpc.enable_retries', 0),
                                    ('grpc.keepalive_timeout_ms', 10000)
                                    ]) as channel:
        stub = PythonServer_pb2_grpc.EventServerStub(channel)

        if args.latest: getLatest(stub)
        if args.minimum: getMinimumEvents(stub)
        if args.maximum: getMaximumEvents(stub)
        if args.unknown: getUnknownEvents(stub)
        if args.clear_unknown: stub.ClearUnknownEvents(empty)
        if args.locations: getLocations(stub)
        if args.location_events != None: getLocationEvents(stub,args.location_events)
        if args.summary: getSummaryEvents(stub)
        if args.all: getAllEvents(stub)
        if args.config_sensor: configSensor(stub,args.config_sensor)
        if args.delete_sensor: deleteSensor(stub,args.delete_sensor)
        if args.delete_climemet: stub.DeleteClimeMet(empty)
        if args.delete_unseen: stub.DeleteUnseenSensors(empty)
        if args.sensor_info: getSensorInfo(stub)

if __name__ == "__main__":
    # execute only if run as a script
    main()
