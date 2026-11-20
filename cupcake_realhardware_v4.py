import os
import FreeCAD as App
import Part

# ==============================================================================
# 1. REAL HARDWARE DIMENSIONS (in mm)
# ==============================================================================
TOL = 0.4

# Real Full-Length ESP32-S3-DevKitC-1 (Spans from Half-Head to Bottom Torso!)
ESP_W = 28.5 + TOL        # Real width: 28mm + clearance
ESP_H = 72.0 + TOL        # Real length: 69mm board + USB clearance
ESP_T = 6.5               # PCB + pin header / WROOM shield depth

# 3x Micro Servos (SG90 / MG90S / Sub-Micro)
SERVO_L = 23.0 + TOL
SERVO_W = 12.2 + TOL
SERVO_D = 15.5
SERVO_HORN_R = 3.5
SERVO_SCREW_R = 1.2

# Green Zone: 0.96" / 1.3" OLED Screen
SCREEN_VIEW_W = 28.0
SCREEN_VIEW_H = 16.0
SCREEN_PCB_W = 31.0 + TOL
SCREEN_PCB_H = 30.0 + TOL

# Purple Zone: Top Mini Phone Speaker
SPEAKER_W = 26.0 + TOL
SPEAKER_D = 16.0 + TOL
SPEAKER_T = 4.5

# Sky Blue Zone: Mobile Phone Battery (e.g., BL-5C 53x34x6mm)
BATT_W = 36.0 + TOL
BATT_H = 52.0 + TOL
BATT_T = 7.5 + TOL

# Chibi Robot Proportions (Sized so 72mm ESP32 spans Half-Head to Torso Bottom)
T_BASE_W = 68.0
T_BASE_D = 44.0
T_BASE_H = 11.0
T_STEM_W = 22.0
T_STEM_D = 20.0
T_STEM_H = 14.0
LEG_GAP = 2.0             # 2mm gap so Reverse-T leg rotates freely without rubbing!

TORSO_W = 66.0
TORSO_D = 48.0
TORSO_H = 54.0

NECK_W = 42.0             # Wide enough for 28.5mm ESP32 to pass straight through!
NECK_D = 34.0
NECK_H = 5.0

HEAD_W = 74.0
HEAD_D = 48.0
HEAD_H = 48.0
WALL = 2.8

ARM_L = 46.0
ARM_W = 16.0
ARM_T = 10.0

# Vertical Z Coordinates
LEG_PIVOT_Z = T_BASE_H + T_STEM_H
TORSO_Z0 = LEG_PIVOT_Z + LEG_GAP
NECK_Z0 = TORSO_Z0 + TORSO_H - 1.0
HEAD_Z0 = NECK_Z0 + NECK_H - 1.0
SHOULDER_Z = TORSO_Z0 + TORSO_H - 13.0

# ESP32 starts 6mm above Torso bottom and reaches Halfway up the Head!
ESP_Z0 = TORSO_Z0 + 6.0   # Goes from Z = 33mm up to Z = 105mm (Half-Head is 108mm)
SCREEN_CZ = HEAD_Z0 + HEAD_H / 2.0
BELLY_CZ = TORSO_Z0 + TORSO_H / 2.0 + 1.0


# ==============================================================================
# 2. GEOMETRY HELPERS
# ==============================================================================
def rounded_prism_xz(w, d, h, r, cx=0.0, cy=0.0, cz=0.0):
    r = min(r, w / 2.0 - 0.2, h / 2.0 - 0.2)
    b1 = Part.makeBox(w - 2 * r, d, h, App.Vector(cx - w / 2.0 + r, cy - d / 2.0, cz))
    b2 = Part.makeBox(w, d, h - 2 * r, App.Vector(cx - w / 2.0, cy - d / 2.0, cz + r))
    shape = b1.fuse(b2)
    for x in (cx - w / 2.0 + r, cx + w / 2.0 - r):
        for z in (cz + r, cz + h - r):
            cyl = Part.makeCylinder(r, d, App.Vector(x, cy - d / 2.0, z), App.Vector(0, 1, 0))
            shape = shape.fuse(cyl)
    return shape


