# Factory throttle-body photo fit plate

[1:1 print pattern](factory_iacv_photo_pattern_1to1.svg) · [4 mm fit-check plate STL](factory_iacv_photo_fit_plate.stl) · [Measured trace coordinates](photo_measurements.json)

The four manually picked bolt centers in the 1,200 × 1,200 photo were mapped to the fitted V2's 79 × 79 mm bolt grid. A circle fitted to the visible bore lip in that corrected plane was about 66.0 mm. The fit plate uses the existing 65 mm bore and 7 mm bolt holes. [Image-plane method](https://github.com/opencv/opencv/blob/4.x/doc/tutorials/features2d/homography/homography.markdown)

| Feature | First-pass measurement |
|---|---:|
| Bore center relative to the bolt-grid center | 4.8 mm right, 6.8 mm up as photographed |
| IACV feed outline bounding box | 27 mm wide × 37 mm high |
| IACV feed area centroid | 24 mm left, 21 mm down as photographed |
| Traced gasket centerline bounding box | 78 mm wide × 86 mm high |
| Smallest gap between the traced feed and the 65 mm bore | 3.0 mm |

The plate is a single watertight solid with the four bolt holes, the bore and the IACV opening. The gasket centerline and its divider are shown on the print pattern for alignment. The photo supplies approximate in-plane dimensions. Gasket thickness, compression, groove dimensions and internal passage depth need measurements from the actual parts. The assumed installed orientation puts the linkage up when viewed from the manifold's mating face and agrees with the eccentric bore in the fitted V2.

Print the pattern at 100% or use the fit coupon to compare the actual throttle body and gasket. The eventual flange passage runs from the separate face opening to the isolated IACV supply pocket. The fit plate is for a bench check and its opening is a through-cut.
