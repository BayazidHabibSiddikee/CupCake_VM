import os
import FreeCAD as App
import Part

# ==============================================================================
# 1. PARAMETRIC DIMENSIONS (in mm) - Sized for Real Hardware + 3D Printing
# ==============================================================================
TOL = 0.4  # 3D printer clearance tolerance

# Micro Servo (9g SG90 or 4.3g Sub-Micro)
SERVO_L = 23.0 + TOL      # Length of servo case
SERVO_W = 12.2 + TOL      # Width of servo case
SERVO_D = 16.0            # Pocket depth into torso side/bottom
SERVO_HORN_R = 3.5        # Socket radius for servo horn
SERVO_SCREW_R = 1.2       # M2 screw pass-through hole

# Green Zone: OLED Screen Module (0.96" or 1.3" I2C OLED)
SCREEN_VIEW_W = 28.0      # Front open viewing window width
SCREEN_VIEW_H = 16.0      # Front open viewing window height
SCREEN_PCB_W = 31.0 + TOL # Internal PCB slot width
SCREEN_PCB_H = 30.0 + TOL # Internal PCB slot height
SCREEN_PCB_T = 4.5        # Internal PCB slot depth behind front face

# Purple Zone: Top Head Mini Speaker (Mobile phone speaker / 20mm round speaker)
SPEAKER_W = 26.0 + TOL
SPEAKER_D = 18.0 + TOL
SPEAKER_T = 4.5

# Sky Blue Zone: Mobile Phone Battery (Fits BL-5C 53x34x6mm or small LiPo pouch)
BATT_W = 38.0 + TOL
BATT_H = 54.0 + TOL
BATT_T = 8.5 + TOL

# Red Zone: ESP32-S3 Board (Fits XIAO ESP32-S3, SuperMini, ESP32-CAM, or DevKit)
ESP_W = 30.0 + TOL
ESP_H = 56.0 + TOL
ESP_T = 6.0

# Robot Outer Proportions (Scaled slightly so Battery + Servos + ESP32 fit cleanly)
HEAD_W = 74.0
HEAD_D = 46.0
HEAD_H = 50.0

NECK_W = 34.0             # Widened neck so Red spine wires/boards pass through
NECK_D = 28.0
NECK_H = 6.0

TORSO_W = 64.0
TORSO_D = 46.0
TORSO_H = 64.0
WALL = 2.8

ARM_L = 46.0              # Hand/Arm total length
ARM_W = 16.0              # Arm width (Y)
ARM_T = 10.0              # Arm thickness (X)

T_STEM_W = 22.0           # Reverse-T vertical stem
T_STEM_D = 20.0
T_STEM_H = 15.0
T_BASE_W = 68.0           # Reverse-T bottom foot bar
T_BASE_D = 44.0
T_BASE_H = 12.0


# ==============================================================================
# 2. DETERMINISTIC ROUNDED PRISM HELPERS (Zero fragile rotations or 3D fillets)
# ==============================================================================
def rounded_prism_xz(w, d, h, r, cx=0.0, cy=0.0, cz=0.0):
    """Box with rounded corners in the Front View (X-Z plane)."""
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
    """Box with rounded vertical corners in the Top View (X-Y plane)."""
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
    """Box with rounded corners in the Side View (Y-Z plane) - used for Hands/Arms."""
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
    """Smooth 3D rounded shell created by intersecting Front and Top prisms."""
    return rounded_prism_xz(w, d, h, r_front, cx, cy, cz).common(
        rounded_prism_xy(w, d, h, r_top, cx, cy, cz)
    )


# ==============================================================================
# 3. VERTICAL LAYOUT COORDINATES
# ==============================================================================
TORSO_Z0 = T_BASE_H + T_STEM_H + 1.5
NECK_Z0 = TORSO_Z0 + TORSO_H - 1.0
HEAD_Z0 = NECK_Z0 + NECK_H - 1.0
SHOULDER_Z = TORSO_Z0 + TORSO_H - 14.0

SCREEN_CZ = HEAD_Z0 + HEAD_H / 2.0 - 1.0
BELLY_CZ = TORSO_Z0 + TORSO_H / 2.0 - 2.0