def rounded_prism_xy(w, d, h, r, cx=0.0, cy=0.0, cz=0.0):
    r = min(r, w / 2.0 - 0.2, d / 2.0 - 0.2)
    b1 = Part.makeBox(w - 2 * r, d, h, App.Vector(cx - w / 2.0 + r, cy - d / 2.0, cz))
    b2 = Part.makeBox(w, d - 2 * r, h, App.Vector(cx - w / 2.0, cy - d / 2.0 + r, cz))
    shape = b1.fuse(b2)
    for x in (cx - w / 2.0 + r, cx + w / 2.0 - r):
        for y in (cy - d / 2.0 + r, cy + d / 2.0 - r):
            cyl = Part.makeCylinder(r, h, App.Vector(x, y, cz), App.Vector(0, 0, 1))
            shape = shape.fuse(cyl)
    return shape


def rounded_prism_yz(w, d, h, r, cx=0.0, cy=0.0, cz=0.0):
    r = min(r, d / 2.0 - 0.2, h / 2.0 - 0.2)
    b1 = Part.makeBox(w, d - 2 * r, h, App.Vector(cx - w / 2.0, cy - d / 2.0 + r, cz))
    b2 = Part.makeBox(w, d, h - 2 * r, App.Vector(cx - w / 2.0, cy - d / 2.0, cz + r))
    shape = b1.fuse(b2)
    for y in (cy - d / 2.0 + r, cy + d / 2.0 - r):
        for z in (cz + r, cz + h - r):
            cyl = Part.makeCylinder(r, w, App.Vector(cx - w / 2.0, y, z), App.Vector(1, 0, 0))
            shape = shape.fuse(cyl)
    return shape


def chibi_pillow_box(w, d, h, r_front, r_top, cx=0.0, cy=0.0, cz=0.0):
    return rounded_prism_xz(w, d, h, r_front, cx, cy, cz).common(
        rounded_prism_xy(w, d, h, r_top, cx, cy, cz)
    )


