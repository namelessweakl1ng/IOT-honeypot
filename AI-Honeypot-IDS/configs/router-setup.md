# Router setup guide

The lab uses any standard 4-port home router. We use a TP-Link Archer C7 in
this example; any equivalent works.

## 1. Physical setup
1. Plug the router's power adapter in.
2. Connect Computer 1 NIC → router LAN port 1.
3. Connect Computer 2 NIC → router LAN port 2.
4. Connect Computer 3 NIC → router LAN port 3.
5. **LEAVE THE WAN PORT EMPTY.** The router must have no Internet uplink.

## 2. Log in to the router admin UI
- From any connected machine, browse to `http://192.168.1.1`.
- Default admin credentials depend on the router model (often
  `admin/admin` or `admin/password`). Change them.

## 3. LAN configuration
- Set LAN IP to `192.168.1.1` (subnet `255.255.255.0`).
- Disable the DHCP server (we use static IPs) — OR enable DHCP but reserve
  the three lab IPs by MAC so they never change.

## 4. Wi-Fi
- Disable Wi-Fi entirely (we are Ethernet-only for the demo).

## 5. Firewall
- Leave at factory defaults. The lab is air-gapped; the router's stateful
  firewall is sufficient.

## 6. WAN
- Set WAN connection type to "Disabled" / "Dynamic IP" / "None" — whatever
  your router exposes. The WAN cable is unplugged regardless.

## 7. Verify
- From Computer 1: `ping 192.168.1.1` → success.
- From Computer 1: `ping 192.168.1.20` → success.
- From Computer 1: `ping 8.8.8.8` → **FAIL** (air-gap confirmed).