# ==============================================================================
# 4. PRINTABLE PART BUILDERS
# ==============================================================================
def build_printable_main_body():
    """
    1_Main_Body_Shell:
    - Hollow Head + Wide Neck + Torso
    - GREEN: Open screen cutout on face + internal PCB slot
    - PURPLE: Top speaker grille holes + internal speaker pocket
    - SKY BLUE: 4 Belly button holes + internal mobile phone battery bay
    - RED: Open rear service access for ESP32-S3 + wiring
    """
    # 1. Outer Chibi Shell (Torso + Neck + Head + Front Belly Bezel Frame)
    torso = chibi_pillow_box(TORSO_W, TORSO_D, TORSO_H, r_front=11.0, r_top=11.0, cz=TORSO_Z0)
    neck = rounded_prism_xy(NECK_W, NECK_D, NECK_H + 3.0, r=8.0, cz=NECK_Z0)
    head = chibi_pillow_box(HEAD_W, HEAD_D, HEAD_H, r_front=16.0, r_top=13.0, cz=HEAD_Z0)

    # Raised cute belly border on front torso (-Y)
    belly_frame = rounded_prism_xz(
        40.0, 2.0, 42.0, r=8.0,
        cx=0, cy=-TORSO_D / 2.0 - 0.5, cz=BELLY_CZ - 21.0
    )
    outer_shell = torso.fuse(neck).fuse(head).fuse(belly_frame)

    # 2. Internal Hollow Cavities (Head Cavity + Wide Neck Spine + Torso Cavity)
    head_cavity = chibi_pillow_box(
        HEAD_W - 2 * WALL, HEAD_D - 2 * WALL, HEAD_H - 2 * WALL,
        r_front=12.0, r_top=10.0, cz=HEAD_Z0 + WALL
    )
    # Wide Red Spine Channel connecting head and torso so wires/boards fit easily
    spine_tunnel = rounded_prism_xy(
        NECK_W - 2 * WALL, NECK_D - 2 * WALL, NECK_H + 20.0,
        r=5.0, cz=NECK_Z0 - 8.0
    )
    # Main Torso Cavity (leaving bottom floor for waist servo)
    torso_cavity = chibi_pillow_box(
        TORSO_W - 2 * WALL, TORSO_D - 2 * WALL, TORSO_H - WALL - 16.0,
        r_front=8.0, r_top=8.0, cz=TORSO_Z0 + 15.0
    )

    # 3. GREEN ZONE: Open Screen Window on Face (-Y) + Internal PCB Slot
    face_recess = rounded_prism_xz(
        HEAD_W - 14.0, 2.5, HEAD_H - 14.0, r=10.0,
        cx=0, cy=-HEAD_D / 2.0, cz=HEAD_Z0 + 7.0
    )
    screen_window = rounded_prism_xz(
        SCREEN_VIEW_W, 12.0, SCREEN_VIEW_H, r=2.0,
        cx=0, cy=-HEAD_D / 2.0, cz=SCREEN_CZ - SCREEN_VIEW_H / 2.0
    )
    screen_pcb_slot = Part.makeBox(
        SCREEN_PCB_W, SCREEN_PCB_T, SCREEN_PCB_H,
        App.Vector(-SCREEN_PCB_W / 2.0, -HEAD_D / 2.0 + 2.2, SCREEN_CZ - SCREEN_PCB_H / 2.0)
    )

    # 4. PURPLE ZONE: Top Head Speaker Pocket + Acoustic Grille Holes (+Z)
    speaker_top_z = HEAD_Z0 + HEAD_H - WALL - 1.5
    speaker_pocket = rounded_prism_xy(
        SPEAKER_W, SPEAKER_D, SPEAKER_T, r=5.0,
        cx=0, cy=0, cz=speaker_top_z - 2.0
    )
    speaker_holes = Part.makeCylinder(
        1.6, 12.0, App.Vector(0, 0, HEAD_Z0 + HEAD_H - 8.0), App.Vector(0, 0, 1)
    )
    for dx in (-7.0, -3.5, 3.5, 7.0):
        h1 = Part.makeCylinder(1.5, 12.0, App.Vector(dx, -3.5, HEAD_Z0 + HEAD_H - 8.0), App.Vector(0, 0, 1))
        h2 = Part.makeCylinder(1.5, 12.0, App.Vector(dx, 3.5, HEAD_Z0 + HEAD_H - 8.0), App.Vector(0, 0, 1))
        speaker_holes = speaker_holes.fuse(h1).fuse(h2)

    # 5. SKY BLUE ZONE: 4 Belly Push-Button Cutouts (-Y)
    belly_button_cuts = Part.makeCylinder(
        1.8, 10.0, App.Vector(0, -TORSO_D / 2.0 - 3.0, BELLY_CZ + 12.0), App.Vector(0, 1, 0)
    ) # Top center LED / status pinhole
    btn_offsets = [(-8.5, 3.5), (8.5, 3.5), (-8.5, -8.5), (8.5, -8.5)]
    for bx, bz in btn_offsets:
        btn_hole = Part.makeCylinder(
            3.8, 12.0,
            App.Vector(bx, -TORSO_D / 2.0 - 3.0, BELLY_CZ + bz),
            App.Vector(0, 1, 0)
        )
        belly_button_cuts = belly_button_cuts.fuse(btn_hole)

    # 6. RED ZONE: Rear Service Opening (+Y) so Battery, Screen, Speaker & ESP32 go in easily
    rear_torso_opening = rounded_prism_xz(
        TORSO_W - 16.0, 14.0, TORSO_H - 18.0, r=6.0,
        cx=0, cy=TORSO_D / 2.0 - 4.0, cz=TORSO_Z0 + 10.0
    )
    rear_head_opening = rounded_prism_xz(
        HEAD_W - 24.0, 14.0, HEAD_H - 16.0, r=7.0,
        cx=0, cy=HEAD_D / 2.0 - 4.0, cz=HEAD_Z0 + 8.0
    )

    # 7. Three Micro-Servo Pockets (Left Shoulder, Right Shoulder, Bottom Waist)
    l_servo = Part.makeBox(
        SERVO_D, SERVO_W, SERVO_L,
        App.Vector(-TORSO_W / 2.0 - 1.0, -SERVO_W / 2.0, SHOULDER_Z - SERVO_L + 6.0)
    )
    r_servo = Part.makeBox(
        SERVO_D, SERVO_W, SERVO_L,
        App.Vector(TORSO_W / 2.0 - SERVO_D + 1.0, -SERVO_W / 2.0, SHOULDER_Z - SERVO_L + 6.0)
    )
    b_servo = Part.makeBox(
        SERVO_L, SERVO_W, SERVO_D,
        App.Vector(-SERVO_L / 2.0, -SERVO_W / 2.0, TORSO_Z0 - 1.0)
    )

    all_cuts = (
        head_cavity
        .fuse(spine_tunnel)
        .fuse(torso_cavity)
        .fuse(face_recess)
        .fuse(screen_window)
        .fuse(screen_pcb_slot)
        .fuse(speaker_pocket)
        .fuse(speaker_holes)
        .fuse(belly_button_cuts)
        .fuse(rear_torso_opening)
        .fuse(rear_head_opening)
        .fuse(l_servo)
        .fuse(r_servo)
        .fuse(b_servo)
    )

    body_hollow = outer_shell.cut(all_cuts)

    # Add internal battery retention rails inside torso (keeps Sky Blue battery in place)
    left_rail = Part.makeBox(2.5, 3.0, 38.0, App.Vector(-BATT_W / 2.0 - 2.5, -6.0, TORSO_Z0 + 16.0))
    right_rail = Part.makeBox(2.5, 3.0, 38.0, App.Vector(BATT_W / 2.0, -6.0, TORSO_Z0 + 16.0))

    return body_hollow.fuse(left_rail).fuse(right_rail)


