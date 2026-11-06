// =============================================================================
// 2004 Ford Focus SVT · JVC KW-V830BT Custom Radio Adapter
// =============================================================================
// Solves Metra 95-5806 pinching issue on JVC Double-DIN head unit faceplate.
// Compatible with OpenSCAD 2021+ or any 3D slicer.

$fn = 60;

// --- Primary Dimensions (mm) ---
jvc_width       = 179.39; // Measured JVC KW-V830BT faceplate width
jvc_height      = 98.43;  // Measured JVC KW-V830BT faceplate height
dash_opening_w  = 190.50; // Measured Focus SVT dash opening width (7.50")
dash_opening_h  = 101.60; // Measured Focus SVT dash opening height (4.00")

// --- Clearances & Tolerances ---
clearance_w     = 1.60;   // Total width clearance (+0.80 mm per side)
clearance_h     = 1.57;   // Total height clearance (+0.78 mm top & bottom)

// --- Flange & Boss Geometry ---
flange_overlap  = 3.00;   // Overlap past dash opening on all sides
flange_thick    = 2.50;   // Front faceplate thickness
boss_insertion  = 9.50;   // Depth of alignment boss into dash opening
boss_clearance  = 0.50;   // Slip clearance per side into dash opening

// --- Radii ---
flange_r        = 5.00;   // Outer flange corner radius
boss_r          = 3.50;   // Alignment boss corner radius
cutout_r        = 2.00;   // Inner cutout corner radius

// --- Mode Selection ---
// 1 = Stepped Front Trim Bezel (re-uses Metra / ISO side brackets)
// 2 = All-in-One Housing Cage (integrated side brackets with ISO M5 slots)
adapter_mode    = 2;

// --- Calculated Dimensions ---
cutout_w = jvc_width + clearance_w;       // 180.99 mm
cutout_h = jvc_height + clearance_h;      // 100.00 mm
flange_w = dash_opening_w + 2 * flange_overlap; // 196.50 mm
flange_h = dash_opening_h + 2 * flange_overlap; // 107.60 mm
boss_w   = dash_opening_w - 2 * boss_clearance; // 189.50 mm
boss_h   = dash_opening_h - 2 * (boss_clearance - 0.1); // 100.80 mm

// Helper: 2D Rounded Rectangle centered at origin
module rounded_rect(w, h, r) {
    hull() {
        translate([ (w/2 - r),  (h/2 - r)]) circle(r=r);
        translate([-(w/2 - r),  (h/2 - r)]) circle(r=r);
        translate([-(w/2 - r), -(h/2 - r)]) circle(r=r);
        translate([ (w/2 - r), -(h/2 - r)]) circle(r=r);
    }
}

// -----------------------------------------------------------------------------
// Model 1: Stepped Trim Bezel
// -----------------------------------------------------------------------------
module trim_bezel() {
    difference() {
        union() {
            // Front overlap flange (Z = 0 to flange_thick)
            linear_extrude(height = flange_thick)
                rounded_rect(flange_w, flange_h, flange_r);
            
            // Rear insertion alignment boss (Z = -boss_insertion to 0)
            translate([0, 0, -boss_insertion])
                linear_extrude(height = boss_insertion)
                    rounded_rect(boss_w, boss_h, boss_r);
        }
        
        // Through-cutout for JVC head unit
        translate([0, 0, -boss_insertion - 1])
            linear_extrude(height = boss_insertion + flange_thick + 2)
                rounded_rect(cutout_w, cutout_h, cutout_r);
    }
}

// -----------------------------------------------------------------------------
// Model 2: Unibody Cage with Side Mounting Arms
// -----------------------------------------------------------------------------
module unibody_cage() {
    bracket_depth = 65.0; // Depth of side brackets along radio chassis
    bracket_thick = 3.5;  // Wall thickness of side brackets
    
    union() {
        // Front trim bezel
        trim_bezel();
        
        // Left & Right Side Brackets
        for (side = [-1, 1]) {
            translate([side * (cutout_w / 2 + bracket_thick / 2), 0, -bracket_depth / 2])
            difference() {
                // Bracket wall
                cube([bracket_thick, cutout_h * 0.75, bracket_depth], center = true);
                
                // Slotted ISO M5 mounting screw holes (Standard 35mm pitch)
                for (z_off = [-15, 15]) {
                    translate([0, 0, z_off])
                        rotate([0, 90, 0])
                            hull() {
                                translate([0, -8, 0]) cylinder(h = bracket_thick + 2, d = 5.5, center = true);
                                translate([0,  8, 0]) cylinder(h = bracket_thick + 2, d = 5.5, center = true);
                            }
                }
            }
        }
    }
}

// Render based on selected mode
if (adapter_mode == 1) {
    trim_bezel();
} else {
    unibody_cage();
}
