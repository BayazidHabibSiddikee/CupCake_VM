import FreeCAD as App
import Part
import math
import os

# ==============================================================================
# 1. PARAMETRIC CONFIGURATION (All dimensions in mm)
# ==============================================================================
TOL = 0.4  # 3D printing clearance tolerance

# Micro Servo (Default: 9g SG90 / MG90S. Change to 19.6 x 8.2 x 20.0 for 4.3g servo)
SERVO_L = 23.2 + TOL   # Length of servo body
SERVO_W = 12.4 + TOL   # Width of servo body
SERVO_H = 22.5         # Depth of body into cavity before mounting tabs
SERVO_SHAFT_OFFSET = 6.0  # Distance from one end of servo to output shaft axis
SERVO_HORN_R = 3.6     # Radius of circular servo horn boss socket
SERVO_SCREW_R = 1.2    # M2 screw pass-through radius

# OLED Display (0.96" SSD1306 I2C Module)
OLED_PCB_W = 27.8 + TOL
OLED_PCB_H = 28.0 + TOL
OLED_SCREEN_W = 24.5   # Active viewing window width
OLED_SCREEN_H = 14.0   # Active viewing window height

# ESP32-S3 Mount on Back of Torso (ESP32-S3-DevKitC-1 default; adjust for XIAO)
ESP_W = 28.4 + TOL
ESP_H = 57.6 + TOL
ESP_DEPTH = 5.0        # Depth of back pocket recess

# Robot Body Proportions
TORSO_W = 64.0         # X width
TORSO_D = 46.0         # Y depth
TORSO_H = 68.0         # Z height
WALL = 3.0             # Shell wall thickness

NECK_W = 20.0
NECK_D = 18.0
NECK_H = 10.0

HEAD_W = 58.0
HEAD_D = 38.0
HEAD_H = 38.0

ARM_L = 54.0           # Arm length
ARM_W = 16.0           # Arm width
ARM_T = 7.0            # Arm thickness

LEG_STEM_W = 20.0      # Vertical column of Reverse-T
LEG_STEM_D = 20.0
LEG_STEM_H = 22.0

LEG_BASE_W = 72.0      # Horizontal foot of Reverse-T
LEG_BASE_D = 48.0
LEG_BASE_H = 10.0


# ==============================================================================
# 2. GEOMETRY HELPER FUNCTIONS
# ==============================================================================
def make_centered_box(w, d, h, cx=0, cy=0, cz=0, fillet_r=0):
    """Creates a box centered on X and Y, starting at cz in Z, with safe fillets."""
    box = Part.makeBox(w, d, h, App.Vector(cx - w / 2.0, cy - d / 2.0, cz))
    if fillet_r > 0:
        box = box.makeFillet(fillet_r, box.Edges)
    return box


def make_servo_cutout(origin, orientation):
    """Creates a subtraction volume for a micro servo + wire slot + shaft hole.
    orientation: 'LEFT' (-X shaft), 'RIGHT' (+X shaft), or 'BOTTOM' (-Z shaft)
    """
    if orientation in ('LEFT', 'RIGHT'):
        # Servo body aligned vertically (Z = SERVO_L, Y = SERVO_W, X = SERVO_H)
        bx = SERVO_H
        by = SERVO_W
        bz = SERVO_L
        sx = origin.x - (bx if orientation == 'RIGHT' else 0)
        sy = origin.y - by / 2.0
        sz = origin.z - (bz - SERVO_SHAFT_OFFSET)
        body = Part.makeBox(bx, by, bz, App.Vector(sx, sy, sz))

        # Output shaft hole through torso wall
        shaft_dir = App.Vector(1 if orientation == 'RIGHT' else -1, 0, 0)
        shaft_start = App.Vector(origin.x - 10 * shaft_dir.x, origin.y, origin.z)
        shaft = Part.makeCylinder(SERVO_HORN_R + 1.0, 25.0, shaft_start, shaft_dir)
        return body.fuse(shaft)

    elif orientation == 'BOTTOM':
        # Servo body at bottom center, shaft pointing down (-Z), body extending up (+Z)
        bx = SERVO_L
        by = SERVO_W
        bz = SERVO_H
        sx = origin.x - SERVO_SHAFT_OFFSET
        sy = origin.y - by / 2.0
        sz = origin.z
        body = Part.makeBox(bx, by, bz, App.Vector(sx, sy, sz))
        shaft = Part.makeCylinder(
            SERVO_HORN_R + 1.0, 20.0,
            App.Vector(origin.x, origin.y, origin.z - 10.0),
            App.Vector(0, 0, 1)
        )
        return body.fuse(shaft)


