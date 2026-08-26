# Section Analysis Tool

A Fusion 360-style section analysis add-on for Blender. Slice through your
selected objects along a chosen axis using a non-destructive boolean cutting
plane, with live control over distance, tilt, size, and centering.

## Features

- **Axis-aligned cuts** — cut along X, Y, or Z with one click.
- **Distance offset** — slide the cutting plane along the chosen axis.
- **Tilt** — angle the cutting face toward or away from the object, instead
  of a fixed perpendicular cut.
- **Center on Selection** — the cutting plane bases its position on the
  combined bounding-box center of your selected objects (rather than world
  origin), so it starts positioned on your geometry regardless of where it
  sits in the scene. Can be disabled to fall back to world-origin-relative
  positioning.
- **Plane sizing**
  - *Manual* — set a fixed cutting plane size.
  - *Auto (Selection)* — the plane automatically sizes itself to fit the
    combined bounding box of the selected objects, with an adjustable
    margin so it comfortably clears the geometry.
- **Wireframe toggle** — display the cutting plane as wireframe or solid.
- **Non-destructive** — applies a Boolean Difference modifier per object
  rather than altering your mesh data; clear it at any time to restore the
  original geometry.

## Requirements

- Blender 4.2 or newer.

## Installation

1. Download the extension `.zip`.
2. In Blender, go to **Edit > Preferences > Get Extensions** (or
   **Add-ons**, depending on version) and choose **Install from Disk**.
3. Select the downloaded `.zip` file.
4. Enable **Section Analysis Tool** if it isn't already active.

## Usage

1. Select one or more mesh objects in the 3D Viewport.
2. Open the sidebar (`N` panel) and go to the **Section Analysis** tab.
3. Set your cut **Axis**, **Distance**, and **Tilt** as needed.
4. Choose a **Size Mode** — Manual for a fixed plane size, or Auto to fit
   the selection's bounding box.
5. Click **Apply Section Analysis** to add the cutting plane and boolean
   modifiers.
6. Click **Clear Section Analysis** at any time to remove the cutter and
   its modifiers, restoring the original geometry.

## Panel Reference

| Property | Description |
|---|---|
| Axis | Which world axis the cutting plane's normal faces (X, Y, or Z). |
| Distance | Offset of the cutting plane along the chosen axis, measured from the selection's bounding-box center (or world origin, if Center on Selection is off). |
| Tilt | Rotates the cutting plane around an in-plane axis, angling its face toward or away from the object. |
| Show Wireframe | Displays the cutting plane as wireframe instead of solid. |
| Center on Selection | Positions the cutting plane at the selected objects' bounding-box center instead of world origin. |
| Size Mode | Manual (fixed size) or Auto (fits the selection's bounding box). |
| Plane Size | Fixed cutting plane size, used in Manual mode. |
| Margin | Multiplier applied to the selection's bounding-box diagonal, used in Auto mode. |

