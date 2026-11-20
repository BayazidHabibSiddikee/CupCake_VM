import FreeCAD as App
import Part

# ==============================================================================
# 1. PARAMETRIC DIMENSIONS (in mm) - Matched to Mobile UI Chibi Proportions
# ==============================================================================
TOL = 0.35  # 3D print clearance

# Sub-Micro / Micro Servo (e.g., 4.3g GH-S37D or 9g SG90)
SERVO_L = 20.0 + TOL      # Servo body length
SERVO_W = 8.6 + TOL       # Servo body width
SERVO_D = 18.0            # Insertion depth into torso
SERVO_HORN_R = 3.2        # Servo horn socket radius
SERVO_SHAFT_R = 2.2       # Output boss radius

# 0.96" OLED Display (SSD1306 128x64)
OLED_VIEW_W = 26.0
OLED_VIEW_H = 14.5
OLED_PCB_W = 28.0 + TOL
OLED_PCB_H = 28.0 + TOL

# ESP32-S3 Board on Back (Seeed XIAO / SuperMini or DevKitC-1)
ESP_W = 28.5 + TOL
ESP_H = 44.0 + TOL
ESP_T = 4.5

# Chibi Robot Proportions (Matches Phone App Mascot)
HEAD_W = 68.0
HEAD_D = 40.0
HEAD_H = 46.0

NECK_W = 22.0
NECK_D = 18.0
NECK_H = 5.0

TORSO_W = 54.0
TORSO_D = 38.0
TORSO_H = 52.0
WALL = 2.8

ARM_L = 42.0
ARM_W = 14.0
ARM_T = 9.0

# Reverse-T Leg Proportions
T_STEM_W = 20.0           # Vertical column of Reverse-T
T_STEM_D = 18.0
T_STEM_H = 14.0
T_BASE_W = 62.0           # Horizontal bottom bar of Reverse-T
T_BASE_D = 40.0
T_BASE_H = 11.0


# ==============================================================================
# 2. BULLETPROOF ROUNDED GEOMETRY HELPERS (Zero fragile 3D fillets)
# ==============================================================================
def rounded_prism_xz(w, d, h, r, cx=0.0, cy=0.0, cz=0.0):
    """Creates a block with smooth rounded corners in the Front View (X-Z plane)."""
    r = min(r, w / 2.0 - 0.2, h / 2.0 - 0.2)
    b1 = Part.makeBox(w - 2 * r, d, h, App.Vector(cx - w / 2.0 + r, cy - d / 2.0, cz))
    b2 = Part.makeBox(w, d, h - 2 * r, App.Vector(cx - w / 2.0, cy - d / 2.0, cz + r))
    shape = b1.fuse(b2)
    corners = [
        (cx - w / 2.0 + r, cz + r),
        (cx + w / 2.0 - r, cz + r),
        (cx - w / 2.0 + r, cz + h - r),
        (cx + w / 2.0 - r, cz + h - r),
    ]
    for x, z in corners:
        cyl = Part.makeCylinder(r, d, App.Vector(x, cy - d / 2.0, z), App.Vector(0, 1, 0))
        shape = shape.fuse(cyl)
    return shape


def rounded_prism_xy(w, d, h, r, cx=0.0, cy=0.0, cz=0.0):
    """Creates a block with smooth rounded vertical corners in the Top View (X-Y plane)."""
    r = min(r, w / 2.0 - 0.2, d / 2.0 - 0.2)
    b1 = Part.makeBox(w - 2 * r, d, h, App.Vector(cx - w / 2.0 + r, cy - d / 2.0, cz))
    b2 = Part.makeBox(w, d - 2 * r, h, App.Vector(cx - w / 2.0, cy - d / 2.0 + r, cz))
    shape = b1.fuse(b2)
    corners = [
        (cx - w / 2.0 + r, cy - d / 2.0 + r),
        (cx + w / 2.0 - r, cy - d / 2.0 + r),
        (cx - w / 2.0 + r, cy + d / 2.0 - r),
        (cx + w / 2.0 - r, cy + d / 2.0 - r),
    ]
    for x, y in corners:
        cyl = Part.makeCylinder(r, h, App.Vector(x, y, cz), App.Vector(0, 0, 1))
        shape = shape.fuse(cyl)
    return shape