# ==============================================================================
# 3. PRINTABLE BODY, BACK COVER & BUTTONS
# ==============================================================================
def build_main_body():
    torso = chibi_pillow_box(TORSO_W, TORSO_D, TORSO_H, r_front=10.0, r_top=10.0, cz=TORSO_Z0)
    neck = rounded_prism_xy(NECK_W, NECK_D, NECK_H + 4.0, r=8.0, cz=NECK_Z0 - 1.0)
    head = chibi_pillow_box(HEAD_W, HEAD_D, HEAD_H, r_front=15.0, r_top=13.0, cz=HEAD_Z0)
    belly_frame = rounded_prism_xz(38.0, 2.0, 38.0, r=7.0, cx=0, cy=-TORSO_D / 2.0 - 0.5, cz=BELLY_CZ - 19.0)
    outer = torso.fuse(neck).fuse(head).fuse(belly_frame)

    # Internal cavities
    head_cav = chibi_pillow_box(
        HEAD_W - 2 * WALL, HEAD_D - 2 * WALL, HEAD_H - 2 * WALL,
        r_front=11.0, r_top=9.0, cz=HEAD_Z0 + WALL
    )
    neck_cav = rounded_prism_xy(
        NECK_W - 2 * WALL, NECK_D - 2 * WALL, NECK_H + 20.0,
        r=5.0, cz=NECK_Z0 - 8.0
    )
    torso_cav = chibi_pillow_box(
        TORSO_W - 2 * WALL, TORSO_D - 2 * WALL, TORSO_H - WALL - 15.0,
        r_front=7.0, r_top=7.0, cz=TORSO_Z0 + 14.0
    )

    # RED ZONE: Continuous Half-Head-to-Bottom-Torso Channel for Long ESP32-S3!
    esp_spine_channel = Part.makeBox(
        ESP_W + 4.0, 22.0, ESP_H + 4.0,
        App.Vector(-(ESP_W + 4.0) / 2.0, TORSO_D / 2.0 - 14.0, ESP_Z0 - 2.0)
    )
    usb_bottom_hole = Part.makeBox(
        14.0, 14.0, 14.0,
        App.Vector(-7.0, TORSO_D / 2.0 - 12.0, TORSO_Z0 - 1.0)
    )

    # GREEN ZONE: Open Screen Window + Internal Slot
    face_recess = rounded_prism_xz(
        HEAD_W - 14.0, 2.5, HEAD_H - 12.0, r=10.0,
        cx=0, cy=-HEAD_D / 2.0, cz=HEAD_Z0 + 6.0
    )
    screen_hole = rounded_prism_xz(
        SCREEN_VIEW_W, 12.0, SCREEN_VIEW_H, r=2.0,
        cx=0, cy=-HEAD_D / 2.0, cz=SCREEN_CZ - SCREEN_VIEW_H / 2.0
    )
    screen_slot = Part.makeBox(
        SCREEN_PCB_W, 4.5, SCREEN_PCB_H,
        App.Vector(-SCREEN_PCB_W / 2.0, -HEAD_D / 2.0 + 2.2, SCREEN_CZ - SCREEN_PCB_H / 2.0)
    )

    # PURPLE ZONE: Top Speaker Pocket + Grille
    spk_pocket = rounded_prism_xy(
        SPEAKER_W, SPEAKER_D, SPEAKER_T, r=4.0,
        cx=0, cy=-4.0, cz=HEAD_Z0 + HEAD_H - WALL - 3.0
    )
    spk_holes = Part.makeCylinder(1.6, 10.0, App.Vector(0, -4.0, HEAD_Z0 + HEAD_H - 6.0), App.Vector(0, 0, 1))
    for dx in (-7.0, -3.5, 3.5, 7.0):
        h1 = Part.makeCylinder(1.5, 10.0, App.Vector(dx, -7.5, HEAD_Z0 + HEAD_H - 6.0), App.Vector(0, 0, 1))
        h2 = Part.makeCylinder(1.5, 10.0, App.Vector(dx, -0.5, HEAD_Z0 + HEAD_H - 6.0), App.Vector(0, 0, 1))
        spk_holes = spk_holes.fuse(h1).fuse(h2)

    # SKY BLUE ZONE: 4 Belly Button Holes
    btn_cuts = Part.makeCylinder(1.8, 10.0, App.Vector(0, -TORSO_D / 2.0 - 3.0, BELLY_CZ + 11.0), App.Vector(0, 1, 0))
    for bx, bz in [(-8.5, 3.0), (8.5, 3.0), (-8.5, -8.5), (8.5, -8.5)]:
        bh = Part.makeCylinder(3.8, 12.0, App.Vector(bx, -TORSO_D / 2.0 - 3.0, BELLY_CZ + bz), App.Vector(0, 1, 0))
        btn_cuts = btn_cuts.fuse(bh)

    # 3x Micro Servo Bays (Left Shoulder, Right Shoulder, Bottom Waist)
    l_srv = Part.makeBox(
        SERVO_D, SERVO_W, SERVO_L,
        App.Vector(-TORSO_W / 2.0 - 1.0, -SERVO_W / 2.0 - 3.0, SHOULDER_Z - SERVO_L + 6.0)
    )
    r_srv = Part.makeBox(
        SERVO_D, SERVO_W, SERVO_L,
        App.Vector(TORSO_W / 2.0 - SERVO_D + 1.0, -SERVO_W / 2.0 - 3.0, SHOULDER_Z - SERVO_L + 6.0)
    )
    b_srv = Part.makeBox(
        SERVO_L, SERVO_W, SERVO_D,
        App.Vector(-SERVO_L / 2.0, -SERVO_W / 2.0 - 2.0, TORSO_Z0 - 1.0)
    )

    cuts = (
        head_cav
        .fuse(neck_cav)
        .fuse(torso_cav)
        .fuse(esp_spine_channel)
        .fuse(usb_bottom_hole)
        .fuse(face_recess)
        .fuse(screen_hole)
        .fuse(screen_slot)
        .fuse(spk_pocket)
        .fuse(spk_holes)
        .fuse(btn_cuts)
        .fuse(l_srv)
        .fuse(r_srv)
        .fuse(b_srv)
    )
    return outer.cut(cuts)


