# CORE Services

* Table of Contents
{:toc}

## Services

CORE uses the concept of services to specify what processes or scripts run on a
node when it is started. Layer-3 nodes such as routers and PCs are defined by
the services that they run.

Services may be customized for each node, or new custom services can be
created. New node types can be created each having a different name, icon, and
set of default services. Each service defines the per-node directories,
configuration files, startup index, starting commands, validation commands,
shutdown commands, and meta-data associated with a node.

> **NOTE:** **Network namespace nodes do not undergo the normal Linux boot process**
   using the **init**, **upstart**, or **systemd** frameworks. These
   lightweight nodes use configured CORE *services*.

## Available Services

| Service Group | Services |
|---|---|
|[BIRD](services/bird.md)|BGP, OSPF, RADV, RIP, Static|
|[EMANE](services/emane.md)|Transport Service|
|[FRR](services/frr.md)|BABEL, BGP, OSPFv2, OSPFv3, PIMD, RIP, RIPNG, Zebra|
|[NRL](services/nrl.md)|arouted, MGEN Sink, MGEN Actor, NHDP, OLSR, OLSRORG, OLSRv2, SMF|
|[Quagga](services/quagga.md)|BABEL, BGP, OSPFv2, OSPFv3, OSPFv3 MDR, RIP, RIPNG, XPIMD, Zebra|
|[SDN](services/sdn.md)|OVS, RYU|
|[Security](services/security.md)|Firewall, IPsec, NAT, VPN Client, VPN Server|
|[Utility](services/utility.md)|ATD, Routing Utils, DHCP, FTP, IP Forward, PCAP, RADVD, SSF, UCARP|
|[XORP](services/xorp.md)|BGP, OLSR, OSPFv2, OSPFv3, PIMSM4, PIMSM6, RIP, RIPNG, Router Manager|

## Node Types and Default Services

Here are the default node types and their services:

| Node Type | Services |
|---|---|
| *router* | zebra, OSFPv2, OSPFv3, and IPForward services for IGP link-state routing. |
| *host* | DefaultRoute and SSH services, representing an SSH server having a default route when connected directly to a router. |
| *PC* | DefaultRoute service for having a default route when connected directly to a router. |
| *mdr* | zebra, OSPFv3MDR, and IPForward services for wireless-optimized MANET Designated Router routing. |
| *prouter* | a physical router, having the same default services as the *router* node type; for incorporating Linux testbed machines into an emulation. |

Configuration files can be automatically generated by each service. For
example, CORE automatically generates routing protocol configuration for the
router nodes in order to simplify the creation of virtual networks.

To change the services associated with a node, double-click on the node to
invoke its configuration dialog and click on the *Services...* button,
or right-click a node a choose *Services...* from the menu.
Services are enabled or disabled by clicking on their names. The button next to
each service name allows you to customize all aspects of this service for this
node. For example, special route redistribution commands could be inserted in
to the Quagga routing configuration associated with the zebra service.

To change the default services associated with a node type, use the Node Types
dialog available from the *Edit* button at the end of the Layer-3 nodes
toolbar, or choose *Node types...* from the  *Session* menu. Note that
any new services selected are not applied to existing nodes if the nodes have
been customized.

The node types are saved in a **~/.core/nodes.conf** file, not with the
**.imn** file. Keep this in mind when changing the default services for
existing node types; it may be better to simply create a new node type. It is
recommended that you do not change the default built-in node types. The
**nodes.conf** file can be copied between CORE machines to save your custom
types.

## Customizing a Service

A service can be fully customized for a particular node. From the node's
configuration dialog, click on the button next to the service name to invoke
the service customization dialog for that service.
The dialog has three tabs for configuring the different aspects of the service:
files, directories, and startup/shutdown.

> **NOTE:** A **yellow** customize icon next to a service indicates that service
   requires customization (e.g. the *Firewall* service).
   A **green** customize icon indicates that a custom configuration exists.
   Click the *Defaults* button when customizing a service to remove any
   customizations.

The Files tab is used to display or edit the configuration files or scripts that
are used for this service. Files can be selected from a drop-down list, and
their contents are displayed in a text entry below. The file contents are
generated by the CORE daemon based on the network topology that exists at
the time the customization dialog is invoked.

The Directories tab shows the per-node directories for this service. For the
default types, CORE nodes share the same filesystem tree, except for these
per-node directories that are defined by the services. For example, the
**/var/run/quagga** directory needs to be unique for each node running
the Zebra service, because Quagga running on each node needs to write separate
PID files to that directory.

> **NOTE:** The **/var/log** and **/var/run** directories are
   mounted uniquely per-node by default.
   Per-node mount targets can be found in **/tmp/pycore.nnnnn/nN.conf/**
   (where *nnnnn* is the session number and *N* is the node number.)

The Startup/shutdown tab lists commands that are used to start and stop this
service. The startup index allows configuring when this service starts relative
to the other services enabled for this node; a service with a lower startup
index value is started before those with higher values. Because shell scripts
generated by the Files tab will not have execute permissions set, the startup
commands should include the shell name, with
something like ```sh script.sh```.

Shutdown commands optionally terminate the process(es) associated with this
service. Generally they send a kill signal to the running process using the
*kill* or *killall* commands. If the service does not terminate
the running processes using a shutdown command, the processes will be killed
when the *vnoded* daemon is terminated (with *kill -9*) and
the namespace destroyed. It is a good practice to
specify shutdown commands, which will allow for proper process termination, and
for run-time control of stopping and restarting services.

Validate commands are executed following the startup commands. A validate
command can execute a process or script that should return zero if the service
has started successfully, and have a non-zero return value for services that
have had a problem starting. For example, the *pidof* command will check
if a process is running and return zero when found. When a validate command
produces a non-zero return value, an exception is generated, which will cause
an error to be displayed in the Check Emulation Light.

> **NOTE:** To start, stop, and restart services during run-time, right-click a
   node and use the *Services...* menu.

## New Services

Services can save time required to configure nodes, especially if a number
of nodes require similar configuration procedures. New services can be
introduced to automate tasks.

### Leveraging UserDefined

The easiest way to capture the configuration of a new process into a service
is by using the **UserDefined** service. This is a blank service where any
aspect may be customized. The UserDefined service is convenient for testing
ideas for a service before adding a new service type.

### Creating New Services

1. Modify the [Example Service File](../daemon/examples/myservices/sample.py)
   to do what you want. It could generate config/script files, mount per-node
   directories, start processes/scripts, etc. sample.py is a Python file that
   defines one or more classes to be imported. You can create multiple Python
   files that will be imported. Add any new filenames to the __init__.py file.

2. Put these files in a directory such as /home/username/.core/myservices
   Note that the last component of this directory name **myservices** should not
   be named something like **services** which conflicts with an existing Python
   name (the syntax 'from myservices import *' is used).

3. Add a **custom_services_dir = /home/username/.core/myservices** entry to the
   /etc/core/core.conf file.

   **NOTE:**
   The directory name used in **custom_services_dir** should be unique and
   should not correspond to
   any existing Python module name. For example, don't use the name **subprocess**
   or **services**.

4. Restart the CORE daemon (core-daemon). Any import errors (Python syntax)
   should be displayed in the /var/log/core-daemon.log log file (or on screen).

5. Start using your custom service on your nodes. You can create a new node
   type that uses your service, or change the default services for an existing
   node type, or change individual nodes.

If you have created a new service type that may be useful to others, please
consider contributing it to the CORE project.
