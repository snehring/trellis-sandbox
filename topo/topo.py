#!/usr/bin/python
# Copyright 2019-present Open Networking Foundation
# SPDX-License-Identifier: Apache-2.0

from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import Host
from mininet.topo import Topo
from stratum import StratumBmv2Switch


class RoutedHost(Host):
    """Host that can be configured with multiple IP addresses."""

    def __init__(self, name, ips, gateway, *args, **kwargs):
        super(RoutedHost, self).__init__(name, *args, **kwargs)
        self.ips = ips
        self.gateway = gateway

    def config(self, **kwargs):
        Host.config(self, **kwargs)
        self.cmd('ip -4 addr flush dev %s' % self.defaultIntf())
        for ip in self.ips:
            self.cmd('ip addr add %s dev %s' % (ip, self.defaultIntf()))
        self.cmd('ip route add default via %s' % self.gateway)
        # Disable offload
        for attr in ["rx", "tx", "sg"]:
            cmd = "/sbin/ethtool --offload %s %s off" % (self.defaultIntf(), attr)
            self.cmd(cmd)


class TaggedRoutedHost(RoutedHost):
    """Host that can be configured with multiple IP addresses."""

    def __init__(self, name, ips, gateway, vlan, *args, **kwargs):
        super(RoutedHost, self).__init__(name, *args, **kwargs)
        self.ips = ips
        self.gateway = gateway
        self.vlan = vlan
        self.vlanIntf = None

    def config(self, **kwargs):
        Host.config(self, **kwargs)
        self.vlanIntf = "%s.%s" % (self.defaultIntf(), self.vlan)
        self.cmd('ip -4 addr flush dev %s' % self.defaultIntf())
        self.cmd('ip link add link %s name %s type vlan id %s' % (
            self.defaultIntf(), self.vlanIntf, self.vlan))
        self.cmd('ip link set up %s' % self.vlanIntf)
        # Set ips and gateway
        for ip in self.ips:
            self.cmd('ip addr add %s dev %s' % (ip, self.vlanIntf))
        self.cmd('ip route add default via %s' % self.gateway)
        # Update the intf name and host's intf map
        self.defaultIntf().name = self.vlanIntf
        self.nameToIntf[self.vlanIntf] = self.defaultIntf()
        # Disable offload
        for attr in ["rx", "tx", "sg"]:
            cmd = "/sbin/ethtool --offload %s %s off" % (self.vlanIntf, attr)
            self.cmd(cmd)

    def terminate(self, **kwargs):
        self.cmd('ip link remove link %s' % self.vlanIntf)
        super(TaggedRoutedHost, self).terminate()


class LeafSpineTopo(Topo):
    "Trellis basic topology"

    def __init__(self, *args, **kwargs):
        Topo.__init__(self, *args, **kwargs)

        # Leaves
        leaf1 = self.addSwitch('leaf1')  # gRPC 50001
        leaf2 = self.addSwitch('leaf2')  # gRPC 50002
        leaf3 = self.addSwitch('leaf3')  # gRPC 50003
        leaf4 = self.addSwitch('leaf4')  # gRPC 50004

        # Spines
        spine1 = self.addSwitch('spine1')  # gRPC 50005
        spine2 = self.addSwitch('spine2')  # gRPC 50006

        # Links
        self.addLink(spine1, leaf1)
        self.addLink(spine1, leaf2)
        self.addLink(spine1, leaf3)
        self.addLink(spine1, leaf4)
        self.addLink(spine2, leaf1)
        self.addLink(spine2, leaf2)
        self.addLink(spine2, leaf3)
        self.addLink(spine2, leaf4)
        self.addLink(leaf3, leaf4, port1=30, port2=30)

        # IPv4 Hosts
        h1 = self.addHost('h1', cls=RoutedHost, mac='00:aa:00:00:00:01',
                          ips=['10.0.2.1/24'], gateway='10.0.2.254')
        h2 = self.addHost('h2', cls=TaggedRoutedHost, mac='00:aa:00:00:00:02',
                          ips=['10.0.2.2/24'], gateway='10.0.2.254', vlan=10)
        h3 = self.addHost('h3', cls=RoutedHost, mac='00:aa:00:00:00:03',
                          ips=['10.0.3.1/24'], gateway='10.0.3.254')
        h4 = self.addHost('h4', cls=TaggedRoutedHost, mac='00:aa:00:00:00:04',
                          ips=['10.0.3.2/24'], gateway='10.0.3.254', vlan=20)
        #h5 = self.addHost('h5', cls=TaggedRoutedHost, mac='00:aa:00:00:00:05',
        #                  ips=['10.90.2.1/22'], gateway='10.90.3.254', vlan=3421)
        #h6 = self.addHost('h6', cls=TaggedRoutedHost, mac='00:aa:00:00:00:06',
        #                  ips=['10.90.2.2/22'], gateway='10.90.3.254', vlan=3421)
        #h7 = self.addHost('h7', cls=TaggedRoutedHost, mac='00:aa:00:00:00:07',
        #                  ips=['10.90.2.3/22'], gateway='10.90.3.254', vlan=3421)
        #h8 = self.addHost('h8', cls=TaggedRoutedHost, mac='00:aa:00:00:00:08',
        #                  ips=['10.90.2.4/22'], gateway='10.90.3.254', vlan=3421)
        #h9 = self.addHost('h9', cls=TaggedRoutedHost, mac='00:aa:00:00:00:09',
        #                  ips=['10.90.2.5/22'], gateway='10.90.3.254', vlan=3421)
        h5 = self.addHost('h5')
        h6 = self.addHost('h6')
        h7 = self.addHost('h7')
        h8 = self.addHost('h8')
        h9 = self.addHost('h9')
        

        self.addLink(h1, leaf1)
        self.addLink(h2, leaf1)
        self.addLink(h3, leaf2)
        self.addLink(h4, leaf2)
        self.addLink(h5, leaf3)
        self.addLink(h5, leaf4)
        self.addLink(h6, leaf3)
        self.addLink(h6, leaf4)
        self.addLink(h7, leaf3)
        self.addLink(h7, leaf4)
        self.addLink(h8, leaf3)
        self.addLink(h8, leaf4)
        self.addLink(h9, leaf3)
        self.addLink(h9, leaf4)
        

def main():
    net = Mininet(
        topo=LeafSpineTopo(),
        switch=StratumBmv2Switch,
        controller=None)
    net.start()
    for i in range(5, 10):
        host = net.get('h'+str(i))
        host.cmd('modprobe bonding mode=4')
        host.cmd('ip link add bond0 type bond')
        host.cmd('ip link set bond0 address 00:aa:00:00:00:00:0'+str(i))
        host.cmd('ip link set h'+str(i)+'-eth0 down')
        host.cmd('ip link set h'+str(i)+'-eth1 down')
        host.cmd('ip link set h'+str(i)+'-eth0 address 00:aa:00:00:00:00:'+str(i)+'1')
        host.cmd('ip link set h'+str(i)+'-eth1 address 00:aa:00:00:00:00:'+str(i)+'2')
        host.cmd('ip link set h'+str(i)+'-eth0 master bond0')
        host.cmd('ip link set h'+str(i)+'-eth1 master bond0')
        host.cmd('ip addr add 10.90.2.'+str(i-4)+'/22 dev bond0')
        host.cmd('ip link set bond0 up')

    CLI(net)
    net.stop()


if __name__ == "__main__":
    setLogLevel('info')
    main()