# ==============================================================================
# 3. PART BUILDERS
# ==============================================================================
def build_body_and_fixed_head():
    """Builds the main torso, fixed neck, fixed head, OLED window, ESP32 dock, and 3 servo bays."""
    torso_z0 = LEG_BASE_H + LEG_STEM_H + 2.0  # Clearance above Reverse-T leg

    # 1. Outer Torso + Fixed Neck + Outer Head
    torso_outer = make_centered_box(TORSO_W, TORSO_D, TORSO_H, 0, 0, torso_z0, fillet_r=4.0)

    neck_z0 = torso_z0 + TORSO_H - 2.0
    neck_outer = make_centered_box(NECK_W, NECK_D, NECK_H + 4.0, 0, 0, neck_z0, fillet_r=2.0)

    head_z0 = neck_z0 + NECK_H
    head_outer = make_centered_box(HEAD_W, HEAD_D, HEAD_H, 0, 0, head_z0, fillet_r=8.0)

    main_shell = torso_outer.fuse(neck_outer).fuse(head_outer)

    # 2. Internal Torso Hollow Cavity (leaving thick walls around servo mounts)
    cavity = make_centered_box(
        TORSO_W - 2 * WALL,
        TORSO_D - 2 * WALL - ESP_DEPTH,
        TORSO_H - 2 * WALL - 12.0,
        0, -ESP_DEPTH / 2.0, torso_z0 + WALL + 10.0
    )

    # 3. Wire Conduit through Fixed Neck (Connects OLED face to ESP32 back bay)
    neck_wire_tunnel = Part.makeCylinder(
        5.0, NECK_H + 20.0,
        App.Vector(0, 0, torso_z0 + TORSO_H - 15.0),
        App.Vector(0, 0, 1)
    )

    # 4. OLED Visor Recess & PCB Pocket on Front Face (-Y is front)
    head_center_z = head_z0 + HEAD_H / 2.0
    visor_recess = make_centered_box(
        HEAD_W - 12.0, 6.0, HEAD_H - 12.0,
        0, -HEAD_D / 2.0 + 1.0, head_z0 + 6.0, fillet_r=2.0
    )
    oled_window = make_centered_box(
        OLED_SCREEN_W, 12.0, OLED_SCREEN_H,
        0, -HEAD_D / 2.0, head_center_z - OLED_SCREEN_H / 2.0
    )
    oled_pcb_bay = make_centered_box(
        OLED_PCB_W, 8.0, OLED_PCB_H,
        0, -HEAD_D / 2.0 + 5.0, head_center_z - OLED_PCB_H / 2.0
    )

    # 5. Back Body ESP32-S3 Mounting Pocket (+Y is back)
    esp_z0 = torso_z0 + (TORSO_H - ESP_H) / 2.0
    esp_pocket = make_centered_box(
        ESP_W, ESP_DEPTH + 2.0, ESP_H,
        0, TORSO_D / 2.0 - ESP_DEPTH / 2.0 + 1.0, esp_z0
    )
    # Wire pass-through slot from ESP32 bay into torso interior
    esp_wire_slot = make_centered_box(
        ESP_W - 8.0, 16.0, 18.0,
        0, TORSO_D / 2.0 - ESP_DEPTH, torso_z0 + TORSO_H / 2.0 - 9.0
    )
    # Bottom USB-C cable access notch for ESP32-S3
    usb_notch = make_centered_box(
        14.0, ESP_DEPTH + 4.0, 15.0,
        0, TORSO_D / 2.0 - ESP_DEPTH / 2.0, torso_z0 - 1.0
    )

    # 6. Three Micro Servo Bays (Left Shoulder, Right Shoulder, Bottom Waist)
    shoulder_z = torso_z0 + TORSO_H - 14.0
    left_servo = make_servo_cutout(App.Vector(-TORSO_W / 2.0, 0, shoulder_z), 'LEFT')
    right_servo = make_servo_cutout(App.Vector(TORSO_W / 2.0, 0, shoulder_z), 'RIGHT')
    bottom_servo = make_servo_cutout(App.Vector(0, 0, torso_z0), 'BOTTOM')

    # Combine all cutouts and subtract from main body
    cuts = (
        cavity
        .fuse(neck_wire_tunnel)
        .fuse(visor_recess)
        .fuse(oled_window)
        .fuse(oled_pcb_bay)
        .fuse(esp_pocket)
        .fuse(esp_wire_slot)
        .fuse(usb_notch)
        .fuse(left_servo)
        .fuse(right_servo)
        .fuse(bottom_servo)
    )

    return main_shell.cut(cuts)


