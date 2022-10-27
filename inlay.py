from solid import *
import subprocess

## DIRECT PARAMETER
## card game dimensions
card_size = {"width":60, "height": 92, "thickness":0.24} # EU card (SKAT standard) 
#card_size = {"width": 50, "height": 100, "thickness": 0.24}  # test values
box_size = {"width": 298, "depth": 298, "height": 75} # size of a Dominion box
stack_count = [60, 40, 30, 12, 12, 24, 30, 16, 5] # number of cards of a stack. Every list entry represents a stack of cards.
equal_stacks = {"stacks":76, "count":10} # number of stacks with an equla stack size which are added to the stack_count
additional_trays = [] # size of additional trays (for coins, game figures, etc.). Every list entry represents a single tray.
## output path
output = "inlay.scad"

## printer model values
wall_thickness = 3 # defines the spacing and outer wall width.
printer_size = {"x": 210, "y": 210, "z": 205} # Anycubic i3 Mega S

## indirect parameter
height_factor = 0.6 # height of all stack seperators
stack_tolerance = 2 # tolerance for each stack tray
cover_spacing = 5 # space to fit the description card in Dominion. Propably not necessary in other games and can be set to "0"

## program flow control variables
single_tray_only = False # creats a single tray with the size of the first element in stack_count
#single_tray_only = True # creats a single tray with the size of the first element in stack_count
openSCAD_export_stl = True # calls openSCAD to export all files. DISABLE ON WINDOWS!
openSCAD_view = True # calls openSCAD to view all files. DISABLE ON WINDOWS!

'''
    ============================
!!! DO NOT MODIFY THE CODE BELOW !!!
    ============================
'''

## RUNTIME VARIABLES
a = cube(0) # openSCAD object to build. Initialize with an empty cube
current_pos = {"x": 0, "y": wall_thickness} # current posiotion for correct placement
stack_thickness = [] # claculated stack thickness (size of trays)
scad_file_names = [] # list of scad file names for export and view 


## FUNCTION DECLARATION
def create_outline(x, y):
    outline = cube([x, y, card_size["height"] + wall_thickness+cover_spacing])
    outline = outline - translate((wall_thickness, wall_thickness, -wall_thickness))(
        cube(
            [
                x - 2 * wall_thickness,
                y - 2 * wall_thickness,
                card_size["height"] + 3 * wall_thickness+cover_spacing,
            ]
        )
    )
    return outline

def add_eaqual_stacks_to_stack_count():
    for i in range(equal_stacks["stacks"]):
        stack_count.append(equal_stacks["count"])


def tray_cutout(stack_size):
    cutout = color((0, 1, 0))(
        translate(
            (
                card_size["width"] / 2 + wall_thickness,
                -wall_thickness,
                card_size["height"]*height_factor + wall_thickness,
            )
        )(
            rotate((-90, 0, 0))(
                cylinder(d=card_size["width"], h=stack_size + wall_thickness * 4)
            )
        )
    )
    return cutout


def single_tray(stack_size):
    tray = (
        cube(
            [
                card_size["width"] + wall_thickness * 2,
                stack_size + wall_thickness * 2,
                card_size["height"]*height_factor + wall_thickness,
            ]
        )
        - translate((wall_thickness, wall_thickness, -wall_thickness))(
            cube(
                [
                    card_size["width"],
                    stack_size,
                    card_size["height"]*height_factor + wall_thickness * 3,
                ]
            )
        )
        - tray_cutout(stack_size)
    )
    return tray


def cut_part(start_x, start_y, end_x, end_y, model):
    stencil = translate(
        (-box_size["width"] / 2, -box_size["depth"] / 2, -card_size["height"] / 2)
    )(
        cube([box_size["width"] * 2, box_size["depth"] * 2, card_size["height"] * 2])
    ) - translate(
        (start_x, start_y, -card_size["height"])
    )(
        cube([end_x - start_x, end_y - start_y, card_size["height"] * 3])
    )

    part = model - stencil
    return part


