# Configuration summary

Everything below comes from the report (chapters 3 to 6 and Annex A). It is a summary of the parameters and of the outputs shown in the screenshots, **not** a full `running-config` export. Parameters the report does not state (OSPF process id and area, BGP router ids and neighbour statements, VPCS1 address) are deliberately not filled in.

## Addressing

| Device | Interface | Address |
|---|---|---|
| PE1 (R1) | FastEthernet0/0 (client side) | 192.168.1.254/24 |
| PE1 (R1) | FastEthernet0/1 (backbone) | 10.0.12.1/30 |
| PE1 (R1) | Loopback0 | 1.1.1.1/32 |
| P (R2) | FastEthernet0/0 | 10.0.12.2/30 |
| P (R2) | FastEthernet0/1 | 10.0.23.1/30 |
| P (R2) | Loopback0 | 2.2.2.2/32 |
| PE2 (R3) | FastEthernet0/0 (backbone) | 10.0.23.2/30 |
| PE2 (R3) | FastEthernet0/1 (client side) | 192.168.2.254/24 |
| PE2 (R3) | Loopback0 | 3.3.3.3/32 |
| VPCS2 (Client B) | | 192.168.2.1 |

Routers: Cisco 3725. Clients: VPCS.

## Scenario 1: native MPLS

1. Addressing on all interfaces, OSPF on the backbone. It advertises the three loopbacks (1.1.1.1, 2.2.2.2, 3.3.3.3), on which LDP depends.
2. MPLS enabled on the backbone interfaces. LDP builds sessions PE1-P and P-PE2 and distributes labels for the prefixes learned by OSPF.

## Scenario 2: MPLS L3VPN

| Element | Parameters |
|---|---|
| VRF `CLIENT` | Created on PE1 and PE2. RD `65000:1`. RT export and import `65000:100`. Label allocation per-prefix |
| MP-BGP | iBGP between the loopbacks of PE1 (1.1.1.1) and PE2 (3.3.3.3), AS 65000, address family VPNv4 |
| Transport | LDP label (to the PE2 loopback) plus VPN label (identifies the VRF on the egress PE) |

Order matters on the client interface: attach it to the VRF with `ip vrf forwarding CLIENT` first, then configure the IP address again, because attaching to a VRF removes the address already configured.

## Scenario 3: QoS

Classes defined on PE1 (report figure 23):

| Class | Selection | Used for |
|---|---|---|
| `MARK_VOIP` | Protocol ICMP (recognised by NBAR) | Ingress: selects traffic to mark as voice |
| `CLASSE_VOIP` | DSCP EF (46) | Egress: priority queue |
| `CLASSE_DATA` | DSCP AF11 (10) | Egress: guaranteed bandwidth |
| `class-default` | Everything else | Egress: flow-based fair queueing |

Policy-maps as displayed in the report (figure 24):

```
Policy Map MARKING
  Class MARK_VOIP
    set dscp ef
  Class class-default
    set dscp af11

Policy Map QOS_MPLS_VPN
  Class CLASSE_VOIP
    Strict Priority, Bandwidth 512 (kbps) Burst 12800 (Bytes)
  Class CLASSE_DATA
    Bandwidth 256 (kbps) Max Threshold 64 (packets)
  Class class-default
    Flow based Fair Queueing
```

Client interface of PE1 (report figure 25):

```
interface FastEthernet0/0
 ip vrf forwarding CLIENT
 ip address 192.168.1.254 255.255.255.0
 duplex auto
 speed auto
 service-policy input MARKING
```

`QOS_MPLS_VPN` is applied outbound on the backbone interface (Fa0/1 on PE1). The report states the two levels are configured on PE1 and PE2 but only shows the PE1 interface details.

## Verification commands (report Annex A)

| Command | Device | What it shows |
|---|---|---|
| `show ip ospf neighbor` | P | OSPF neighbours (FULL expected) |
| `show mpls ldp neighbor` | P | LDP sessions (Oper expected) |
| `show mpls forwarding-table` | P, PE1 | Local labels, actions (Pop tag, Aggregate [V]), bytes switched |
| `traceroute 3.3.3.3 source 1.1.1.1` | PE1 | Path and MPLS labels |
| `ping 192.168.2.1` (repeat 1000) | VPCS1 | End-to-end latency and loss |
| `show ip vrf detail` | PE1 | RD, import/export RT, VRF interfaces |
| `show bgp vpnv4 unicast all summary` | PE1 | MP-BGP session and received prefixes |
| `show class-map` | PE1 | Traffic classes and match criteria |
| `show policy-map` | PE1 | Contents of `MARKING` and `QOS_MPLS_VPN` |
| `show running-config interface fa0/0` | PE1 | VRF attachment and applied policy |
| `show policy-map interface fa0/0` | PE1 | Counters of classified and marked packets |