def build_printable_back_cover():
    """
    2_Back_Cover_ESP32:
    Snap/screw-on rear service door covering the Head & Torso back openings,
    with an integrated ESP32-S3 mounting cradle and bottom USB-C slot.
    """
    torso_lid = rounded_prism_xz(
        TORSO_W - 12.0, 3.0, TORSO_H - 14.0, r=7.0,
        cx=0, cy=TORSO_D / 2.0 + 1.5, cz=TORSO_Z0 + 8.0
    )
    torso_lip = rounded_prism_xz(
        TORSO_W - 16.8, 3.0, TORSO_H - 18.8, r=5.6,
        cx=0, cy=TORSO_D / 2.0 - 1.0, cz=TORSO_Z0 + 10.4
    )
    head_lid = rounded_prism_xz(
        HEAD_W - 20.0, 3.0, HEAD_H - 12.0, r=8.0,
        cx=0, cy=HEAD_D / 2.0 + 1.5, cz=HEAD_Z0 + 6.0
    )
    head_lip = rounded_prism_xz(
        HEAD_W - 24.8, 3.0, HEAD_H - 16.8, r=6.6,
        cx=0, cy=HEAD_D / 2.0 - 1.0, cz=HEAD_Z0 + 8.4
    )
    neck_bridge = Part.makeBox(
        24.0, 3.0, 22.0,
        App.Vector(-12.0, TORSO_D / 2.0, NECK_Z0 - 8.0)
    )

    cover = torso_lid.fuse(torso_lip).fuse(head_lid).fuse(head_lip).fuse(neck_bridge)

    # Hollow out the inner lip so ESP32-S3 sits recessed inside the back cover
    esp_recess = Part.makeBox(
        ESP_W, 4.5, ESP_H,
        App.Vector(-ESP_W / 2.0, TORSO_D / 2.0 - 2.5, TORSO_Z0 + 12.0)
    )
    # Bottom USB-C cable cutout
    usb_slot = Part.makeBox(
        12.0, 10.0, 10.0,
        App.Vector(-6.0, TORSO_D / 2.0 - 3.0, TORSO_Z0 + 6.0)
    )
    return cover.cut(esp_recess).cut(usb_slot)