def partition_export(model):
    # preparing for a better partition process
    depth = box_size["depth"]
    width = box_size["width"]
    parts_width = 1
    parts_depth = 1
    parts = []

    while depth > printer_size["y"]:
        parts_depth = parts_depth + 1
        depth = depth - printer_size["y"]
    while width > printer_size["x"]:
        parts_width = parts_width + 1
        width = width - printer_size["x"]

    part_width = box_size["width"] / parts_width
    part_depth = box_size["depth"] / parts_depth
    for x in range(parts_width):
        for y in range(parts_depth):
            parts.append(
                cut_part(
                    start_x=part_width * x,
                    end_x=part_width * (x + 1),
                    start_y=part_depth * y,
                    end_y=part_depth * (y + 1),
                    model=model,
                )
            )

    path_file_ending = output.rsplit(".", maxsplit=1)
    print("- parts count: {}".format(len(parts)))

    for i in range(len(parts)):
        scad_file_name = "{}{}.{}".format(path_file_ending[0], i, path_file_ending[1])
        scad_file_names.append(scad_file_name)
        scad_render_to_file(parts[i], scad_file_name)
    return parts

def export_stl():
    print("export scad to stl")
    for i in range(len(parts)):
        print(f"- export file {i}")
        stl_file_name = scad_file_names[i].rsplit(".", maxsplit=1)
        subprocess.run(["openscad", "-q", "-o", f"{stl_file_name[0]}.stl", "--export-format", "asciistl", f"{scad_file_names[i]}"])
    print("- export complete model")
    subprocess.run(["openscad", "-q", "-o", "{}.stl".format(output.rsplit(".", maxsplit=1)[0]), "--export-format", "asciistl", f"{output}"])

def view_scad():
    print("view scad files")
   
    argument = [output]
    for i in range(len(scad_file_names)):
        argument.append(scad_file_names[i])
    subprocess.run(["openscad"] + argument)


## MAIN 
## calculate runtime variables
# stack_count
add_eaqual_stacks_to_stack_count()

# stack thickness
for i in range(len(stack_count)):
    stack_thickness.append(stack_count[i] * card_size["thickness"] + stack_tolerance)
stack_thickness = stack_thickness + additional_trays


if single_tray_only:
    print("creats a single tray with the size of the first element of stack_count[]")
    parts = partition_export(single_tray(stack_thickness[0]))
else:
    print("create whole inlay with {} elements".format(len(stack_count)))
    for i in range(len(stack_thickness) - 1):
        if (wall_thickness + stack_thickness[i] + current_pos["y"]) > box_size["depth"]:
            trans = (current_pos["x"], current_pos["y"] - wall_thickness, 0)
            tray_size = box_size["depth"] - current_pos["y"] - wall_thickness
            a = a + translate(trans)(single_tray(tray_size))
            current_pos["x"] = current_pos["x"] + card_size["width"] + wall_thickness
            current_pos["y"] = wall_thickness
        trans = (current_pos["x"], current_pos["y"] - wall_thickness, 0)
        a = a + translate(trans)(single_tray(stack_thickness[i]))
        current_pos["y"] = current_pos["y"] + stack_thickness[i] + wall_thickness
    a = a + translate((current_pos["x"], current_pos["y"] - wall_thickness, 0))(
        single_tray(box_size["depth"] - current_pos["y"] - wall_thickness))

    a = a + create_outline(box_size["width"], box_size["depth"])

    if (box_size["width"] > printer_size["x"]) or (box_size["depth"] > printer_size["y"]):
        print("Inlay dimensions are bigger than the printer can handle. start to partion the inlay")
    parts = partition_export(a)

scad_render_to_file(a, output)

if openSCAD_export_stl:
    export_stl()               

if openSCAD_view:
    view_scad()   

print("Done!")