def build_continuous_back_cover():
    """One-piece removable back cover spanning from Half-Head to Bottom Torso."""
    lid_outer = rounded_prism_xz(
        ESP_W + 10.0, 3.0, ESP_H + 8.0, r=5.0,
        cx=0, cy=TORSO_D / 2.0 + 1.5, cz=ESP_Z0 - 4.0
    )
    lid_lip = Part.makeBox(
        ESP_W + 3.2, 4.0, ESP_H + 3.2,
        App.Vector(-(ESP_W + 3.2) / 2.0, TORSO_D / 2.0 - 2.5, ESP_Z0 - 1.6)
    )
    esp_hollow = Part.makeBox(
        ESP_W, 5.0, ESP_H,
        App.Vector(-ESP_W / 2.0, TORSO_D / 2.0 - 3.0, ESP_Z0)
    )
    return lid_outer.fuse(lid_lip).cut(esp_hollow)


# ==============================================================================
# 4. ROTATABLE HANDS & REVERSE-T LEG (Built at Local Origin (0,0,0) so they Rotate!)
# ==============================================================================
def build_rotatable_hand(side='LEFT'):
    """
    Built with Shoulder Pivot Shaft at Local (0, 0, 0)!
    Rotating this object around the X-axis swings the arm naturally.
    """
    sign = -1.0 if side == 'LEFT' else 1.0
    local_cx = sign * (ARM_T / 2.0 + 1.5)
    local_z0 = -ARM_L + ARM_W / 2.0

    side_cap = rounded_prism_yz(ARM_T, ARM_W, ARM_L, r=ARM_W / 2.0 - 0.3, cx=local_cx, cy=0, cz=local_z0)
    front_pil = rounded_prism_xz(ARM_T, ARM_W, ARM_L, r=ARM_T / 2.0 - 0.3, cx=local_cx, cy=0, cz=local_z0)
    arm = side_cap.common(front_pil)

    thumb = Part.makeSphere(4.2, App.Vector(local_cx, -ARM_W / 2.0 + 1.5, local_z0 + 11.0))
    boss = Part.makeCylinder(SERVO_HORN_R + 1.8, 4.5, App.Vector(-sign * 1.5, 0, 0), App.Vector(sign, 0, 0))
    horn_cut = Part.makeCylinder(SERVO_HORN_R, 3.5, App.Vector(-sign * 1.6, 0, 0), App.Vector(sign, 0, 0))
    screw_cut = Part.makeCylinder(SERVO_SCREW_R, ARM_T + 8.0, App.Vector(local_cx - ARM_T, 0, 0), App.Vector(1, 0, 0))

    return arm.fuse(thumb).fuse(boss).cut(horn_cut).cut(screw_cut)


def build_rotatable_reverse_t_leg():
    """
    Built with Waist Pivot Shaft at X=0, Y=0!
    Rotating this object around the Z-axis turns the Reverse-T leg left and right.
    """
    stem = chibi_pillow_box(T_STEM_W, T_STEM_D, T_STEM_H + 3.0, r_front=4.5, r_top=5.5, cx=0, cy=-2.0, cz=T_BASE_H - 2.0)
    l_foot = chibi_pillow_box(T_BASE_W / 2.0 - 1.5, T_BASE_D, T_BASE_H, r_front=5.5, r_top=11.0, cx=-(T_BASE_W / 4.0 + 0.5), cy=-2.0, cz=0)
    r_foot = chibi_pillow_box(T_BASE_W / 2.0 - 1.5, T_BASE_D, T_BASE_H, r_front=5.5, r_top=11.0, cx=(T_BASE_W / 4.0 + 0.5), cy=-2.0, cz=0)
    bridge = rounded_prism_xy(26.0, T_BASE_D - 10.0, T_BASE_H, r=5.0, cx=0, cy=-1.0, cz=0)

    leg = stem.fuse(l_foot).fuse(r_foot).fuse(bridge)
    horn_cut = Part.makeCylinder(SERVO_HORN_R, 4.0, App.Vector(0, -2.0, LEG_PIVOT_Z - 3.8), App.Vector(0, 0, 1))
    screw_cut = Part.makeCylinder(SERVO_SCREW_R, LEG_PIVOT_Z + 2.0, App.Vector(0, -2.0, -1.0), App.Vector(0, 0, 1))
    return leg.cut(horn_cut).cut(screw_cut)


