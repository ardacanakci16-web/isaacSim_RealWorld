#!/usr/bin/env python3
"""
3D İnsansız Hava Aracı (İHA) Model Oluşturucu
- Sabit Kanat İHA (Tactical Fixed-Wing UAV - Bayraktar TB2 / Predator stili)
- Döner Kanat Quadcopter İHA (Multirotor Drone)

Bu betik .obj ve .mtl dosyalarını saf Python ve NumPy ile üretir.
"""

import math
import numpy as np
import os

class ObjBuilder:
    def __init__(self, mtl_filename="materials.mtl"):
        self.vertices = []      # (x, y, z)
        self.normals = []       # (nx, ny, nz)
        self.texcoords = []     # (u, v)
        self.objects = []       # (obj_name, mat_name, [faces])
        self.current_obj = "Default"
        self.current_mat = None
        self.current_faces = []
        self.mtl_filename = mtl_filename

    def set_object(self, obj_name, mat_name=None):
        if self.current_faces:
            self.objects.append((self.current_obj, self.current_mat, self.current_faces))
            self.current_faces = []
        self.current_obj = obj_name
        if mat_name:
            self.current_mat = mat_name

    def set_material(self, mat_name):
        if self.current_faces:
            self.objects.append((self.current_obj, self.current_mat, self.current_faces))
            self.current_faces = []
        self.current_mat = mat_name

    def add_vertex(self, v):
        self.vertices.append(v)
        return len(self.vertices)  # 1-based index in OBJ

    def add_normal(self, n):
        norm = math.sqrt(n[0]*n[0] + n[1]*n[1] + n[2]*n[2])
        if norm > 1e-6:
            n = (n[0]/norm, n[1]/norm, n[2]/norm)
        else:
            n = (0.0, 1.0, 0.0)
        self.normals.append(n)
        return len(self.normals)

    def add_face(self, v_idx_list, vn_idx_list=None):
        """v_idx_list and vn_idx_list are lists of 1-based indices"""
        if vn_idx_list is None:
            vn_idx_list = [None] * len(v_idx_list)
        self.current_faces.append(list(zip(v_idx_list, vn_idx_list)))

    def add_box(self, center, size, flat_normals=True):
        """center=(x,y,z), size=(dx,dy,dz)"""
        cx, cy, cz = center
        dx, dy, dz = size[0]/2, size[1]/2, size[2]/2

        # 8 corners
        corners = [
            (cx - dx, cy - dy, cz - dz), # 0: ---
            (cx + dx, cy - dy, cz - dz), # 1: +--
            (cx + dx, cy + dy, cz - dz), # 2: ++-
            (cx - dx, cy + dy, cz - dz), # 3: -+-
            (cx - dx, cy - dy, cz + dz), # 4: --+
            (cx + dx, cy - dy, cz + dz), # 5: +-+
            (cx + dx, cy + dy, cz + dz), # 6: +++
            (cx - dx, cy + dy, cz + dz), # 7: -++
        ]

        faces_def = [
            # face corners, normal
            ([4, 5, 6, 7], (0, 0, 1)),   # Front (+Z)
            ([1, 0, 3, 2], (0, 0, -1)),  # Back (-Z)
            ([3, 2, 6, 7], (0, 1, 0)),   # Top (+Y)
            ([0, 1, 5, 4], (0, -1, 0)),  # Bottom (-Y)
            ([5, 1, 2, 6], (1, 0, 0)),   # Right (+X)
            ([0, 4, 7, 3], (-1, 0, 0)),  # Left (-X)
        ]

        for corner_indices, n in faces_def:
            n_idx = self.add_normal(n)
            v_indices = [self.add_vertex(corners[i]) for i in corner_indices]
            self.add_face(v_indices, [n_idx]*len(v_indices))

    def add_cylinder(self, p1, p2, r1, r2=None, segments=16, caps=True):
        """Cylinder or cone between p1 and p2 with radius r1 at p1 and r2 at p2"""
        if r2 is None:
            r2 = r1
        p1 = np.array(p1, dtype=float)
        p2 = np.array(p2, dtype=float)
        axis = p2 - p1
        length = np.linalg.norm(axis)
        if length < 1e-6:
            return
        z_dir = axis / length

        # Robust orthogonal vector
        if abs(z_dir[0]) < 0.8 and abs(z_dir[1]) < 0.8:
            ref = np.array([1, 0, 0], dtype=float)
        else:
            ref = np.array([0, 0, 1], dtype=float)
        x_dir = np.cross(ref, z_dir)
        norm_x = np.linalg.norm(x_dir)
        if norm_x < 1e-6:
            ref = np.array([0, 1, 0], dtype=float)
            x_dir = np.cross(ref, z_dir)
            norm_x = np.linalg.norm(x_dir)
        x_dir /= norm_x
        y_dir = np.cross(z_dir, x_dir)
        y_dir /= np.linalg.norm(y_dir)

        ring1_v = []
        ring2_v = []
        ring_n = []

        for i in range(segments):
            angle = 2 * math.pi * i / segments
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            rad_dir = cos_a * x_dir + sin_a * y_dir

            v1 = p1 + r1 * rad_dir
            v2 = p2 + r2 * rad_dir

            ring1_v.append(self.add_vertex(tuple(v1)))
            ring2_v.append(self.add_vertex(tuple(v2)))

            # Normal vector along side
            n_side = rad_dir
            ring_n.append(self.add_normal(tuple(n_side)))

        # Side quad faces
        for i in range(segments):
            i_next = (i + 1) % segments
            v_face = [ring1_v[i], ring1_v[i_next], ring2_v[i_next], ring2_v[i]]
            n_face = [ring_n[i], ring_n[i_next], ring_n[i_next], ring_n[i]]
            self.add_face(v_face, n_face)

        # Caps
        if caps:
            if r1 > 1e-4:
                c1_idx = self.add_vertex(tuple(p1))
                n1_idx = self.add_normal(tuple(-z_dir))
                for i in range(segments):
                    i_next = (i + 1) % segments
                    self.add_face([c1_idx, ring1_v[i_next], ring1_v[i]], [n1_idx, n1_idx, n1_idx])
            if r2 > 1e-4:
                c2_idx = self.add_vertex(tuple(p2))
                n2_idx = self.add_normal(tuple(z_dir))
                for i in range(segments):
                    i_next = (i + 1) % segments
                    self.add_face([c2_idx, ring2_v[i], ring2_v[i_next]], [n2_idx, n2_idx, n2_idx])

    def add_sphere(self, center, radius, lat_segments=12, lon_segments=16):
        cx, cy, cz = center
        rings_v = []
        rings_n = []

        for i in range(lat_segments + 1):
            theta = math.pi * i / lat_segments # 0 to pi
            sin_t = math.sin(theta)
            cos_t = math.cos(theta)
            cur_ring_v = []
            cur_ring_n = []
            for j in range(lon_segments):
                phi = 2 * math.pi * j / lon_segments
                x = sin_t * math.cos(phi)
                y = cos_t
                z = sin_t * math.sin(phi)

                vx = cx + radius * x
                vy = cy + radius * y
                vz = cz + radius * z

                cur_ring_v.append(self.add_vertex((vx, vy, vz)))
                cur_ring_n.append(self.add_normal((x, y, z)))
            rings_v.append(cur_ring_v)
            rings_n.append(cur_ring_n)

        for i in range(lat_segments):
            for j in range(lon_segments):
                j_next = (j + 1) % lon_segments
                v1 = rings_v[i][j]
                v2 = rings_v[i][j_next]
                v3 = rings_v[i+1][j_next]
                v4 = rings_v[i+1][j]

                n1 = rings_n[i][j]
                n2 = rings_n[i][j_next]
                n3 = rings_n[i+1][j_next]
                n4 = rings_n[i+1][j]

                if i == 0:
                    self.add_face([v1, v3, v4], [n1, n3, n4])
                elif i == lat_segments - 1:
                    self.add_face([v1, v2, v3], [n1, n2, n3])
                else:
                    self.add_face([v1, v2, v3, v4], [n1, n2, n3, n4])

    def add_torus(self, center, r_major, r_minor, seg_major=16, seg_minor=8, axis='y'):
        """Torus / Wheel tire"""
        cx, cy, cz = center
        grid_v = []
        grid_n = []

        for i in range(seg_major):
            theta = 2 * math.pi * i / seg_major
            cos_t = math.cos(theta)
            sin_t = math.sin(theta)
            ring_v = []
            ring_n = []
            for j in range(seg_minor):
                phi = 2 * math.pi * j / seg_minor
                cos_p = math.cos(phi)
                sin_p = math.sin(phi)

                rad = r_major + r_minor * cos_p
                if axis == 'x': # Wheel axis along X
                    vx = cx + r_minor * sin_p
                    vy = cy + rad * cos_t
                    vz = cz + rad * sin_t
                    nx = sin_p
                    ny = cos_p * cos_t
                    nz = cos_p * sin_t
                elif axis == 'y':
                    vx = cx + rad * cos_t
                    vy = cy + r_minor * sin_p
                    vz = cz + rad * sin_t
                    nx = cos_p * cos_t
                    ny = sin_p
                    nz = cos_p * sin_t
                else: # z
                    vx = cx + rad * cos_t
                    vy = cy + rad * sin_t
                    vz = cz + r_minor * sin_p
                    nx = cos_p * cos_t
                    ny = cos_p * sin_t
                    nz = sin_p

                ring_v.append(self.add_vertex((vx, vy, vz)))
                ring_n.append(self.add_normal((nx, ny, nz)))
            grid_v.append(ring_v)
            grid_n.append(ring_n)

        for i in range(seg_major):
            i_next = (i + 1) % seg_major
            for j in range(seg_minor):
                j_next = (j + 1) % seg_minor
                self.add_face(
                    [grid_v[i][j], grid_v[i_next][j], grid_v[i_next][j_next], grid_v[i][j_next]],
                    [grid_n[i][j], grid_n[i_next][j], grid_n[i_next][j_next], grid_n[i][j_next]]
                )

    def add_lofted_surface(self, sections, close_caps=True):
        """
        sections: list of lists of 3D points forming closed loops.
        Each section has the same number of vertices.
        """
        n_sec = len(sections)
        n_pts = len(sections[0])
        grid_v = []

        for sec in sections:
            row_v = [self.add_vertex(p) for p in sec]
            grid_v.append(row_v)

        for i in range(n_sec - 1):
            for j in range(n_pts):
                j_next = (j + 1) % n_pts
                v1 = grid_v[i][j]
                v2 = grid_v[i][j_next]
                v3 = grid_v[i+1][j_next]
                v4 = grid_v[i+1][j]

                # Compute approximate flat normal
                p1 = np.array(self.vertices[v1-1])
                p2 = np.array(self.vertices[v2-1])
                p4 = np.array(self.vertices[v4-1])
                n = np.cross(p2 - p1, p4 - p1)
                n_norm = np.linalg.norm(n)
                if n_norm > 1e-6:
                    n /= n_norm
                else:
                    n = [0, 1, 0]
                n_idx = self.add_normal(tuple(n))

                self.add_face([v1, v2, v3, v4], [n_idx, n_idx, n_idx, n_idx])

        if close_caps:
            # First cap (inverted winding)
            first_pts = grid_v[0]
            # Center of first cap
            c1 = np.mean([self.vertices[v-1] for v in first_pts], axis=0)
            c1_idx = self.add_vertex(tuple(c1))
            n1 = np.cross(np.array(self.vertices[first_pts[0]-1]) - c1, np.array(self.vertices[first_pts[1]-1]) - c1)
            if np.linalg.norm(n1) > 1e-6: n1 /= np.linalg.norm(n1)
            n1_idx = self.add_normal(tuple(-n1))
            for j in range(n_pts):
                j_next = (j + 1) % n_pts
                self.add_face([c1_idx, first_pts[j_next], first_pts[j]], [n1_idx, n1_idx, n1_idx])

            # End cap
            last_pts = grid_v[-1]
            c2 = np.mean([self.vertices[v-1] for v in last_pts], axis=0)
            c2_idx = self.add_vertex(tuple(c2))
            n2 = np.cross(np.array(self.vertices[last_pts[0]-1]) - c2, np.array(self.vertices[last_pts[1]-1]) - c2)
            if np.linalg.norm(n2) > 1e-6: n2 /= np.linalg.norm(n2)
            n2_idx = self.add_normal(tuple(n2))
            for j in range(n_pts):
                j_next = (j + 1) % n_pts
                self.add_face([c2_idx, last_pts[j], last_pts[j_next]], [n2_idx, n2_idx, n2_idx])

    def export_obj(self, filepath):
        if self.current_faces:
            self.objects.append((self.current_obj, self.current_mat, self.current_faces))
            self.current_faces = []

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# Wavefront OBJ File - Generated by Antigravity UAV Modeler\n")
            f.write(f"mtllib {self.mtl_filename}\n\n")

            f.write(f"# Vertices: {len(self.vertices)}\n")
            for v in self.vertices:
                f.write(f"v {v[0]:.5f} {v[1]:.5f} {v[2]:.5f}\n")

            f.write(f"\n# Normals: {len(self.normals)}\n")
            for n in self.normals:
                f.write(f"vn {n[0]:.5f} {n[1]:.5f} {n[2]:.5f}\n")

            f.write("\n")
            for obj_name, mat_name, faces in self.objects:
                f.write(f"\no {obj_name}\n")
                if mat_name:
                    f.write(f"usemtl {mat_name}\n")
                for face in faces:
                    parts = []
                    for v_idx, vn_idx in face:
                        if vn_idx is not None:
                            parts.append(f"{v_idx}//{vn_idx}")
                        else:
                            parts.append(f"{v_idx}")
                    f.write(f"f {' '.join(parts)}\n")
        print(f"OBJ model kaydedildi: {filepath}")

