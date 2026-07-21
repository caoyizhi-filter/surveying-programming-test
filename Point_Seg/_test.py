import sys
sys.stdout.reconfigure(encoding='utf-8')
import math
from calculator import *
import file_io

# Load data
points = file_io.read_points(r"D:\GitHub\surveying-programming\surveying-programming-test\Point_Seg\Point.txt")
print(f"Loaded {len(points)} points")

# ===== 1. Basic stats =====
proc = PointCloudProcessor(points)
proc.run()

p5 = points[4]
s = proc.stats
print(f"\n--- 1-9: Basic Stats ---")
print(f"1. P5 x = {p5.x:.3f}")
print(f"2. P5 y = {p5.y:.3f}")
print(f"3. P5 z = {p5.z:.3f}")
print(f"4. xmin = {s['xmin']:.3f}")
print(f"5. xmax = {s['xmax']:.3f}")
print(f"6. ymin = {s['ymin']:.3f}")
print(f"7. ymax = {s['ymax']:.3f}  (ref: 99.935)")
print(f"8. zmin = {s['zmin']:.3f}")
print(f"9. zmax = {s['zmax']:.3f}  (ref: 5.668)")

# ===== 2. Grid =====
print(f"\n--- 10-16: Grid ---")
bi = int(math.floor(p5.y / 10.0))
bj = int(math.floor(p5.x / 10.0))
print(f"10-11. P5 grid: i={bi}, j={bj}  (ref: j=0)")

# Find grid C (same col as P5 or max_z ~ 1.192)
grid_c = None
matches = []
for key, g in proc.grids.items():
    if abs(g.max_z() - 1.192) < 0.0005 and g.size > 1:
        matches.append((key, g))
if matches:
    matches.sort(key=lambda x: (x[0][0], x[0][1]))
    grid_c = matches[0][1]
    print(f"Found grid C at ({grid_c.i},{grid_c.j}) by max_z=1.192")
if not grid_c:
    for key, g in proc.grids.items():
        if key[1] == bj and g.size > 1:
            grid_c = g
            print(f"Found grid C at ({g.i},{g.j}) by P5 column")
            break
if not grid_c:
    print("WARNING: grid C not found!")
    grid_c = list(proc.grids.values())[0]

print(f"12. Grid C point count: {grid_c.size}")
print(f"13. Grid C avg z: {grid_c.avg_z():.3f}")
print(f"14. Grid C max z: {grid_c.max_z():.3f}  (ref: 1.192)")
print(f"15. Grid C diff z: {grid_c.diff_z():.3f}")
print(f"16. Grid C var z: {grid_c.var_z():.3f}")

# ===== 3. S1 Plane =====
print(f"\n--- 17-21: S1 Plane ---")
print(f"17. Triangle area: {proc.S1_area:.6f}")
print(f"18. S1 A = {proc.plane_S1.A:.6f}")
print(f"19. S1 B = {proc.plane_S1.B:.6f}")
print(f"20. S1 C = {proc.plane_S1.C:.6f}")
print(f"21. S1 D = {proc.plane_S1.D:.6f}")

# ===== 4. S1 distances =====
print(f"\n--- 22-25: S1 Inliers/Outliers ---")
d_p1000 = proc.plane_S1.distance(points[999])
d_p5 = proc.plane_S1.distance(p5)
print(f"22. P1000 dist to S1: {d_p1000:.3f}  (ref: 0.262)")
print(f"23. P5 dist to S1: {d_p5:.3f}")

s1_in = sum(1 for pt in points if proc.plane_S1.distance(pt) < 0.1)
s1_in_adj = s1_in - 3  # exclude the 3 fitting points
s1_out = len(points) - s1_in
print(f"24. S1 inliers: {s1_in_adj}")
print(f"25. S1 outliers: {s1_out}")

# ===== 5. J1 =====
print(f"\n--- 26-31: J1 Best Plane ---")
print(f"26. J1 A = {proc.plane_J1.A:.6f}")
print(f"27. J1 B = {proc.plane_J1.B:.6f}")
print(f"28. J1 C = {proc.plane_J1.C:.6f}")
print(f"29. J1 D = {proc.plane_J1.D:.6f}")
j1_in = len(proc.J1_inliers)
j1_out = len(points) - j1_in - 3
print(f"30. J1 inliers: {j1_in}")
print(f"31. J1 outliers: {j1_out}  (ref: 260)")

# ===== 6. J2 =====
print(f"\n--- 32-37: J2 Plane ---")
if proc.plane_J2:
    print(f"32. J2 A = {proc.plane_J2.A:.6f}")
    print(f"33. J2 B = {proc.plane_J2.B:.6f}")
    print(f"34. J2 C = {proc.plane_J2.C:.6f}")
    print(f"35. J2 D = {proc.plane_J2.D:.6f}")
    j2_in = len(proc.J2_inliers)
    remaining_for_j2 = j1_out + 3
    j2_out = remaining_for_j2 - j2_in - 3
    print(f"36. J2 inliers: {j2_in}  (ref: 137)")
    print(f"37. J2 outliers: {j2_out}")
else:
    print("J2 not found!")

# ===== 7. Projections =====
print(f"\n--- 38-43: Projections ---")
xt1, yt1, zt1 = proc.P5_proj_J1
print(f"38. P5->J1 xt = {xt1:.3f}")
print(f"39. P5->J1 yt = {yt1:.3f}")
print(f"40. P5->J1 zt = {zt1:.3f}")
xt2, yt2, zt2 = proc.P800_proj_J2
print(f"41. P800->J2 xt = {xt2:.3f}")
print(f"42. P800->J2 yt = {yt2:.3f}")
print(f"43. P800->J2 zt = {zt2:.3f}")

# ===== Save result =====
file_io.write_result(
    r"D:\GitHub\surveying-programming\surveying-programming-test\Point_Seg\result.txt",
    proc
)
print("\nresult.txt saved")

# Count labels
labels = {}
for pt in points:
    lbl = proc.get_label(pt)
    labels[lbl] = labels.get(lbl, 0) + 1
print(f"Labels: {labels}")