def build_belly_buttons():
    backing = rounded_prism_xz(28.0, 1.2, 24.0, r=4.0, cx=0, cy=-TORSO_D / 2.0 + WALL, cz=BELLY_CZ - 14.5)
    for bx, bz in [(-8.5, 3.0), (8.5, 3.0), (-8.5, -8.5), (8.5, -8.5)]:
        cap = Part.makeCylinder(3.4, 5.5, App.Vector(bx, -TORSO_D / 2.0 - 2.0, BELLY_CZ + bz), App.Vector(0, 1, 0))
        backing = backing.fuse(cap)
    return backing


# ==============================================================================
# 5. REAL HARDWARE PREVIEWS (Full-Length ESP32-S3 from Half-Head to Bottom!)
# ==============================================================================
def build_real_hardware_models():
    # RED: Real 69mm ESP32-S3-DevKitC-1 (Spans from Half-Head Z=103mm down to Torso Bottom Z=33mm!)
    pcb = Part.makeBox(28.0, 1.6, 69.0, App.Vector(-14.0, TORSO_D / 2.0 - 6.0, ESP_Z0 + 1.5))
    wroom_can = Part.makeBox(18.0, 3.2, 25.5, App.Vector(-9.0, TORSO_D / 2.0 - 9.2, ESP_Z0 + 40.0))
    usb_port1 = Part.makeBox(9.0, 3.2, 7.5, App.Vector(-11.0, TORSO_D / 2.0 - 9.2, ESP_Z0))
    usb_port2 = Part.makeBox(9.0, 3.2, 7.5, App.Vector(2.0, TORSO_D / 2.0 - 9.2, ESP_Z0))
    red_esp32 = pcb.fuse(wroom_can).fuse(usb_port1).fuse(usb_port2)

    # GREEN: OLED Screen in Head
    green_oled = Part.makeBox(30.0, 2.5, 29.0, App.Vector(-15.0, -HEAD_D / 2.0 + 3.0, SCREEN_CZ - 14.5))

    # PURPLE: Top Speaker in Head Crown
    purple_spk = rounded_prism_xy(24.0, 14.0, 3.5, r=3.5, cx=0, cy=-4.0, cz=HEAD_Z0 + HEAD_H - WALL - 2.5)

    # SKY BLUE: Mobile Phone Battery in Front Belly
    sky_batt = Part.makeBox(34.0, 6.0, 50.0, App.Vector(-17.0, -TORSO_D / 2.0 + 5.0, TORSO_Z0 + 15.0))

    return red_esp32, green_oled, purple_spk, sky_batt