def build_movable_arm(side='LEFT'):
    """Builds a rounded paddle arm with a servo horn recess at the shoulder pivot."""
    torso_z0 = LEG_BASE_H + LEG_STEM_H + 2.0
    shoulder_z = torso_z0 + TORSO_H - 14.0
    sign = -1 if side == 'LEFT' else 1
    arm_cx = sign * (TORSO_W / 2.0 + ARM_T / 2.0 + 1.5)

    # Rounded vertical arm bar with cylindrical top and bottom caps
    bar_h = ARM_L - ARM_W
    bar_z0 = shoulder_z - bar_h + (ARM_W / 2.0)
    bar = make_centered_box(ARM_T, ARM_W, bar_h, arm_cx, 0, bar_z0 - ARM_W / 2.0)

    top_cyl = Part.makeCylinder(
        ARM_W / 2.0, ARM_T,
        App.Vector(arm_cx - ARM_T / 2.0, 0, shoulder_z),
        App.Vector(1, 0, 0)
    )
    bot_cyl = Part.makeCylinder(
        ARM_W / 2.0, ARM_T,
        App.Vector(arm_cx - ARM_T / 2.0, 0, shoulder_z - bar_h),
        App.Vector(1, 0, 0)
    )
    arm_solid = bar.fuse(top_cyl).fuse(bot_cyl)

    # Servo horn pocket on inner face + M2 screw hole
    inner_x = arm_cx - sign * (ARM_T / 2.0)
    horn_dir = App.Vector(sign, 0, 0)
    horn_pocket = Part.makeCylinder(SERVO_HORN_R, 3.5, App.Vector(inner_x, 0, shoulder_z), horn_dir)
    screw_hole = Part.makeCylinder(SERVO_SCREW_R, ARM_T + 4.0, App.Vector(arm_cx - ARM_T, 0, shoulder_z), App.Vector(1, 0, 0))

    return arm_solid.cut(horn_pocket.fuse(screw_hole))


def build_reverse_t_leg():
    """Builds the Reverse-T shaped leg/base with a top servo horn socket."""
    # Horizontal wide base plate (the bottom bar of the upside-down T)
    base_plate = make_centered_box(LEG_BASE_W, LEG_BASE_D, LEG_BASE_H, 0, 0, 0, fillet_r=3.0)

    # Front center cutout to give the signature dual-foot silhouette from your sketch
    foot_notch = make_centered_box(16.0, 14.0, LEG_BASE_H + 4.0, 0, -LEG_BASE_D / 2.0 + 5.0, -2.0, fillet_r=2.0)
    base_plate = base_plate.cut(foot_notch)

    # Vertical center stem (the vertical column of the upside-down T)
    stem = make_centered_box(LEG_STEM_W, LEG_STEM_D, LEG_STEM_H + 2.0, 0, 0, LEG_BASE_H - 2.0, fillet_r=2.5)
    t_leg = base_plate.fuse(stem)

    # Top servo horn socket (couples to the bottom waist servo shaft)
    top_z = LEG_BASE_H + LEG_STEM_H
    horn_socket = Part.makeCylinder(
        SERVO_HORN_R, 4.0,
        App.Vector(0, 0, top_z - 4.0),
        App.Vector(0, 0, 1)
    )
    screw_channel = Part.makeCylinder(
        SERVO_SCREW_R, LEG_BASE_H + LEG_STEM_H + 2.0,
        App.Vector(0, 0, -1.0),
        App.Vector(0, 0, 1)
    )

    return t_leg.cut(horn_socket.fuse(screw_channel))


# ==============================================================================
# 4. DOCUMENT GENERATION & SAVE
# ==============================================================================
def create_cupcake_document():
    doc = App.newDocument("CupCake_Robot_CAD")

    parts = [
        ("Body_FixedHead", build_body_and_fixed_head(), (0.22, 0.52, 0.82)),  # Robot Blue
        ("Left_Arm", build_movable_arm('LEFT'), (0.22, 0.52, 0.82)),          # Robot Blue
        ("Right_Arm", build_movable_arm('RIGHT'), (0.22, 0.52, 0.82)),        # Robot Blue
        ("Reverse_T_Leg", build_reverse_t_leg(), (0.92, 0.94, 0.96)),         # Off-White Accent
    ]

    for name, shape, color in parts:
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        if App.GuiUp:
            obj.ViewObject.ShapeColor = color
    doc.recompute()
    if App.GuiUp:
        import FreeCADGui as Gui
        Gui.SendMsgToMainWindow("ViewFit")
        Gui.activeDocument().activeView().viewIsometric()

    # Save the document as FCStd file
    # Use user home directory for compatibility
    home_dir = os.path.expanduser("~")
    save_path = os.path.join(home_dir, "CupCake_Robot.FCStd")
    doc.save(save_path)
    print(f"CupCake robot FCStd saved to: {save_path}")
    print(f"File exists: {os.path.exists(save_path)}")

    return doc


if __name__ == "__main__":
    create_cupcake_document()
