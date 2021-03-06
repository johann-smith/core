"""
sdn.py defines services to start Open vSwitch and the Ryu SDN Controller.
"""

import re

import netaddr

from core.services.coreservices import CoreService


class SdnService(CoreService):
    """
    Parent class for SDN services.
    """

    group = "SDN"

    @classmethod
    def generate_config(cls, node, filename):
        return ""


class OvsService(SdnService):
    name = "OvsService"
    executables = ("ovs-ofctl", "ovs-vsctl")
    group = "SDN"
    dirs = ("/etc/openvswitch", "/var/run/openvswitch", "/var/log/openvswitch")
    configs = ("OvsService.sh",)
    startup = ("sh OvsService.sh",)
    shutdown = ("killall ovs-vswitchd", "killall ovsdb-server")

    @classmethod
    def generate_config(cls, node, filename):
        # Check whether the node is running zebra
        has_zebra = 0
        for s in node.services:
            if s.name == "zebra":
                has_zebra = 1

        cfg = "#!/bin/sh\n"
        cfg += "# auto-generated by OvsService (OvsService.py)\n"
        cfg += "## First make sure that the ovs services are up and running\n"
        cfg += "/etc/init.d/openvswitch-switch start < /dev/null\n\n"
        cfg += "## create the switch itself, set the fail mode to secure, \n"
        cfg += "## this stops it from routing traffic without defined flows.\n"
        cfg += "## remove the -- and everything after if you want it to act as a regular switch\n"
        cfg += "ovs-vsctl add-br ovsbr0 -- set Bridge ovsbr0 fail-mode=secure\n"

        cfg += "\n## Now add all our interfaces as ports to the switch\n"
        portnum = 1
        for ifc in node.netifs():
            if hasattr(ifc, "control") and ifc.control is True:
                continue
            ifnumstr = re.findall(r"\d+", ifc.name)
            ifnum = ifnumstr[0]

            # create virtual interfaces
            cfg += "## Create a veth pair to send the data to\n"
            cfg += "ip link add rtr%s type veth peer name sw%s\n" % (ifnum, ifnum)

            # remove ip address of eths because quagga/zebra will assign same IPs to rtr interfaces
            # or assign them manually to rtr interfaces if zebra is not running
            for ifcaddr in ifc.addrlist:
                addr = ifcaddr.split("/")[0]
                if netaddr.valid_ipv4(addr):
                    cfg += "ip addr del %s dev %s\n" % (ifcaddr, ifc.name)
                    if has_zebra == 0:
                        cfg += "ip addr add %s dev rtr%s\n" % (ifcaddr, ifnum)
                elif netaddr.valid_ipv6(addr):
                    cfg += "ip -6 addr del %s dev %s\n" % (ifcaddr, ifc.name)
                    if has_zebra == 0:
                        cfg += "ip -6 addr add %s dev rtr%s\n" % (ifcaddr, ifnum)
                else:
                    raise ValueError("invalid address: %s" % ifcaddr)

            # add interfaces to bridge
            # Make port numbers explicit so they're easier to follow in reading the script
            cfg += "## Add the CORE interface to the switch\n"
            cfg += (
                "ovs-vsctl add-port ovsbr0 eth%s -- set Interface eth%s ofport_request=%d\n"
                % (ifnum, ifnum, portnum)
            )
            cfg += "## And then add its sibling veth interface\n"
            cfg += (
                "ovs-vsctl add-port ovsbr0 sw%s -- set Interface sw%s ofport_request=%d\n"
                % (ifnum, ifnum, portnum + 1)
            )
            cfg += "## start them up so we can send/receive data\n"
            cfg += "ovs-ofctl mod-port ovsbr0 eth%s up\n" % ifnum
            cfg += "ovs-ofctl mod-port ovsbr0 sw%s up\n" % ifnum
            cfg += "## Bring up the lower part of the veth pair\n"
            cfg += "ip link set dev rtr%s up\n" % ifnum
            portnum += 2

        # Add rule for default controller if there is one local (even if the controller is not local, it finds it)
        cfg += "\n## We assume there will be an SDN controller on the other end of this, \n"
        cfg += "## but it will still function if there's not\n"
        cfg += "ovs-vsctl set-controller ovsbr0 tcp:127.0.0.1:6633\n"

        cfg += "\n## Now to create some default flows, \n"
        cfg += "## if the above controller will be present then you probably want to delete them\n"
        # Setup default flows
        portnum = 1
        for ifc in node.netifs():
            if hasattr(ifc, "control") and ifc.control is True:
                continue
            cfg += "## Take the data from the CORE interface and put it on the veth and vice versa\n"
            cfg += (
                "ovs-ofctl add-flow ovsbr0 priority=1000,in_port=%d,action=output:%d\n"
                % (portnum, portnum + 1)
            )
            cfg += (
                "ovs-ofctl add-flow ovsbr0 priority=1000,in_port=%d,action=output:%d\n"
                % (portnum + 1, portnum)
            )
            portnum += 2

        return cfg


class RyuService(SdnService):
    name = "ryuService"
    executables = ("ryu-manager",)
    group = "SDN"
    dirs = ()
    configs = ("ryuService.sh",)
    startup = ("sh ryuService.sh",)
    shutdown = ("killall ryu-manager",)

    @classmethod
    def generate_config(cls, node, filename):
        """
        Return a string that will be written to filename, or sent to the
        GUI for user customization.
        """
        cfg = "#!/bin/sh\n"
        cfg += "# auto-generated by ryuService (ryuService.py)\n"
        cfg += (
            "ryu-manager --observe-links ryu.app.ofctl_rest ryu.app.rest_topology &\n"
        )
        return cfg