def generate_naca0012_profile(chord, n_points=16):
    """Generates 2D airfoil points (x_local along chord, y_local thickness) normalized to chord"""
    pts = []
    # Upper surface: from trailing edge to leading edge
    for i in range(n_points):
        beta = math.pi * i / (n_points - 1)
        x = 0.5 * (1.0 - math.cos(beta)) # Cosine clustering at LE
        # NACA 0012 formula (12% thickness)
        yt = 5 * 0.12 * (0.2969 * math.sqrt(x) - 0.1260 * x - 0.3516 * (x**2) + 0.2843 * (x**3) - 0.1015 * (x**4))
        pts.append((x * chord, yt * chord))
    # Lower surface: from leading edge to trailing edge
    for i in range(n_points - 2, 0, -1):
        beta = math.pi * i / (n_points - 1)
        x = 0.5 * (1.0 - math.cos(beta))
        yt = 5 * 0.12 * (0.2969 * math.sqrt(x) - 0.1260 * x - 0.3516 * (x**2) + 0.2843 * (x**3) - 0.1015 * (x**4))
        pts.append((x * chord, -yt * chord))
    return pts

def build_fixed_wing_uav(filepath, mtl_path):
    """
    Sabit Kanat İHA (Bayraktar TB2 / TAI Anka / Predator tarzı taktik İHA)
    Ölçek: 1:1 Metre (Kanat açıklığı ~12m, Gövde boyu ~6.5m)
    Eksenler:
      +Z: Burun (İleri)
      -Z: Kuyruk (Geri)
      +X: Sağ Kanat
      -X: Sol Kanat
      +Y: Yukarı
    """
    obj = ObjBuilder(os.path.basename(mtl_path))

    # ================= 1. GÖVDE (FUSELAGE) =================
    obj.set_object("Govde_Fuselage", "Govde_AskeriGri")
    # Akıcı, aerodinamik gövde kesitleri (Burundan kuyruğa Z ekseni boyunca)
    fuselage_stations = [
        # (z_pos, y_offset, width, height)
        (2.6,   -0.1,  0.08, 0.08),  # 0: Burun ucu (Pitot tüpü arkası)
        (2.3,   -0.08, 0.32, 0.30),  # 1: Burun kubbesi
        (1.8,    0.02, 0.56, 0.52),  # 2: Ön gövde / Aviyonik kubbesi
        (1.0,    0.10, 0.68, 0.62),  # 3: SATCOM kamburu (uydu anteni tümseği)
        (0.0,    0.08, 0.66, 0.60),  # 4: Orta gövde (kanat bağlantısı)
        (-1.0,   0.05, 0.58, 0.54),  # 5: Arka gövde
        (-1.8,   0.02, 0.44, 0.42),  # 6: Motor kaputu önü
        (-2.2,   0.00, 0.36, 0.34),  # 7: Motor kaputu arkası (pervane şaftı)
    ]

    fuselage_sections = []
    n_circ = 16
    for z_pos, y_off, w, h in fuselage_stations:
        sec = []
        for i in range(n_circ):
            ang = 2 * math.pi * i / n_circ
            # Eliptik kesit, üst tarafı biraz daha basık/dolgun
            scale_y = 1.1 if math.sin(ang) > 0 else 0.9
            x = (w / 2.0) * math.cos(ang)
            y = y_off + (h / 2.0) * math.sin(ang) * scale_y
            sec.append((x, y, z_pos))
        fuselage_sections.append(sec)

    obj.add_lofted_surface(fuselage_sections, close_caps=True)

    # Pitot Tüpü (Burun ucundaki hava hızı sensörü)
    obj.set_object("Govde_PitotTupu", "Krom_Metal")
    obj.add_cylinder((0, -0.1, 2.6), (0, -0.1, 3.0), r1=0.015, r2=0.005, segments=8)

    # Motor Hava Emiş Kanalı (Sırt hava alığı / Air Scoop)
    obj.set_object("Govde_HavaEmisi", "Koyu_Panel")
    obj.add_box((0, 0.40, -1.2), (0.28, 0.12, 0.60))

    # ================= 2. KANATLAR (WINGS) =================
    obj.set_object("AnaKanat_SolVeSag", "Govde_AskeriGri")
    # Profil kesitleri: Kanat kökü (Root) ve Kanat ucu (Tip)
    airfoil_pts_root = generate_naca0012_profile(chord=1.2, n_points=14)
    airfoil_pts_tip  = generate_naca0012_profile(chord=0.55, n_points=14)

    # Sağ Kanat (+X)
    # Kanat kökü Z konumu: hücum kenarı Z=0.6, firar kenarı Z=-0.6
    wing_stations_right = []
    # 3 istasyon: Kök (X=0.3), Orta (X=3.0), Uç (X=6.0)
    spans_r = [0.33, 3.2, 5.8]
    chords_r = [1.2, 0.88, 0.55]
    dihedrals_r = [0.08, 0.14, 0.22] # Hafif V-açısı (dihedral)
    sweeps_r = [0.2, 0.0, -0.2]     # Hafif ok açısı geriye

    for x_span, chord, y_dih, z_sw in zip(spans_r, chords_r, dihedrals_r, sweeps_r):
        pts = generate_naca0012_profile(chord=chord, n_points=14)
        sec = []
        for x_c, y_t in pts:
            # Uçak koordinatında: x_c geriye doğru (-Z ekseninde)
            pz = z_sw - (x_c - chord * 0.25)
            py = y_dih + y_t
            px = x_span
            sec.append((px, py, pz))
        wing_stations_right.append(sec)

    obj.add_lofted_surface(wing_stations_right, close_caps=True)

    # Sol Kanat (-X) (Simetrik)
    wing_stations_left = []
    for sec_r in wing_stations_right:
        sec_l = [(-p[0], p[1], p[2]) for p in reversed(sec_r)]
        wing_stations_left.append(sec_l)
    obj.add_lofted_surface(wing_stations_left, close_caps=True)

    # Kanat Ucu Kanatçıkları (Winglets)
    obj.set_object("Kanatcıklar_Winglets", "Koyu_Panel")
    # Sağ winglet
    obj.add_box((5.85, 0.38, -0.25), (0.04, 0.35, 0.45))
    # Sol winglet
    obj.add_box((-5.85, 0.38, -0.25), (0.04, 0.35, 0.45))

    # Mühimmat / Sensör İstasyonları (Under-wing Hardpoints / Pylons)
    obj.set_object("Kanat_Pylonlar", "Koyu_Panel")
    for sign in [-1, 1]:
        # İç istasyon (X = +-1.5m)
        obj.add_box((sign * 1.5, -0.02, 0.1), (0.06, 0.14, 0.55))
        # Dış istasyon (X = +-2.7m)
        obj.add_box((sign * 2.7, 0.03, 0.0), (0.06, 0.14, 0.45))

    # ================= 3. KUYRUK KİRİŞLERİ VE TERS V KUYRUK (TAIL BOOMS & INVERTED V-TAIL) =================
    obj.set_object("Kuyruk_Kirisleri", "Govde_AskeriGri")
    # İki kiriş: sağ (+1.25m) ve sol (-1.25m), kanat kökünden geriye uzanır
    boom_x = 1.25
    boom_start_z = -0.1
    boom_end_z = -3.8
    boom_y = 0.15

    for sign in [-1, 1]:
        # Ana kiriş borusu
        obj.add_cylinder(
            (sign * boom_x, boom_y, boom_start_z),
            (sign * boom_x, boom_y + 0.1, boom_end_z),
            r1=0.065, r2=0.05, segments=12
        )

    # Ters V-Kuyruk (Inverted V-Tail - Bayraktar TB2 karakteristik tasarımı)
    obj.set_object("Kuyruk_V_Stabilizor", "Govde_AskeriGri")
    # Sol fin (Boom'dan aşağı-dışa doğru veya yukarı-içe)
    # TB2'de kuyruk kirişlerinden yukarı veya ters V şeklinde aşağı/yukarı bağlanır.
    # Ters V: Kirişlerin uçlarından yukarı birleşen veya aşağı inen V kanatları.
    # TB2 stili: Kirişlerin uçlarından yukarı doğru birleşip ters V çatısı oluşturur:
    # Sol kiriş (-1.25, 0.25, -3.8) -> Zirve (0.0, 1.35, -4.1) -> Sağ kiriş (1.25, 0.25, -3.8)
    tail_apex = (0.0, 1.45, -4.15)
    tail_left = (-boom_x, boom_y + 0.1, boom_end_z)
    tail_right = (boom_x, boom_y + 0.1, boom_end_z)

    # Sol V-Fin
    obj.add_cylinder(tail_left, tail_apex, r1=0.07, r2=0.05, segments=10)
    # Sağ V-Fin
    obj.add_cylinder(tail_right, tail_apex, r1=0.07, r2=0.05, segments=10)

    # Kanat yüzeyleri (Elevon kanatçıkları levhaları)
    # Sol dümen yüzeyi
    obj.set_object("Kuyruk_Dumenleri", "Koyu_Panel")
    # Kirişlerin altındaki dikey dengeleyici küçük yüzgeçler (Ventral fins)
    for sign in [-1, 1]:
        obj.add_box((sign * boom_x, boom_y - 0.22, boom_end_z - 0.1), (0.03, 0.45, 0.40))

    # ================= 4. İTİCİ PERVANE (PUSHER PROPELLER) =================
    obj.set_object("Pervane_Gobek", "Siyah_Karbon")
    # Gövdenin arkasındaki pervane göbeği (Z = -2.25)
    obj.add_cylinder((0, 0, -2.20), (0, 0, -2.42), r1=0.14, r2=0.07, segments=14)

    # 2 Pervane Palası (Propeller Blades)
    obj.set_object("Pervane_Palalari", "Siyah_Karbon")
    prop_radius = 0.85
    # Dikey pala (+Y ve -Y)
    obj.add_box((0, 0.45, -2.32), (0.09, prop_radius, 0.02))
    obj.add_box((0, -0.45, -2.32), (0.09, prop_radius, 0.02))
    # Yatay pala (+X ve -X - 4 palli pervane efekti)
    obj.add_box((0.45, 0, -2.32), (prop_radius, 0.09, 0.02))
    obj.add_box((-0.45, 0, -2.32), (prop_radius, 0.09, 0.02))

    # Pala Uçlarındaki Sarı Güvenlik Şeritleri
    obj.set_object("Pervane_SariSeritler", "Sari_Isaret")
    obj.add_box((0, 0.82, -2.32), (0.095, 0.10, 0.022))
    obj.add_box((0, -0.82, -2.32), (0.095, 0.10, 0.022))
    obj.add_box((0.82, 0, -2.32), (0.10, 0.095, 0.022))
    obj.add_box((-0.82, 0, -2.32), (0.10, 0.095, 0.022))

    # ================= 5. FLIR / KAMERA GİMBAL SİSTEMİ =================
    obj.set_object("Kamera_Gimbal_Gövde", "Titanyum_Gövde")
    # Gövde altı montaj adaptörü (Z = 1.5, Y = -0.35)
    gimbal_center = (0.0, -0.42, 1.5)
    obj.add_cylinder((0.0, -0.25, 1.5), gimbal_center, r1=0.22, r2=0.19, segments=14)

    # Döner Küre (Electro-optical / Infrared Turret)
    obj.add_sphere(gimbal_center, radius=0.20, lat_segments=12, lon_segments=16)

    # Kamera Optik Lens Yuvaları (FLIR, Gündüz Kamerası, Lazer Mesafe Ölçer)
    obj.set_object("Kamera_Lensler", "Lens_Cami")
    # Ana termal lens (önde)
    lens_pos = (0.0, -0.42, 1.68)
    obj.add_cylinder((0.0, -0.42, 1.60), lens_pos, r1=0.08, r2=0.08, segments=12)
    # İkincil optik lens
    obj.add_cylinder((0.08, -0.48, 1.62), (0.08, -0.48, 1.66), r1=0.035, r2=0.035, segments=10)

    # ================= 6. İNİŞ TAKIMLARI (LANDING GEAR) =================
    obj.set_object("InisTakimi_Dikmeler", "Krom_Metal")
    # Ön İniş Takımı (Nose Gear)
    obj.add_cylinder((0, -0.15, 1.9), (0, -0.85, 1.8), r1=0.03, r2=0.025, segments=10)
    # Ön tekerlek aksı
    obj.add_cylinder((-0.07, -0.85, 1.8), (0.07, -0.85, 1.8), r1=0.015, r2=0.015, segments=8)

    # Ana İniş Takımları (Main Landing Gear: sol ve sağ gövde altı)
    for sign in [-1, 1]:
        # Gövdeden dışa-aşağı açılan yaylı bacak
        obj.add_cylinder((sign * 0.25, -0.15, -0.2), (sign * 0.85, -0.85, -0.3), r1=0.04, r2=0.03, segments=10)
        # Tekerlek aksı
        obj.add_cylinder((sign * 0.78, -0.85, -0.3), (sign * 0.92, -0.85, -0.3), r1=0.015, segments=8)

    # Tekerlek Lastikleri (Tires)
    obj.set_object("InisTakimi_Lastikler", "Kaucuk_Lastik")
    # Ön tekerlek (Y=-0.85, Z=1.8)
    obj.add_torus((0.0, -0.85, 1.8), r_major=0.12, r_minor=0.045, seg_major=14, seg_minor=8, axis='x')
    # Ana tekerlekler
    obj.add_torus((-0.85, -0.85, -0.3), r_major=0.16, r_minor=0.055, seg_major=14, seg_minor=8, axis='x')
    obj.add_torus((0.85, -0.85, -0.3), r_major=0.16, r_minor=0.055, seg_major=14, seg_minor=8, axis='x')

    # Tekerlek Jantları (Rims)
    obj.set_object("InisTakimi_Jantlar", "Krom_Metal")
    obj.add_cylinder((-0.04, -0.85, 1.8), (0.04, -0.85, 1.8), r1=0.08, segments=10)
    obj.add_cylinder((-0.89, -0.85, -0.3), (-0.81, -0.85, -0.3), r1=0.11, segments=10)
    obj.add_cylinder((0.81, -0.85, -0.3), (0.89, -0.85, -0.3), r1=0.11, segments=10)

    # Dışa aktar
    obj.export_obj(filepath)

