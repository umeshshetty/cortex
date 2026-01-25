// Cortex Digital Twin Schema
// Defines Uniqueness Constraints and Indexes for Infrastructure Nodes

// 1. Sites (Data Centers)
CREATE CONSTRAINT site_code_unique IF NOT EXISTS
FOR (s:Site) REQUIRE s.code IS UNIQUE;

CREATE INDEX site_city_index IF NOT EXISTS
FOR (s:Site) ON (s.city);

// 2. Devices (Routers, Switches, Optical Gear)
CREATE CONSTRAINT device_hostname_unique IF NOT EXISTS
FOR (d:Device) REQUIRE d.hostname IS UNIQUE;

CREATE INDEX device_type_index IF NOT EXISTS
FOR (d:Device) ON (d.type);

// 3. Interfaces (Ports)
// Composite key might be better (device + name), but for simplicity:
CREATE INDEX interface_name_index IF NOT EXISTS
FOR (i:Interface) ON (i.name);

// 4. Ensuring 'Entity' compatibility (so Agent can find them)
// We might want Devices to also be labeled :Entity?
// Start with explicit labels, and maybe double label them if needed.