def chibi_pillow_box(w, d, h, r_front, r_top, cx=0.0, cy=0.0, cz=0.0):
    """Intersects Front and Top rounded prisms to form a smooth 3D Chibi shell."""
    p_xz = rounded_prism_xz(w, d, h, r_front, cx, cy, cz)
    p_xy = rounded_prism_xy(w, d, h, r_top, cx, cy, cz)
    return p_xz.common(p_xy)


# ==============================================================================
# 3. COMPONENT BUILDERS (Matched to Phone UI + Hardware Requirements)
# ==============================================================================
TORSO_Z0 = T_BASE_H + T_STEM_H + 1.5
NECK_Z0 = TORSO_Z0 + TORSO_H - 1.0
HEAD_Z0 = NECK_Z0 + NECK_H - 1.0
SHOULDER_Z = TORSO_Z0 + TORSO_H - 13.0


def build_main_blue_body():
    """Builds the hollow Blue Torso + Fixed Neck + Rounded Chibi Head + ESP32 Back Mount + 3 Servo Bays."""
    # 1. Outer Chibi Torso, Fixed Neck, and Wide Stadium Head
    torso = chibi_pillow_box(TORSO_W, TORSO_D, TORSO_H, r_front=10.0, r_top=10.0, cz=TORSO_Z0)
    neck = rounded_prism_xy(NECK_W, NECK_D, NECK_H + 3.0, r=6.0, cz=NECK_Z0)
    head = chibi_pillow_box(HEAD_W, HEAD_D, HEAD_H, r_front=15.0, r_top=12.0, cz=HEAD_Z0)

    # Rear ESP32-S3 Protective Frame Boss on the back of the torso (+Y is Back)
    esp_frame_z = TORSO_Z0 + (TORSO_H - (ESP_H + 6.0)) / 2.0
    esp_outer_frame = rounded_prism_xz(
        ESP_W + 6.0, 6.0, ESP_H + 6.0, r=4.0,
        cx=0, cy=TORSO_D / 2.0 + 1.0, cz=esp_frame_z
    )

    outer_body = torso.fuse(neck).fuse(head).fuse(esp_outer_frame)

    # 2. Internal Hollow Cavity & Neck Wire Conduit
    torso_cavity = chibi_pillow_box(
        TORSO_W - 2 * WALL, TORSO_D - 2 * WALL, TORSO_H - 2 * WALL - 8.0,
        r_front=7.0, r_top=7.0, cz=TORSO_Z0 + WALL + 6.0
    )
    neck_conduit = Part.makeCylinder(
        5.5, NECK_H + 18.0,
        App.Vector(0, 0, TORSO_Z0 + TORSO_H - 10.0),
        App.Vector(0, 0, 1)
    )

    # 3. Front Head Recess for White Bezel & OLED PCB (-Y is Front)
    bezel_recess = rounded_prism_xz(
        HEAD_W - 10.0, 6.0, HEAD_H - 10.0, r=11.0,
        cx=0, cy=-HEAD_D / 2.0 + 1.0, cz=HEAD_Z0 + 5.0
    )
    oled_pcb_pocket = Part.makeBox(
        OLED_PCB_W, 10.0, OLED_PCB_H,
        App.Vector(-OLED_PCB_W / 2.0, -HEAD_D / 2.0 + 3.0, HEAD_Z0 + (HEAD_H - OLED_PCB_H) / 2.0)
    )

    # 4. Rear ESP32-S3 Board Pocket & Wire Pass-Through (+Y is Back)
    esp_pocket = Part.makeBox(
        ESP_W, ESP_T + 3.0, ESP_H,
        App.Vector(-ESP_W / 2.0, TORSO_D / 2.0 - 0.5, TORSO_Z0 + (TORSO_H - ESP_H) / 2.0)
    )
    esp_wire_hole = Part.makeBox(
        ESP_W - 8.0, 12.0, 16.0,
        App.Vector(-(ESP_W - 8.0) / 2.0, TORSO_D / 2.0 - 6.0, TORSO_Z0 + TORSO_H / 2.0 - 8.0)
    )
    usb_bottom_slot = Part.makeBox(
        12.0, 10.0, 12.0,
        App.Vector(-6.0, TORSO_D / 2.0 - 1.0, TORSO_Z0 - 1.0)
    )

    # 5. Three Micro-Servo Pockets (Left Shoulder, Right Shoulder, Bottom Waist)
    l_servo_bay = Part.makeBox(
        SERVO_D, SERVO_W, SERVO_L,
        App.Vector(-TORSO_W / 2.0 - 1.0, -SERVO_W / 2.0, SHOULDER_Z - SERVO_L + 5.0)
    )
    r_servo_bay = Part.makeBox(
        SERVO_D, SERVO_W, SERVO_L,
        App.Vector(TORSO_W / 2.0 - SERVO_D + 1.0, -SERVO_W / 2.0, SHOULDER_Z - SERVO_L + 5.0)
    )
    b_servo_bay = Part.makeBox(
        SERVO_L, SERVO_W, SERVO_D,
        App.Vector(-SERVO_L / 2.0, -SERVO_W / 2.0, TORSO_Z0 - 1.0)
    )

    cuts = (
        torso_cavity
        .fuse(neck_conduit)
        .fuse(bezel_recess)
        .fuse(oled_pcb_pocket)
        .fuse(esp_pocket)
        .fuse(esp_wire_hole)
        .fuse(usb_bottom_slot)
        .fuse(l_servo_bay)
        .fuse(r_servo_bay)
        .fuse(b_servo_bay)
    )
    return outer_body.cut(cuts)


