# Density-profile-processor
Processor of raw .dl1 files containing density profiles from EWS Dense-lab Mark 3 

This repository contains two files:
1. Densityprofiledl1reader; a code which transforms .dl1 files from the EWS Dense-lab into .xlsx files for further processing.
2. Density profile processor; a code which analysis and fits a logistical function for additional density profile parameters

The output of desntiyprofiledl1reader can be used in the density profile processor. The density profile processor then fits a logistical function on the left and right side of the density profile.This is done in order to mathematically split the density profile in core from surface. After this other measurements can be made, such as surface thickness, surface density and core density. The following picture explain the used definition of the surface-core split:

![image](https://user-images.githubusercontent.com/82240304/209134503-639d46ac-f3e3-41a4-a2d3-21aa76ecff47.png)

For more information or suggestions please contact Thijs Meijerink