def build_printable_hand_arm(side='LEFT'):
    """
    3_Left_Hand_Arm / 4_Right_Hand_Arm:
    Built directly in global coordinates using rounded_prism_yz & rounded_prism_xz
    so it never disappears! Includes cute thumb bump + servo horn socket.
    """
    sign = -1.0 if side == 'LEFT' else 1.0
    arm_cx = sign * (TORSO_W / 2.0 + ARM_T / 2.0 + 1.5)
    arm_z0 = SHOULDER_Z - ARM_L + ARM_W / 2.0

    # Intersect Side-view rounded capsule (Y-Z) with Front-view rounded pill (X-Z)
    side_capsule = rounded_prism_yz(
        ARM_T, ARM_W, ARM_L, r=ARM_W / 2.0 - 0.3,
        cx=arm_cx, cy=0.0, cz=arm_z0
    )
    front_pill = rounded_prism_xz(
        ARM_T, ARM_W, ARM_L, r=ARM_T / 2.0 - 0.3,
        cx=arm_cx, cy=0.0, cz=arm_z0
    )
    arm_body = side_capsule.common(front_pill)

    # Cute chibi thumb/hand contour on the front lower side (-Y)
    thumb = Part.makeSphere(4.2, App.Vector(arm_cx, -ARM_W / 2.0 + 1.5, arm_z0 + 11.0))
    arm_body = arm_body.fuse(thumb)

    # Shoulder Servo Boss extending toward torso servo pocket
    inner_face_x = arm_cx - sign * (ARM_T / 2.0)
    boss_start_x = inner_face_x - sign * 3.0
    boss = Part.makeCylinder(
        SERVO_HORN_R + 1.8, 4.5,
        App.Vector(boss_start_x, 0.0, SHOULDER_Z),
        App.Vector(sign, 0.0, 0.0)
    )
    arm_with_boss = arm_body.fuse(boss)

    # Servo Horn Socket + M2 Screw Hole
    horn_socket = Part.makeCylinder(
        SERVO_HORN_R, 3.5,
        App.Vector(boss_start_x - sign * 0.1, 0.0, SHOULDER_Z),
        App.Vector(sign, 0.0, 0.0)
    )
    screw_hole = Part.makeCylinder(
        SERVO_SCREW_R, ARM_T + 8.0,
        App.Vector(arm_cx - ARM_T, 0.0, SHOULDER_Z),
        App.Vector(1.0, 0.0, 0.0)
    )
    return arm_with_boss.cut(horn_socket).cut(screw_hole)