def build_quadcopter_uav(filepath, mtl_path):
    """
    Döner Kanat Quadcopter İHA (Multirotor Drone)
    Ölçek: 1:1 Metre (Gövde çapı ~550mm - F550 sınıfı drone)
    Eksenler:
      +Z: Ön
      -Z: Arka
      +X: Sağ
      -X: Sol
      +Y: Yukarı
    """
    obj = ObjBuilder(os.path.basename(mtl_path))

    # ================= 1. MERKEZİ GÖVDE (CHASSIS & AVIONICS) =================
    obj.set_object("Govde_AltPlaka", "Siyah_Karbon")
    # Alt Karbon Plaka
    obj.add_cylinder((0, 0.0, 0), (0, 0.005, 0), r1=0.14, segments=16)

    # Üst Karbon Plaka
    obj.set_object("Govde_UstPlaka", "Siyah_Karbon")
    obj.add_cylinder((0, 0.05, 0), (0, 0.055, 0), r1=0.14, segments=16)

    # Gövde İçi Destek Direkleri (Standoffs)
    obj.set_object("Gövde_MetalVidalar", "Krom_Metal")
    for ang_deg in [30, 90, 150, 210, 270, 330]:
        ang = math.radians(ang_deg)
        x = 0.10 * math.cos(ang)
        z = 0.10 * math.sin(ang)
        obj.add_cylinder((x, 0.005, z), (x, 0.05, z), r1=0.005, segments=8)

    # Üst Koruma Kubbesi / Aviyonik Kapağı (Canopy Dome)
    obj.set_object("Govde_Canopy", "Koyu_Panel")
    obj.add_sphere((0, 0.055, 0.01), radius=0.11, lat_segments=10, lon_segments=16)

    # GPS Anten Mantarı (GPS Puck)
    obj.set_object("GPS_Anteni", "Govde_AskeriGri")
    obj.add_cylinder((0, 0.055, -0.06), (0, 0.13, -0.06), r1=0.005, segments=8) # Anten direği
    obj.add_cylinder((0, 0.13, -0.06), (0, 0.145, -0.06), r1=0.035, segments=14) # Anten diski

    # ================= 2. KOLLAR (ARMS) =================
    arm_angles = [45, 135, 225, 315] # X konfigürasyonu
    arm_length = 0.28 # Merkezden motor merkezine mesafe

    obj.set_object("Kollar_KarbonFiber", "Siyah_Karbon")
    for ang_deg in arm_angles:
        ang = math.radians(ang_deg)
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        # Merkezden dışarı uzanan boru kol
        p_start = (0.09 * cos_a, 0.025, 0.09 * sin_a)
        p_end   = (arm_length * cos_a, 0.025, arm_length * sin_a)
        obj.add_cylinder(p_start, p_end, r1=0.012, segments=10)

    # ================= 3. MOTORLAR (BRUSHLESS MOTORS) =================
    obj.set_object("Motorlar_Gövde", "Titanyum_Gövde")
    for ang_deg in arm_angles:
        ang = math.radians(ang_deg)
        mx = arm_length * math.cos(ang)
        mz = arm_length * math.sin(ang)

        # Motor alt yatağı
        obj.add_cylinder((mx, 0.015, mz), (mx, 0.025, mz), r1=0.022, segments=12)
        # Motor gövdesi (Stator / Rotor)
        obj.add_cylinder((mx, 0.025, mz), (mx, 0.055, mz), r1=0.020, segments=14)
        # Pervane kilit somunu
        obj.add_cylinder((mx, 0.055, mz), (mx, 0.070, mz), r1=0.007, segments=10)

    # ================= 4. PERVANELER (PROPELLERS) =================
    # Ön kollar (+Z): 45 (Ön-Sağ) ve 315 (Ön-Sol)
    # Arka kollar (-Z): 135 (Arka-Sağ) ve 225 (Arka-Sol)
    prop_blade_len = 0.13 # 10 inç pervane yarıçapı ~0.13m
    obj.set_object("Pervaneler", "Siyah_Karbon")

    for i, ang_deg in enumerate(arm_angles):
        ang = math.radians(ang_deg)
        mx = arm_length * math.cos(ang)
        mz = arm_length * math.sin(ang)
        py = 0.062

        # Pervaneler farklı açılarda dursun (dinamik görünüm)
        blade_rot = math.radians(ang_deg + (i * 35))
        bx = math.cos(blade_rot)
        bz = math.sin(blade_rot)

        # 2 Pal
        p1_start = (mx, py, mz)
        p1_end   = (mx + prop_blade_len * bx, py, mz + prop_blade_len * bz)
        p2_end   = (mx - prop_blade_len * bx, py, mz - prop_blade_len * bz)

        # Aerodinamik ince kanat formu
        obj.add_box(
            (mx + 0.5 * prop_blade_len * bx, py, mz + 0.5 * prop_blade_len * bz),
            (0.022, 0.004, 0.022)
        )
        obj.add_cylinder(p1_start, p1_end, r1=0.012, r2=0.004, segments=8)
        obj.add_cylinder(p1_start, p2_end, r1=0.012, r2=0.004, segments=8)

    # ================= 5. İNİŞ AYAKLARI (LANDING SKIDS) =================
    obj.set_object("InisAyaklari", "Siyah_Karbon")
    # Sol ve sağ U/kemer şeklinde iniş ayakları
    for sign in [-1, 1]:
        lx = sign * 0.12
        # Ön bacak
        obj.add_cylinder((lx * 0.8, 0.0, 0.08), (lx * 1.2, -0.12, 0.10), r1=0.008, segments=8)
        # Arka bacak
        obj.add_cylinder((lx * 0.8, 0.0, -0.08), (lx * 1.2, -0.12, -0.10), r1=0.008, segments=8)
        # Yere basan kızak borusu
        obj.add_cylinder((lx * 1.2, -0.12, -0.16), (lx * 1.2, -0.12, 0.16), r1=0.009, segments=8)

    # ================= 6. ÖN FPV / GİMBAL KAMERA =================
    obj.set_object("Kamera_FPV", "Titanyum_Gövde")
    cam_pos = (0.0, -0.02, 0.13)
    obj.add_box(cam_pos, (0.04, 0.035, 0.035))

    obj.set_object("Kamera_Lensler", "Lens_Cami")
    obj.add_cylinder((0.0, -0.02, 0.145), (0.0, -0.02, 0.165), r1=0.012, segments=12)

    # Durum LED Işığı (Arkada Yeşil/Kırmızı LED)
    obj.set_object("LED_DurumIsigi", "Sari_Isaret")
    obj.add_cylinder((0.0, 0.03, -0.135), (0.0, 0.03, -0.142), r1=0.008, segments=8)

    obj.export_obj(filepath)

