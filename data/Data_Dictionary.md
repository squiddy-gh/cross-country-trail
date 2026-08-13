# Fairfax Cross County Trail
# Data Dictionary

Version: 0.1

---

# Overview

This document defines the data model used by the Fairfax Cross County Trail project.

The project separates:

* Geographic objects
* Editorial content
* Relationships
* Generated outputs

Each table represents one type of object.

Relationships between objects are stored explicitly rather than duplicated.

---

# Entity Relationship Diagram

```
Trail
 │
 ├── Sections
 │
 ├── Areas
 │      │
 │      └── contains ───── POIs
 │                           │
 │              ┌────────────┼────────────┐
 │              │            │            │
 │           Photos     Narratives      Tags
 │
 └── Transit Stops
```

---

# Table: POIs

Purpose

Represents individual physical locations that a hiker may visit.

Examples

* Parking lot
* Water fountain
* Historic marker
* Restaurant
* Restroom
* Trailhead

Each POI exists at one specific geographic location.

## Fields

### ID

Human-readable identifier.

Examples

```
P01
R04
H12
```

Used on:

* maps
* guidebook
* GPX
* website

Should remain stable.

---

### UUID

Permanent internal identifier.

Never changes.

Allows names or IDs to change without breaking relationships.

Example

```
a8f2e74d...
```

---

### Type

General category.

Current values

* Parking
* Trailhead
* Historic
* Restaurant
* Restroom
* Water
* Convenience Store
* Viewpoint

May expand in future.

---

### Name

Display name.

Example

```
Occoquan Regional Park Parking
```

---

### Priority

Importance when generating maps.

Suggested scale

| Value | Meaning |
|--------|---------|
| 1 | Always display |
| 2 | Major feature |
| 3 | Important |
| 4 | Optional |
| 5 | Minor |

---

### TrailMileage

Distance measured along the official trail centerline.

Example

```
17.43
```

This is NOT GPS distance.

This allows the guide to say

> Water available at Mile 17.4

---

### Latitude

Latitude (WGS84)

Decimal degrees.

---

### Longitude

Longitude (WGS84)

Decimal degrees.

---

### TrailOffset

Walking distance from the trail to reach the feature.

Examples

```
0.00
```

Directly on trail

```
0.08
```

Short detour

```
0.32
```

Requires leaving trail

Measured as walking distance whenever practical.

---

### AccessType

How the hiker reaches the feature.

Examples

* On Trail
* Side Trail
* Road Walk
* Parking Lot
* Building

---

### Capacity

Parking capacity or seating capacity where applicable.

Otherwise blank.

---

### Surface

Surface type.

Examples

* Asphalt
* Gravel
* Dirt
* Concrete
* Grass

---

### Restrooms

Availability.

Examples

```
Yes
No
Seasonal
```

---

### Water

Drinking water availability.

Examples

```
Yes
Seasonal
No
```

---

### Hours

Operating hours.

Example

```
Dawn to Dusk
```

---

### Fees

Parking or admission fee.

---

### Verified

Date information was last personally verified.

---

### Source

Origin of the information.

Examples

* OSM
* Fairfax County
* Field Survey
* GTFS
* Website

---

### Status

Current status.

Suggested values

* Active
* Seasonal
* Temporary
* Closed
* Removed
* Planned

---

### Notes

Short factual notes.

Examples

* Lot locked after dark
* Fountain off during winter

Keep concise.

Long narratives belong in Narratives.

---

### PrimaryPhotoID

Reference to the preferred photo.

Example

```
PH012
```

Links to Photos table.

---

### PrimaryNarrativeID

Reference to the primary article.

Example

```
N008
```

Links to Narratives table.

---

### URL

Official website.

---

# Table: Areas

Purpose

Represents places that contain multiple POIs.

Examples

* Occoquan Regional Park
* Laurel Hill
* Burke Lake Park

Areas may have boundaries or polygons in the future.

Areas organize content.

They are NOT individual destinations.

---

# Table: Relationships

Purpose

Connects one object to another.

Example

```
Area A01

contains

P01
H02
R03
```

No information should be duplicated if a relationship can describe it.

---

# Table: Narratives

Purpose

Editorial content.

Examples

* History
* Hiking advice
* Park description
* Wildlife

Unlike Notes, Narratives may be several paragraphs long.

One Narrative may describe:

* a Section
* an Area
* a POI

---

# Table: Photos

Purpose

Stores photo metadata.

A photo belongs to exactly one object.

Objects may have many photos.

---

# Table: Tags

Purpose

Flexible categorization.

Examples

```
Civil War
Family Friendly
Accessible
Scenic
Birding
```

Tags allow searching without changing the database schema.

---

# Table: ObjectTags

Purpose

Many-to-many relationship between objects and tags.

Example

```
POI H04

has tag

Civil War
```

---

# Table: Transit

Purpose

Public transportation near the trail.

Expected source

GTFS

Typical fields

* stop name
* routes
* distance from trail
* nearest trail mile

---

# Guiding Principles

Facts belong in structured tables.

Stories belong in Narratives.

Relationships belong in Relationship tables.

Generated outputs should never contain manually duplicated information.

The database is the single source of truth.