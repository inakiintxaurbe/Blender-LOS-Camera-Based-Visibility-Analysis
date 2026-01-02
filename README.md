# Blender-LOS-Camera-Based-Visibility-Analysis
Python script for Blender that performs line-of-sight (LOS) visibility analysis of a target surface from a predefined camera, approximating the human visual field and detecting visible, occluded, and out-of-field areas.

The script is intended for spatial, architectural, and archaeological analysis (e.g. visibility of rock art panels in caves), but it can be applied to any 3D environment.

**Author**: Iñaki Intxaurbe Alberdi
*Department of Graphic Design and Engineering Projects*

*(Universidad del País Vasco/Euskal Herriko Unibertsitatea)*

*PACEA UMR 5199*

*(Université du Bordeaux)*

**e-mail**: inaki.intxaurbe@ehu.eus; inaki.intxaurbe@u-bordeaux.fr; inaki.intxaurbe@gmail.com

**ORDICD nº**: https://orcid.org/0000-0003-3643-3177

**Date**: 2026-01-02

*Copyright (C) 2026  Iñaki Intxaurbe*

## Overview

This script:

--> Samples a target mesh surface using a configurable point density.

--> Evaluates visibility of each sampled point from an active camera using ray casting.

--> Classifies points as:

----> visible,

----> occluded by geometry,

----> outside the camera field of view,

----> outside the maximum analysis range.

--> Colors the target surface according to visibility results.

--> Exports all computed data to a CSV file for further analysis.

## Requirements

Blender (tested with Blender 3.x or newer).
--> https://www.blender.org/download/

A Blender scene containing:

--> *One active camera*

--> *One target panel mesh*

--> *Scene geometry acting as potential occluders*

No external Python libraries are required beyond Blender’s standard API (```bpy```).

## Scene Setup

our Blender project must include:

--> ```XXX.blend``` → Blender project file (any name)

-->```Target_Panel.obj```, ```.stl```, etc. → Target surface mesh

----> *Important: the object must be named exactly*: ```Target_Panel```

--> One Camera (active and correctly positioned. *For exampe at the height of the eyes of a prehistoric individual*).

--> Environment geometry (cave walls, architecture, terrain, etc.).

## Script Configuration

Key parameters can be modified at the top of the script:

```PANEL_OBJECT_NAME = "Target_Panel"
POINT_DENSITY_CM = 3.0
H_FOV_DEG = 110.0
V_FOV_DEG = 90.0
MAX_DISTANCE_M = 50.0```