def write_mtl_file(filepath):
    mtl_content = """# Wavefront Material File
# UAV / İHA Kaplama ve Malzeme Tanımları

newmtl Govde_AskeriGri
Ka 0.20 0.22 0.24
Kd 0.48 0.52 0.55
Ks 0.25 0.25 0.25
Ns 35.0
d 1.0
illum 2

newmtl Koyu_Panel
Ka 0.10 0.10 0.12
Kd 0.22 0.24 0.26
Ks 0.35 0.35 0.35
Ns 50.0
d 1.0
illum 2

newmtl Siyah_Karbon
Ka 0.05 0.05 0.05
Kd 0.12 0.12 0.13
Ks 0.40 0.40 0.40
Ns 80.0
d 1.0
illum 2

newmtl Titanyum_Gövde
Ka 0.15 0.16 0.18
Kd 0.35 0.38 0.40
Ks 0.60 0.60 0.62
Ns 100.0
d 1.0
illum 2

newmtl Krom_Metal
Ka 0.25 0.25 0.25
Kd 0.70 0.72 0.75
Ks 0.90 0.90 0.90
Ns 120.0
d 1.0
illum 2

newmtl Lens_Cami
Ka 0.02 0.05 0.08
Kd 0.05 0.15 0.25
Ks 0.95 0.95 1.00
Ns 150.0
d 0.85
illum 2

newmtl Kaucuk_Lastik
Ka 0.05 0.05 0.05
Kd 0.08 0.08 0.09
Ks 0.05 0.05 0.05
Ns 10.0
d 1.0
illum 1

newmtl Sari_Isaret
Ka 0.40 0.35 0.05
Kd 0.95 0.80 0.10
Ks 0.30 0.30 0.20
Ns 40.0
d 1.0
illum 2
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(mtl_content)
    print(f"MTL malzeme dosyası kaydedildi: {filepath}")

if __name__ == "__main__":
    out_dir = "/home/arda/iha_models"
    os.makedirs(out_dir, exist_ok=True)

    mtl_file = os.path.join(out_dir, "iha_materials.mtl")
    write_mtl_file(mtl_file)

    sabit_kanat_file = os.path.join(out_dir, "sabit_kanat_iha.obj")
    build_fixed_wing_uav(sabit_kanat_file, mtl_file)

    quad_file = os.path.join(out_dir, "dortpervane_iha.obj")
    build_quadcopter_uav(quad_file, mtl_file)

    print("\nTüm İHA 3D modelleri başarıyla oluşturuldu!")
