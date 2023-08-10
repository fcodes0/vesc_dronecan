#!/usr/bin/env python3

import dronecan, math, time
from dronecan import uavcan
from dronecan import dsdl

from argparse import ArgumentParser
parser = ArgumentParser(description='dump all DroneCAN messages')
parser.add_argument("--bitrate", default=1000000, type=int, help="CAN bit rate")
parser.add_argument("--node-id", default=100, type=int, help="CAN node ID")
parser.add_argument("--dna-server", action='store_true', default=False, help="run DNA server")
parser.add_argument("port", default=None, type=str, help="serial port")
parser.add_argument("--dyno-node-id",default=None,type=int,help="dyno node id")
args = parser.parse_args()

node_info = uavcan.protocol.GetNodeInfo.Response()
node_info.name = 'org.kha.dynodemo'

node = dronecan.make_node(args.port,node_id=args.node_id,node_info=node_info)

node_monitor = dronecan.app.node_monitor.NodeMonitor(node)

if args.dna_server:
    # optionally start a DNA server
    dynamic_node_id_allocator = dronecan.app.dynamic_node_id.CentralizedServer(node, node_monitor)

# callback for printing all messages in human-readable YAML format.
#node.add_handler(None, lambda msg: print(dronecan.to_yaml(msg)))

# callback for printing vesc data
#node.add_handler(dronecan.thirdparty.vesc.RTData, lambda msg: print(dronecan.to_yaml(msg)))
#node.add_handler(dronecan.thirdparty.vesc.RTData, lambda msg: print(msg))
def get_dyno_power(event):
    # print(args.dyno_node_id)
    # print(type(event.transfer.source_node_id))
    if event.transfer.source_node_id == args.dyno_node_id:
        #print(dronecan.to_yaml(event))
        dynopower = float(str(event.transfer.payload._fields["curr_in"]))*float(str(event.transfer.payload._fields["volt_in"]))
        print(f'Dyno Power:{dynopower}')
        publish_throttle_setpoint(dynopower)
        #return dynopower

last_run_time = None
integrator = 0.
# Publishing setpoint values from this function; it is invoked periodically from the node thread.
def publish_throttle_setpoint(dynopower):
    global last_run_time, integrator
    # if args.send_safety:
    #     # optionally send safety off messages. These are needed for some ESCs
    #     message = dronecan.ardupilot.indication.SafetyState()
    #     message.status = message.STATUS_SAFETY_OFF
    #     node.broadcast(message)
    #     print(dronecan.to_yaml(message))

    # Generating a sine wave
    rpm_setpoint = 1000
    # Commanding ESC with indices 0, 1, 2, 3 only
    kp = 20
    ki = 100.0
    dynopower_target = -20
    dynopower_error = dynopower_target-dynopower
    tnow = time.monotonic()
    if last_run_time is None:
        dt = 0
    else:
        dt = tnow-last_run_time
    last_run_time = tnow
    integrator += ki*dt*dynopower_error
    current_setpoint = kp*dynopower_error
    commands = [int(round(rpm_setpoint)), int(round(-(current_setpoint+integrator))), 0, 0]
    message = dronecan.uavcan.equipment.esc.RawCommand(cmd=commands)
    node.broadcast(message)
    # display the message on the console in human readable format
    print(dronecan.to_yaml(message))


# TODO:
# we need to implement a PID controller on the output of the dyno vesc, when test vesc is running, to adjust current on the test vesc motor in order to keep the dyno power output at a set value (e.g 100W)
# SP (setpoint) = e.g 100W
# PV (process value)
# CO (controller output)
# MV (manipulated variable)
# FCE (final control element)

node.add_handler(dronecan.thirdparty.vesc.RTData, get_dyno_power)
#node.periodic(0.01,publish_throttle_setpoint)
#node_monitor.get()

# Running the node until the application is terminated or until first error.
try:
    node.spin()
except KeyboardInterrupt:
    pass