def build_printable_reverse_t_leg():
    """5_Reverse_T_Leg: Movable Reverse-T base with waist servo horn socket."""
    stem = chibi_pillow_box(
        T_STEM_W, T_STEM_D, T_STEM_H + 3.0,
        r_front=4.5, r_top=5.5,
        cx=0, cy=0, cz=T_BASE_H - 2.0
    )
    left_foot = chibi_pillow_box(
        T_BASE_W / 2.0 - 1.5, T_BASE_D, T_BASE_H,
        r_front=5.5, r_top=11.0,
        cx=-(T_BASE_W / 4.0 + 0.5), cy=-2.0, cz=0
    )
    right_foot = chibi_pillow_box(
        T_BASE_W / 2.0 - 1.5, T_BASE_D, T_BASE_H,
        r_front=5.5, r_top=11.0,
        cx=(T_BASE_W / 4.0 + 0.5), cy=-2.0, cz=0
    )
    bridge = rounded_prism_xy(26.0, T_BASE_D - 10.0, T_BASE_H, r=5.0, cx=0, cy=1.0, cz=0)
    t_leg = stem.fuse(left_foot).fuse(right_foot).fuse(bridge)

    top_z = T_BASE_H + T_STEM_H
    horn_socket = Part.makeCylinder(
        SERVO_HORN_R, 4.0,
        App.Vector(0, 0, top_z - 3.8),
        App.Vector(0, 0, 1)
    )
    screw_hole = Part.makeCylinder(
        SERVO_SCREW_R, top_z + 2.0,
        App.Vector(0, 0, -1.0),
        App.Vector(0, 0, 1)
    )
    return t_leg.cut(horn_socket).cut(screw_hole)


def build_printable_belly_buttons():
    """6_Belly_Button_Caps: 4 printable button plungers on a thin retaining backing frame."""
    backing = rounded_prism_xz(
        28.0, 1.2, 24.0, r=4.0,
        cx=0, cy=-TORSO_D / 2.0 + WALL, cz=BELLY_CZ - 14.5
    )
    btn_offsets = [(-8.5, 3.5), (8.5, 3.5), (-8.5, -8.5), (8.5, -8.5)]
    for bx, bz in btn_offsets:
        cap = Part.makeCylinder(
            3.4, 5.5,
            App.Vector(bx, -TORSO_D / 2.0 - 2.0, BELLY_CZ + bz),
            App.Vector(0, 1, 0)
        )
        backing = backing.fuse(cap)
    return backing


# ==============================================================================
# 5. COLOR-CODED HARDWARE PREVIEWS (Matches your drawing colors!)
# ==============================================================================
def build_hardware_previews():
    # GREEN: OLED Screen Module inside head slot
    green_screen = Part.makeBox(
        SCREEN_PCB_W - 1.0, 2.5, SCREEN_PCB_H - 1.0,
        App.Vector(-(SCREEN_PCB_W - 1.0) / 2.0, -HEAD_D / 2.0 + 3.0, SCREEN_CZ - (SCREEN_PCB_H - 1.0) / 2.0)
    )
    # PURPLE: Mini Speaker under top head grille
    purple_speaker = rounded_prism_xy(
        SPEAKER_W - 1.5, SPEAKER_D - 1.5, 3.5, r=4.0,
        cx=0, cy=0, cz=HEAD_Z0 + HEAD_H - WALL - 3.0
    )
    # SKY BLUE: Mobile Phone Battery inside belly bay
    skyblue_battery = Part.makeBox(
        BATT_W - 1.0, BATT_T - 1.0, BATT_H - 2.0,
        App.Vector(-(BATT_W - 1.0) / 2.0, -10.0, TORSO_Z0 + 15.5)
    )
    # RED: ESP32-S3 Board inside rear spine / back cover
    red_esp32 = Part.makeBox(
        ESP_W - 2.0, 3.0, ESP_H - 2.0,
        App.Vector(-(ESP_W - 2.0) / 2.0, TORSO_D / 2.0 - 2.0, TORSO_Z0 + 13.0)
    )
    return green_screen, purple_speaker, skyblue_battery, red_esp32


