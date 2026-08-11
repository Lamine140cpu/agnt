#!/usr/bin/env python3
"""
Calcule la même pièce en tracé de chemin, pour mesurer l'écart.

Le rendu temps réel du navigateur ne calcule aucun rebond de lumière. Chaque
surface reçoit ce que les sources lui envoient directement, et rien de ce que
les autres surfaces lui renvoient. Or dans une pièce réelle, l'essentiel de la
lumière a rebondi au moins une fois : le sol éclaire le plafond, le mur près du
canapé prend sa couleur, les angles s'assombrissent d'eux-mêmes.

C'est cela qui manque, et aucun réglage de lampe ne le remplace. Ce script
construit la même pièce, avec le même mobilier aux mêmes places et la même
caméra, puis la confie à Cycles — qui, lui, suit les rebonds.

    usage : blender --background --python rendu_reference.py -- [échantillons]
"""
import math
import os
import sys

import bpy

SITE = os.path.dirname(os.path.abspath(__file__))
MOBILIER = os.path.join(SITE, "assets", "mobilier")
SORTIE = os.path.join(SITE, "dist", "reference.png")

ECHANTILLONS = int(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else 128
LARGEUR, HAUTEUR = 900, 600

# les cotes de appartement.html, au centimètre près
L, P, H, EP = 6.4, 4.6, 2.70, 0.18
FEN_L, FEN_H, FEN_Y = 1.55, 1.80, 1.62

# three.js a Y en haut, Blender Z : (x, y, z) devient (x, -z, y)
def vers_blender(x, y, z):
    return (x, -z, y)


def vider():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def matiere(nom, couleur, rugosite=0.9, metal=0.0):
    m = bpy.data.materials.new(nom)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*couleur, 1)
    p.inputs["Roughness"].default_value = rugosite
    p.inputs["Metallic"].default_value = metal
    return m


def boite(nom, centre, taille, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=centre)
    o = bpy.context.object
    o.name = nom
    o.scale = tuple(t / 2 for t in taille)
    o.data.materials.append(mat)
    return o


def main():
    vider()
    scene = bpy.context.scene

    platre = matiere("platre", (0.86, 0.85, 0.83), 0.95)
    bois = matiere("parquet", (0.52, 0.35, 0.20), 0.45)
    blanc = matiere("boiserie", (0.93, 0.92, 0.90), 0.35)

    boite("sol", (0, 0, -0.05), (L, P, 0.1), bois)
    boite("plafond", (0, 0, H + 0.06), (L, P, 0.12), platre)
    boite("mur_avant", (0, P / 2, H / 2), (L, EP, H), platre)
    boite("mur_gauche", (-L / 2, 0, H / 2), (EP, P, H), platre)
    boite("mur_droit", (L / 2, 0, H / 2), (EP, P, H), platre)

    # le mur du fond en morceaux, pour laisser passer les deux baies
    bas, haut = FEN_Y - FEN_H / 2, FEN_Y + FEN_H / 2
    bords = [-L / 2, -1.55 - FEN_L / 2, -1.55 + FEN_L / 2,
             1.55 - FEN_L / 2, 1.55 + FEN_L / 2, L / 2]
    for i in (0, 2, 4):
        a, b = bords[i], bords[i + 1]
        if b - a > 0.01:
            boite(f"fond_{i}", ((a + b) / 2, -P / 2, H / 2), (b - a, EP, H), platre)
    for cx in (-1.55, 1.55):
        boite(f"allege_{cx}", (cx, -P / 2, bas / 2), (FEN_L, EP, bas), platre)
        boite(f"linteau_{cx}", (cx, -P / 2, (haut + H) / 2), (FEN_L, EP, H - haut), platre)

    # le mobilier, aux positions de la page
    MEUBLES = [
        ("sofa_03", -2.45, 0, 0.10, math.pi / 2),
        ("modern_coffee_table_01", -1.10, 0, 0.10, 0),
        ("mid_century_lounge_chair", 0.55, 0, 1.05, -2.35),
        ("side_table_01", 1.55, 0, 0.75, 0.3),
        ("Shelf_01", 2.95, 0, -1.15, -math.pi / 2),
        ("potted_plant_01", 2.55, 0, 1.65, 0.8),
        ("potted_plant_04", -1.10, 0.39, 0.10, 1.9),
        ("ceramic_vase_01", 1.55, 0.55, 0.75, 0.5),
        ("modern_ceiling_lamp_01", -1.10, H - 1.17, 0.10, 0),
    ]
    for nom, x, y, z, ry in MEUBLES:
        chemin = os.path.join(MOBILIER, nom, f"{nom}.gltf")
        if not os.path.exists(chemin):
            print(f"  absent : {nom}")
            continue
        avant = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=chemin)
        for o in set(bpy.data.objects) - avant:
            if o.parent is None:
                o.location = vers_blender(x, y, z)
                o.rotation_euler = (0, 0, ry)

    # Le ciel : une lumière d'ambiance sur toute la voûte, plus le soleil.
    monde = bpy.data.worlds.new("ciel")
    monde.use_nodes = True
    monde.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.72, 0.90, 1)
    monde.node_tree.nodes["Background"].inputs[1].default_value = 1.3
    scene.world = monde

    bpy.ops.object.light_add(type="SUN", location=(-3, -7, 5))
    soleil = bpy.context.object
    soleil.data.energy = 2.4
    soleil.data.angle = math.radians(1.5)
    soleil.rotation_euler = (math.radians(58), 0, math.radians(-28))

    # deux surfaces lumineuses devant les baies : c'est le ciel qui entre
    for cx in (-1.55, 1.55):
        bpy.ops.object.light_add(type="AREA", location=(cx, -P / 2 - 0.25, FEN_Y))
        a = bpy.context.object
        a.data.shape = "RECTANGLE"
        a.data.size, a.data.size_y = FEN_L, FEN_H
        a.data.energy = 190
        a.rotation_euler = (math.radians(-90), 0, 0)

    # la caméra de la page : cible (-0,40 / 1,10 / -0,20), azimut 2,30, rayon 2,60
    az, ht, r = 2.55, 0.10, 1.75
    cx, cy, cz = -1.35, 0.62, 0.15
    oeil = (cx + math.sin(az) * math.cos(ht) * r,
            cy + math.sin(ht) * r,
            cz + math.cos(az) * math.cos(ht) * r)
    bpy.ops.object.camera_add(location=vers_blender(*oeil))
    cam = bpy.context.object
    cam.data.sensor_fit = "VERTICAL"
    cam.data.angle_y = math.radians(34)
    vise = bpy.data.objects.new("vise", None)
    bpy.context.collection.objects.link(vise)
    vise.location = vers_blender(cx, cy, cz)
    c = cam.constraints.new("TRACK_TO")
    c.target = vise
    c.track_axis, c.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object = vise
    cam.data.dof.aperture_fstop = 2.8
    scene.camera = cam

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = ECHANTILLONS
    # Ce Blender-là est compilé sans débruiteur : on compense par un nombre
    # d'échantillons plus élevé, faute de mieux.
    scene.cycles.use_denoising = False
    scene.cycles.max_bounces = 6
    scene.render.resolution_x, scene.render.resolution_y = LARGEUR, HAUTEUR
    scene.render.film_transparent = False
    # Filmic délave tout : il est fait pour être étalonné après coup, ce qu'on
    # ne fera pas ici.
    scene.view_settings.view_transform = "Filmic"
    scene.view_settings.exposure = 0.6
    scene.render.filepath = SORTIE

    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    bpy.ops.render.render(write_still=True)
    print(f"écrit {SORTIE}")


main()
