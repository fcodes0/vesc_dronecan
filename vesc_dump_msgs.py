#!/usr/bin/env python3

import dronecan
from dronecan import uavcan
from dronecan import dsdl

from argparse import ArgumentParser
parser = ArgumentParser(description='dump all DroneCAN messages')
parser.add_argument("--bitrate", default=1000000, type=int, help="CAN bit rate")
parser.add_argument("--node-id", default=100, type=int, help="CAN node ID")
parser.add_argument("--dna-server", action='store_true', default=False, help="run DNA server")
parser.add_argument("port", default=None, type=str, help="serial port")
args = parser.parse_args()



node = dronecan.make_node(args.port)

node_monitor = dronecan.app.node_monitor.NodeMonitor(node)

if args.dna_server:
    # optionally start a DNA server
    dynamic_node_id_allocator = dronecan.app.dynamic_node_id.CentralizedServer(node, node_monitor)

# callback for printing all messages in human-readable YAML format.
#node.add_handler(None, lambda msg: print(dronecan.to_yaml(msg)))

# callback for printing vesc data
node.add_handler(dronecan.thirdparty.vesc.RTData, lambda msg: print(dronecan.to_yaml(msg)))


# Running the node until the application is terminated or until first error.
try:
    node.spin()
except KeyboardInterrupt:
    pass