def build_white_face_and_belly():
    """Builds the White Face Bezel and White Belly Plate from the mobile UI."""
    # White Face Bezel inside the head front
    bezel_outer = rounded_prism_xz(
        HEAD_W - 10.5, 4.0, HEAD_H - 10.5, r=10.8,
        cx=0, cy=-HEAD_D / 2.0 + 1.5, cz=HEAD_Z0 + 5.25
    )
    visor_cut = rounded_prism_xz(
        HEAD_W - 18.0, 8.0, HEAD_H - 18.0, r=8.0,
        cx=0, cy=-HEAD_D / 2.0 + 1.0, cz=HEAD_Z0 + 9.0
    )
    face_bezel = bezel_outer.cut(visor_cut)

    # White Rounded Belly Plate on front of torso (-Y)
    belly_w = 34.0
    belly_h = 36.0
    belly_z = TORSO_Z0 + (TORSO_H - belly_h) / 2.0 - 1.0
    belly = rounded_prism_xz(
        belly_w, 2.5, belly_h, r=9.0,
        cx=0, cy=-TORSO_D / 2.0 - 0.4, cz=belly_z
    )
    # Small blue dot cutout at top center of white belly (matches phone sprite!)
    dot_cut = Part.makeCylinder(
        2.2, 5.0,
        App.Vector(0, -TORSO_D / 2.0 - 2.0, belly_z + belly_h - 6.0),
        App.Vector(0, 1, 0)
    )
    belly = belly.cut(dot_cut)

    return face_bezel.fuse(belly)


def build_black_oled_visor():
    """Builds the Black Screen Visor with active OLED window."""
    visor = rounded_prism_xz(
        HEAD_W - 18.4, 3.0, HEAD_H - 18.4, r=7.8,
        cx=0, cy=-HEAD_D / 2.0 + 2.2, cz=HEAD_Z0 + 9.2
    )
    return visor


