# Uncertainty Zones and AI Location Estimation

## How the AI Estimates Location

The triangulation system uses different methods depending on how many nodes detect a device. The AI always shows an **uncertainty zone** to indicate the possible area where the device might be located.

## Detection Scenarios

### Scenario 1: Single Node Detection (1 Node)

When only one node detects a device:

```
         MAP AREA
  ┌───────────────────────┐
  │                       │
  │     ╭─────────╮       │
  │    ╱           ╲      │
  │   │   Node 1    │     │  ← Circular uncertainty zone
  │    ╲    📱     ╱      │    (device could be anywhere
  │     ╰─────────╯       │     in this circle)
  │                       │
  │                       │
  └───────────────────────┘
```

**What you see:**
- **Orange dashed circle** around the node
- **Device marker** at the node position
- **Low confidence** (20%)

**Why:** We only know the device is near this node, but not the exact direction or distance.

---

### Scenario 2: Two Node Detection (2 Nodes)

When two nodes detect a device (e.g., walking between Node 1 and Node 2):

```
         MAP AREA
  ┌───────────────────────┐
  │                       │
  │  Node 1  ┌─────────┐  │
  │    📱    │         │  │
  │          │  Zone   │  │  ← Rectangular uncertainty zone
  │          │    📱   │  │    (device is somewhere in
  │          │         │  │     this box between nodes)
  │          └─────────┘  │
  │                  Node 2│
  │                    📱  │
  └───────────────────────┘
```

**What you see:**
- **Orange dashed rectangle** between the two nodes
- **Device marker** positioned based on signal strength (closer to stronger signal)
- **Medium-low confidence** (40%)

**Why:** We know the device is between these two nodes, but can't pinpoint exactly where without the third node.

**Example:** If Node 1 has RSSI -45 dBm (strong) and Node 2 has RSSI -70 dBm (weak), the device marker will be closer to Node 1, and the box shows all possible positions.

---

### Scenario 3: Three Node Detection (3+ Nodes) - Full Triangulation

When all three nodes detect a device:

```
         MAP AREA
  ┌───────────────────────┐
  │      Node 3           │
  │        📱             │
  │       ╱ ╲             │
  │      ╱   ╲            │
  │     ╱  ●  ╲           │  ← Small circular uncertainty
  │    ╱   📱  ╲          │    (high precision)
  │   ╱         ╲         │
  │  📱─────────📱        │
  │ Node 1    Node 2      │
  └───────────────────────┘
```

**What you see:**
- **Small orange dashed circle** around the calculated position
- **Device marker** at precise location
- **High confidence** (66-100%)

**Why:** With three nodes, we can perform full triangulation and calculate an accurate position. The small circle represents measurement uncertainty.

---

## Real-World Example

### Scenario: Walking Through Your House

**Setup:**
```
Kitchen                     Living Room
┌─────────────────────────────────────┐
│                                     │
│  Node 1 📱                          │
│                                     │
│              Hallway                │
│         ╭───────────────╮           │
│        │  You walking   │           │ ← Rectangle shows
│        │  with phone 📱 │           │   possible area
│         ╰───────────────╯           │
│                                     │
│                          Node 2 📱  │
│                                     │
└─────────────────────────────────────┘
```

**What happens:**
1. You start in the kitchen - **Node 1 only** sees you (circular zone)
2. You walk to hallway - **Nodes 1 & 2** see you (rectangular zone between them)
3. You enter living room - **All 3 nodes** see you (precise point with small circle)

---

## How Signal Strength Affects Zones

### Strong Signal (RSSI > -50 dBm)
- **Smaller uncertainty zones** (device is close)
- **Higher confidence**
- Zone radius: 2-5 meters

### Medium Signal (RSSI -50 to -70 dBm)
- **Medium uncertainty zones**
- **Medium confidence**
- Zone radius: 5-10 meters

### Weak Signal (RSSI < -70 dBm)
- **Larger uncertainty zones** (device is far)
- **Lower confidence**
- Zone radius: 10-20 meters

---

## Understanding the Map Colors

| Color | Meaning |
|-------|---------|
| 🟢 Green dot | WiFi device |
| 🔵 Blue dot | Bluetooth device |
| 🟠 Orange square | Scanner node (Raspberry Pi) |
| 🟠 Orange dashed box/circle | Uncertainty zone (possible device area) |

---

## AI Behavior Examples

### Example 1: Phone in Pocket (Stationary)

**Detected by 3 nodes:**
```
Position: (25.3, 15.7, 1.2)
Confidence: 90%
Uncertainty: ±2 meters
Zone: Small circle (radius 2m)
```

The AI shows a precise position with a small zone.

### Example 2: Phone Moving (Between 2 nodes)

**Detected by 2 nodes:**
```
Position: (12.5, 8.3, 1.0)
Confidence: 40%
Uncertainty: ±8 meters
Zone: Rectangle (16m x 12m)
```

The AI shows a larger rectangular zone indicating "device is somewhere in this area."

### Example 3: Phone at Edge (Only 1 node)

**Detected by 1 node:**
```
Position: (2.0, 1.5, 1.0) (at node position)
Confidence: 20%
Uncertainty: ±10 meters
Zone: Large circle (radius 10m)
```

The AI shows a large circular zone indicating "device is near this node but we don't know exactly where."

---

## Tips for Interpretation

### High Confidence (>70%)
- ✅ All 3 nodes detecting device
- ✅ Small uncertainty zone
- ✅ Position is accurate
- **Trust this location**

### Medium Confidence (40-70%)
- ⚠️ 2 nodes detecting device
- ⚠️ Rectangular zone shown
- ⚠️ Position is approximate
- **Device is within the shown box**

### Low Confidence (<40%)
- ❌ 1 node detecting device
- ❌ Large circular zone
- ❌ Position is just a guess
- **Device is somewhere in the circle**

---

## Advanced: Zone Types

### Circle Zone
```
Used when:
- 1 node detection
- 3+ node triangulation (small circle for accuracy)

Represents:
- Radial distance from a point
- "Could be anywhere at this distance"
```

### Rectangle Zone
```
Used when:
- 2 node detection

Represents:
- Area between two detection points
- Bounded by signal ranges from both nodes
- "Device is somewhere in this corridor"
```

---

## Improving Accuracy

To reduce uncertainty zones:

1. **Add more nodes** - More nodes = smaller zones
2. **Position nodes in triangle** - Better coverage
3. **Reduce obstacles** - Walls weaken signals
4. **Let system learn** - AI improves over time with history
5. **Keep nodes spread out** - Don't cluster them together

---

## Technical Details

### Zone Calculation (2 Nodes)

```python
# Pseudo-code
node1_distance = rssi_to_distance(rssi1)  # e.g., 5 meters
node2_distance = rssi_to_distance(rssi2)  # e.g., 12 meters

# Create box encompassing both circular ranges
min_x = min(node1.x - dist1, node2.x - dist2)
max_x = max(node1.x + dist1, node2.x + dist2)
min_y = min(node1.y - dist1, node2.y - dist2)
max_y = max(node1.y + dist1, node2.y + dist2)

# Device position: weighted by signal strength
# Stronger signal = closer to that node
```

### Zone Calculation (3 Nodes)

```python
# Full triangulation gives precise point
position = triangulate(node1, node2, node3, distances)

# Uncertainty based on measurement error
avg_distance = mean(distances)
uncertainty_radius = avg_distance * 0.3  # 30% error margin
```

---

**The uncertainty zones help you understand how reliable the position estimate is!** 🎯