# ==============================================================================
# 6. ASSEMBLE & TEST ROTATION IN FREECAD
# ==============================================================================
def create_cupcake_v4(output_dir=None, save_fcstd=None):
    doc = App.newDocument("CupCake_RealHardware_V4")

    # 1. Static Printable Parts
    body_obj = doc.addObject("Part::Feature", "Part1_Main_Body_Shell")
    body_obj.Shape = build_main_body()

    cover_obj = doc.addObject("Part::Feature", "Part2_Back_Cover_ESP32")
    cover_obj.Shape = build_continuous_back_cover()

    btn_obj = doc.addObject("Part::Feature", "Part6_Belly_Button_Caps")
    btn_obj.Shape = build_belly_buttons()

    # 2. Rotatable Hands (Pivot set at Shoulder Shafts!)
    l_hand = doc.addObject("Part::Feature", "Part3_Left_Hand_Rotatable")
    l_hand.Shape = build_rotatable_hand('LEFT')
    l_hand.Placement.Base = App.Vector(-TORSO_W / 2.0, -3.0, SHOULDER_Z)
    l_hand.Placement.Rotation = App.Rotation(App.Vector(1, 0, 0), 20.0)  # Swung forward 20 deg!

    r_hand = doc.addObject("Part::Feature", "Part4_Right_Hand_Rotatable")
    r_hand.Shape = build_rotatable_hand('RIGHT')
    r_hand.Placement.Base = App.Vector(TORSO_W / 2.0, -3.0, SHOULDER_Z)
    r_hand.Placement.Rotation = App.Rotation(App.Vector(1, 0, 0), -15.0) # Swung back 15 deg!

    # 3. Rotatable Reverse-T Leg (Pivot set at Waist Shaft!)
    leg_obj = doc.addObject("Part::Feature", "Part5_Reverse_T_Leg_Rotatable")
    leg_obj.Shape = build_rotatable_reverse_t_leg()
    leg_obj.Placement.Base = App.Vector(0, 0, 0)
    leg_obj.Placement.Rotation = App.Rotation(App.Vector(0, 0, 1), 12.0) # Rotated 12 deg!

    # 4. Real Hardware Guides
    red_esp, green_oled, purple_spk, sky_batt = build_real_hardware_models()
    hw_group = doc.addObject("App::DocumentObjectGroup", "Real_Hardware_Inside")
    hw_items = [
        ("RED_ESP32_S3_HalfHeadToBottom", red_esp, (0.95, 0.15, 0.15)),
        ("GREEN_OLED_Screen", green_oled, (0.10, 0.85, 0.30)),
        ("PURPLE_Mini_Speaker", purple_spk, (0.70, 0.20, 0.90)),
        ("SKYBLUE_Phone_Battery", sky_batt, (0.15, 0.78, 0.98)),
    ]
    for name, shape, rgb in hw_items:
        o = doc.addObject("Part::Feature", name)
        o.Shape = shape
        hw_group.addObject(o)
        if App.GuiUp:
            o.ViewObject.ShapeColor = rgb

    if App.GuiUp:
        body_obj.ViewObject.ShapeColor = (0.22, 0.54, 0.96)
        body_obj.ViewObject.Transparency = 45  # Semi-transparent so you see the red ESP32 inside!
        cover_obj.ViewObject.ShapeColor = (0.88, 0.92, 0.96)
        cover_obj.ViewObject.Transparency = 60
        l_hand.ViewObject.ShapeColor = (0.22, 0.54, 0.96)
        r_hand.ViewObject.ShapeColor = (0.22, 0.54, 0.96)
        leg_obj.ViewObject.ShapeColor = (0.22, 0.54, 0.96)
        btn_obj.ViewObject.ShapeColor = (0.98, 0.38, 0.58)

    doc.recompute()

    printable_objs = [body_obj, cover_obj, l_hand, r_hand, leg_obj, btn_obj]
    if output_dir:
        import MeshPart
        os.makedirs(output_dir, exist_ok=True)
        for obj in printable_objs:
            stl_path = os.path.join(output_dir, f"{obj.Label}.stl")
            # For 3D printing, export the part in its untransformed base orientation or as positioned
            mesh = MeshPart.meshFromShape(Shape=obj.Shape, LinearDeflection=0.1, AngularDeflection=0.523599)
            mesh.write(stl_path)
            print(f"Exported {stl_path} (triangles: {mesh.CountFacets})")

    if save_fcstd:
        doc.saveAs(save_fcstd)
        print(f"Saved FreeCAD project to {save_fcstd}")

    if App.GuiUp:
        try:
            import FreeCADGui as Gui
            Gui.activeDocument().activeView().viewAxometric()
            Gui.SendMsgToMainWindow("ViewFit")
        except Exception as e:
            print(f"GUI adjustment error: {e}")

    return doc


if __name__ == "__main__" or __name__ == "builtins":
    try:
        project_dir = os.path.dirname(os.path.abspath(__file__))
    except Exception:
        project_dir = os.path.abspath(".")
    cad_out = os.path.join(project_dir, "cad", "out_v4")
    fcstd_file = os.path.join(project_dir, "cad", "CupCake_RealHardware_V4.FCStd")
    create_cupcake_v4(output_dir=cad_out, save_fcstd=fcstd_file)