def build_cyan_oled_eyes():
    """Builds happy ^ ‿ ^ cyan OLED pixel eyes on the screen face."""
    eye_y = -HEAD_D / 2.0 + 0.5
    eye_z = HEAD_Z0 + HEAD_H / 2.0 + 1.0

    def make_happy_arc(cx):
        outer = Part.makeCylinder(5.0, 1.0, App.Vector(cx, eye_y, eye_z), App.Vector(0, 1, 0))
        inner = Part.makeCylinder(2.8, 3.0, App.Vector(cx, eye_y - 1.0, eye_z - 0.5), App.Vector(0, 1, 0))
        bottom_trim = Part.makeBox(12.0, 3.0, 6.0, App.Vector(cx - 6.0, eye_y - 1.0, eye_z - 6.0))
        return outer.cut(inner).cut(bottom_trim)

    left_eye = make_happy_arc(-11.0)
    right_eye = make_happy_arc(11.0)

    # Cute little smile in the middle
    smile_outer = Part.makeCylinder(3.2, 1.0, App.Vector(0, eye_y, eye_z - 3.5), App.Vector(0, 1, 0))
    smile_inner = Part.makeCylinder(1.8, 3.0, App.Vector(0, eye_y - 1.0, eye_z - 3.5), App.Vector(0, 1, 0))
    top_trim = Part.makeBox(8.0, 3.0, 4.0, App.Vector(-4.0, eye_y - 1.0, eye_z - 3.5))
    smile = smile_outer.cut(smile_inner).cut(top_trim)

    return left_eye.fuse(right_eye).fuse(smile)


def build_capsule_arm(side='LEFT'):
    """Builds a smooth rounded capsule arm coupled to the shoulder servo shaft."""
    sign = -1.0 if side == 'LEFT' else 1.0
    arm_cx = sign * (TORSO_W / 2.0 + ARM_T / 2.0 + 1.8)
    arm_z0 = SHOULDER_Z - ARM_L + ARM_W / 2.0

    # Smooth capsule paddle
    arm = chibi_pillow_box(
        ARM_T, ARM_W, ARM_L,
        r_front=ARM_T / 2.0 - 0.3,
        r_top=ARM_T / 2.0 - 0.3,
        cx=arm_cx, cy=0, cz=arm_z0
    )
    # Round the top and bottom in the Y-Z side profile as well
    side_round = rounded_prism_xz(
        ARM_W, ARM_T + 4.0, ARM_L, r=ARM_W / 2.0 - 0.3,
        cx=0, cy=arm_cx, cz=arm_z0
    )
    # Rotate side_round 90 deg around Z to align with Y-Z plane
    side_round.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 90)
    # Translate to arm_cx
    side_round.translate(App.Vector(arm_cx, -arm_cx, 0))
    arm = arm.common(side_round)

    # Servo shaft boss connecting arm to shoulder servo
    boss_start_x = sign * (TORSO_W / 2.0 - 2.0)
    boss = Part.makeCylinder(
        SERVO_HORN_R, 5.0,
        App.Vector(boss_start_x, 0, SHOULDER_Z),
        App.Vector(sign, 0, 0)
    )
    return arm.fuse(boss)


def build_reverse_t_leg():
    """Builds the movable Reverse-T shaped leg with rounded dual-foot lobes."""
    # 1. Vertical stem of the Reverse-T (coupled to bottom waist servo)
    stem = chibi_pillow_box(
        T_STEM_W, T_STEM_D, T_STEM_H + 3.0,
        r_front=4.0, r_top=5.0,
        cx=0, cy=0, cz=T_BASE_H - 2.0
    )

    # 2. Horizontal wide bottom bar of the Reverse-T (sculpted into cute twin feet)
    left_lobe = chibi_pillow_box(
        T_BASE_W / 2.0 - 1.5, T_BASE_D, T_BASE_H,
        r_front=5.0, r_top=10.0,
        cx=-(T_BASE_W / 4.0 + 0.5), cy=-2.0, cz=0
    )
    right_lobe = chibi_pillow_box(
        T_BASE_W / 2.0 - 1.5, T_BASE_D, T_BASE_H,
        r_front=5.0, r_top=10.0,
        cx=(T_BASE_W / 4.0 + 0.5), cy=-2.0, cz=0
    )
    center_bridge = rounded_prism_xy(
        24.0, T_BASE_D - 10.0, T_BASE_H, r=5.0,
        cx=0, cy=1.0, cz=0
    )

    t_leg = stem.fuse(left_lobe).fuse(right_lobe).fuse(center_bridge)

    # Top servo horn socket on the Reverse-T stem
    top_z = T_BASE_H + T_STEM_H
    horn_cut = Part.makeCylinder(
        SERVO_HORN_R, 4.0,
        App.Vector(0, 0, top_z - 3.5),
        App.Vector(0, 0, 1)
    )
    return t_leg.cut(horn_cut)