# ==============================================================================
# 6. BUILD FREECAD DOCUMENT & EXPORT STLS
# ==============================================================================
def create_printable_cupcake(output_dir=None, save_fcstd=None):
    doc = App.newDocument("CupCake_Printable_V3")

    green_scr, purple_spk, sky_bat, red_esp = build_hardware_previews()

    # Printable STL Parts
    printable_parts = [
        ("Part1_Main_Body_Shell", build_printable_main_body(), (0.22, 0.54, 0.96), 0),
        ("Part2_Back_Cover_ESP32", build_printable_back_cover(), (0.88, 0.92, 0.96), 35),
        ("Part3_Left_Hand_Arm", build_printable_hand_arm('LEFT'), (0.22, 0.54, 0.96), 0),
        ("Part4_Right_Hand_Arm", build_printable_hand_arm('RIGHT'), (0.22, 0.54, 0.96), 0),
        ("Part5_Reverse_T_Leg", build_printable_reverse_t_leg(), (0.22, 0.54, 0.96), 0),
        ("Part6_Belly_Button_Caps", build_printable_belly_buttons(), (0.98, 0.38, 0.58), 0),
    ]

    # Color-Coded Reference Modules (matching your drawing!)
    preview_parts = [
        ("Preview_GREEN_Screen", green_scr, (0.10, 0.85, 0.30)),
        ("Preview_PURPLE_Speaker", purple_spk, (0.70, 0.20, 0.90)),
        ("Preview_SKYBLUE_Battery", sky_bat, (0.15, 0.78, 0.98)),
        ("Preview_RED_ESP32", red_esp, (0.95, 0.18, 0.18)),
    ]

    created_objs = []
    for name, shape, rgb, transp in printable_parts:
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        created_objs.append(obj)
        if App.GuiUp:
            obj.ViewObject.ShapeColor = rgb
            obj.ViewObject.Transparency = transp

    hw_group = doc.addObject("App::DocumentObjectGroup", "Hardware_Color_Guides_DoNotPrint")
    for name, shape, rgb in preview_parts:
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        hw_group.addObject(obj)
        if App.GuiUp:
            obj.ViewObject.ShapeColor = rgb

    doc.recompute()

    if output_dir:
        import MeshPart
        os.makedirs(output_dir, exist_ok=True)
        for obj in created_objs:
            stl_path = os.path.join(output_dir, f"{obj.Label}.stl")
            mesh = MeshPart.meshFromShape(Shape=obj.Shape, LinearDeflection=0.1, AngularDeflection=0.523599)
            mesh.write(stl_path)
            print(f"Exported {stl_path} (triangles: {mesh.CountFacets})")

    if save_fcstd:
        doc.saveAs(save_fcstd)
        print(f"Saved FreeCAD project to {save_fcstd}")

    if App.GuiUp:
        try:
            import FreeCADGui as Gui
            av = Gui.activeDocument().activeView()
            av.viewAxometric()
            Gui.SendMsgToMainWindow("ViewFit")
        except Exception as e:
            print(f"GUI adjustment error: {e}")

    return doc


if __name__ == "__main__" or __name__ == "builtins":
    try:
        project_dir = os.path.dirname(os.path.abspath(__file__))
    except Exception:
        project_dir = os.path.abspath(".")
    cad_out = os.path.join(project_dir, "cad", "out_v3")
    fcstd_file = os.path.join(project_dir, "cad", "CupCake_Printable_V3.FCStd")
    create_printable_cupcake(output_dir=cad_out, save_fcstd=fcstd_file)
