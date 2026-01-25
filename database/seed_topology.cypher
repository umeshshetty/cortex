// Seed Data for Optical Network Topology

// 1. Create Sites
MERGE (ny:Site {code: "NY01", city: "New York", region: "NA"})
MERGE (ldn:Site {code: "LDN01", city: "London", region: "EMEA"})
MERGE (tyo:Site {code: "TYO01", city: "Tokyo", region: "APAC"})

// 2. Create Devices (Routers)
MERGE (r1:Device {hostname: "rtr-ny01-edge", model: "Juniper MX960", role: "Edge"})
MERGE (r2:Device {hostname: "rtr-ldn01-edge", model: "Juniper MX960", role: "Edge"})
MERGE (r3:Device {hostname: "rtr-tyo01-edge", model: "Cisco ASR9k", role: "Edge"})
MERGE (sw1:Device {hostname: "sw-ny01-core", model: "Arista 7280", role: "Core"})

// 3. Locate Devices in Sites
MERGE (r1)-[:LOCATED_IN]->(ny)
MERGE (sw1)-[:LOCATED_IN]->(ny)
MERGE (r2)-[:LOCATED_IN]->(ldn)
MERGE (r3)-[:LOCATED_IN]->(tyo)

// 4. Create Interfaces & Circuits (Topology)
// Trans-Atlantic Link (NY <-> LDN)
MERGE (if1:Interface {name: "et-0/0/0", speed: "100G"})
MERGE (if2:Interface {name: "et-0/0/0", speed: "100G"})
MERGE (r1)-[:HAS_INTERFACE]->(if1)
MERGE (r2)-[:HAS_INTERFACE]->(if2)
MERGE (if1)-[:CONNECTED_TO {circuit_id: "CKT-NY-LDN-001", status: "UP"}]->(if2)

// Inter-Site Link (NY Edge <-> NY Core)
MERGE (if3:Interface {name: "xe-0/0/1", speed: "10G"})
MERGE (if4:Interface {name: "et-1", speed: "10G"})
MERGE (r1)-[:HAS_INTERFACE]->(if3)
MERGE (sw1)-[:HAS_INTERFACE]->(if4)
MERGE (if3)-[:CONNECTED_TO {circuit_id: "INT-NY-001", status: "UP"}]->(if4)
