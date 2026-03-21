# Argo Data Interpolation

Spatiotemporal interpolation of oceanic CTD conditions using Argo float data.

## Overview

This project develops advanced machine learning techniques to predict oceanographic conditions (temperature, salinity, pressure) across space and time from sparse Argo float measurements. The work extends prior research by Alnis Smidchens (University of Washington, advised by Rick Rupan) by incorporating temporal dynamics alongside spatial interpolation.

## Methodology

The project follows a three-phase approach:

### Phase 1: Vertical Interpolation
Single-float depth profile modeling. Estimates CTD readings at any depth along a float's ~2000m vertical trajectory.

### Phase 2: Spatial Interpolation
Multi-float geographic interpolation. Predicts CTD values at arbitrary locations based on nearby float measurements.

### Phase 3: Spatiotemporal Interpolation
Full 4D modeling incorporating both spatial proximity and temporal dynamics to predict oceanographic conditions at any location and time.

## Acknowledgments

This work is supported by the MATE program and will be presented at the 2026 Underwater Interventions conference. Development was inspired by participation in the 2025 MATE Floats workshop.