def build_esp32_preview_board():
    """Visual representation of the ESP32-S3 mounted in the back pocket (+Y)."""
    pcb_z = TORSO_Z0 + (TORSO_H - ESP_H) / 2.0 + 0.5
    pcb = Part.makeBox(
        ESP_W - 1.0, 2.0, ESP_H - 1.0,
        App.Vector(-(ESP_W - 1.0) / 2.0, TORSO_D / 2.0 + 1.0, pcb_z)
    )
    usb_c = Part.makeBox(
        9.0, 3.2, 7.5,
        App.Vector(-4.5, TORSO_D / 2.0 + 1.5, pcb_z - 2.0)
    )
    return pcb.fuse(usb_c)


# ==============================================================================
# 4. GENERATE FREECAD DOCUMENT WITH MATCHING COLORS & EXPORT STLS
# ==============================================================================
def create_cupcake_chibi(output_dir=None, save_fcstd=None):
    doc = App.newDocument("CupCake_Chibi_Robot")

    components = [
        ("Body_And_FixedHead_Blue", build_main_blue_body(), (0.20, 0.52, 0.96)),
        ("FaceBezel_And_Belly_White", build_white_face_and_belly(), (0.96, 0.97, 0.99)),
        ("OLED_Visor_Black", build_black_oled_visor(), (0.08, 0.09, 0.12)),
        ("OLED_Eyes_Cyan", build_cyan_oled_eyes(), (0.15, 0.92, 1.00)),
        ("Left_Arm_Servo", build_capsule_arm('LEFT'), (0.20, 0.52, 0.96)),
        ("Right_Arm_Servo", build_capsule_arm('RIGHT'), (0.20, 0.52, 0.96)),
        ("Reverse_T_Leg_Servo", build_reverse_t_leg(), (0.20, 0.52, 0.96)),
        ("ESP32_S3_Back_Board", build_esp32_preview_board(), (0.12, 0.45, 0.25)),
    ]

    for name, shape, rgb in components:
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        if App.GuiUp:
            obj.ViewObject.ShapeColor = rgb
            obj.ViewObject.DisplayMode = "Shaded"

    doc.recompute()

    if output_dir:
        import os
        import Mesh
        os.makedirs(output_dir, exist_ok=True)
        # Export printable parts
        printable_parts = [
            "Body_And_FixedHead_Blue",
            "FaceBezel_And_Belly_White",
            "Left_Arm_Servo",
            "Right_Arm_Servo",
            "Reverse_T_Leg_Servo",
        ]
        for part_name in printable_parts:
            obj = doc.getObject(part_name)
            stl_path = os.path.join(output_dir, f"{part_name}.stl")
            Mesh.export([obj], stl_path)
            print(f"Exported {stl_path}")

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


if __name__ == "__main__":
    import os
    project_dir = os.path.dirname(os.path.abspath(__file__))
    cad_out = os.path.join(project_dir, "cad", "out")
    fcstd_file = os.path.join(project_dir, "cad", "CupCake_Chibi_Robot.FCStd")
    create_cupcake_chibi(output_dir=cad_out, save_fcstd=fcstd_file)
