#!/usr/bin/env python3
"""
3D İHA Modellerinin Görsel Önizlemesini Üretir (PNG olarak kaydeder)
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import os

def render_obj_preview(obj_path, out_png, title="3D İHA Modeli", elev=25, azim=-60):
    vertices = []
    faces = []

    with open(obj_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('v '):
                parts = line.strip().split()
                vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif line.startswith('f '):
                parts = line.strip().split()[1:]
                f_indices = []
                for p in parts:
                    idx = int(p.split('/')[0]) - 1
                    f_indices.append(idx)
                if len(f_indices) >= 3:
                    faces.append(f_indices)

    fig = plt.figure(figsize=(10, 7), dpi=150)
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('#1e1e24')
    fig.patch.set_facecolor('#1e1e24')

    # Convert to poly collection with proper visual orientation (OBJ Y is Up, map to Matplotlib Z)
    poly_list = []
    for f in faces:
        pts = [[vertices[idx][0], vertices[idx][2], vertices[idx][1]] for idx in f]
        poly_list.append(pts)

    poly_col = Poly3DCollection(
        poly_list,
        facecolors='#4a7c9b',
        edgecolors='#2c3e50',
        linewidths=0.25,
        alpha=0.92
    )
    ax.add_collection3d(poly_col)

    # Calculate bounds based on transformed vertices
    import numpy as np
    v_arr = np.array([[v[0], v[2], v[1]] for v in vertices])
    min_b = v_arr.min(axis=0)
    max_b = v_arr.max(axis=0)
    mid = (max_b + min_b) / 2.0
    max_range = (max_b - min_b).max() / 2.0

    ax.set_xlim(mid[0] - max_range, mid[0] + max_range)
    ax.set_ylim(mid[1] - max_range, mid[1] + max_range)
    ax.set_zlim(mid[2] - max_range, mid[2] + max_range)

    ax.view_init(elev=elev, azim=azim)

    ax.set_xlabel('X (Sağ / Sol)', color='white', labelpad=10)
    ax.set_ylabel('Z (Burun / Kuyruk)', color='white', labelpad=10)
    ax.set_zlabel('Y (Yükseklik)', color='white', labelpad=10)

    ax.tick_params(colors='gray', labelsize=8)
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.set_title(title, color='white', fontsize=14, weight='bold', pad=15)

    plt.tight_layout()
    plt.savefig(out_png, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close()
    print(f"Görsel önizleme oluşturuldu: {out_png}")

if __name__ == "__main__":
    out_dir = "/home/arda/iha_models"
    render_obj_preview(
        os.path.join(out_dir, "sabit_kanat_iha.obj"),
        os.path.join(out_dir, "sabit_kanat_iha_preview.png"),
        title="Sabit Kanat Taktik İHA (Bayraktar TB2 / Predator Stili)",
        elev=28, azim=-65
    )
    render_obj_preview(
        os.path.join(out_dir, "dortpervane_iha.obj"),
        os.path.join(out_dir, "dortpervane_iha_preview.png"),
        title="Döner Kanat Quadcopter İHA (Drone)",
        elev=32, azim=-55
    )
