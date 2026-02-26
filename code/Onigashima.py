import bpy
import math



def nettoyer_scene():
    """
    Supprime tous les objets de la scène.

    Méthode:
        Sélectionne tous les objets puis exécute l'opération de suppression de Blender.
    """
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def configurer_rendu_eevee():
    """
    Passe la scène sur Eevee et active quelques effets (GTAO, bloom, raytracing si disponibles).

    Méthode:
        Modifie les propriétés de contexte de la scène et tente d'ajuster la couleur du Background via les nodes.
    """
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'

    if hasattr(bpy.context.scene.eevee, 'use_gtao'):
        bpy.context.scene.eevee.use_gtao = True
    if hasattr(bpy.context.scene.eevee, 'use_bloom'):
        bpy.context.scene.eevee.use_bloom = True
        bpy.context.scene.eevee.bloom_intensity = 0.05
    if hasattr(bpy.context.scene.eevee, 'use_raytracing'):
        bpy.context.scene.eevee.use_raytracing = True

    try:
        bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (0.005, 0.002, 0.01, 1)
    except:
        pass


def creer_materiau_roche_hostile():
    """
    Construit un matériau nodal simulant une roche sombre et rugueuse.

    Returns:
        mat (bpy.types.Material): matériau prêt à l'emploi.

    Méthode:
        Crée un material node-based, ajoute noise + bump et branche sur le Principled BSDF.
    """
    mat = bpy.data.materials.new(name="Mat_Roche_Hostile")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")

    bsdf.inputs["Base Color"].default_value = (0.08, 0.07, 0.09, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.95

    tex_coord = nodes.new(type='ShaderNodeTexCoord')
    mapping = nodes.new(type='ShaderNodeMapping')
    noise_tex = nodes.new(type='ShaderNodeTexNoise')
    bump = nodes.new(type='ShaderNodeBump')

    noise_tex.inputs['Scale'].default_value = 15.0
    noise_tex.inputs['Detail'].default_value = 15.0
    noise_tex.inputs['Roughness'].default_value = 0.7

    bump.inputs['Strength'].default_value = 0.4
    bump.inputs['Distance'].default_value = 0.1

    links.new(tex_coord.outputs['Object'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], noise_tex.inputs['Vector'])
    links.new(noise_tex.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

    return mat


def creer_materiau_lumiere(puissance):
    """
    Crée un matériau émissif de couleur chaude.

    Args:
        puissance: intensité d'émission.

    Returns:
        mat (bpy.types.Material)

    Méthode:
        Reconstruit le node tree et branche un NodeEmission sur la sortie material.
    """
    mat = bpy.data.materials.new(name="Mat_Feu_Interne")
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    emission = mat.node_tree.nodes.new(type='ShaderNodeEmission')
    emission.inputs['Color'].default_value = (1.0, 0.15, 0.02, 1.0)
    emission.inputs['Strength'].default_value = puissance
    sortie = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    mat.node_tree.links.new(emission.outputs['Emission'], sortie.inputs['Surface'])
    return mat


def appliquer_booleen(cible, outil, operation='DIFFERENCE'):
    """
    Applique un boolean entre 'cible' et 'outil' puis supprime l'outil.

    Args:
        cible: objet cible.
        outil: objet opérateur.
        operation: type d'opération boolean.

    Méthode:
        Applique la transformation de rotation/scale sur l'outil, crée le modifier Boolean sur la cible,
        l'applique, puis supprime l'outil.
    """
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = outil
    outil.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    bpy.ops.object.select_all(action='DESELECT')
    mod = cible.modifiers.new(name="DecoupeBool", type='BOOLEAN')
    mod.operation = operation
    mod.solver = 'FLOAT'
    mod.object = outil

    cible.select_set(True)
    bpy.context.view_layer.objects.active = cible
    bpy.context.view_layer.update()

    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(outil, do_unlink=True)


def ajouter_bruit_initial(objet, force, taille):
    """
    Ajoute un modificateur Displace basé sur une texture Clouds et l'applique.

    Args:
        objet: cible du displacement.
        force: force (strength) du displacement.
        taille: noise_scale de la texture.


    Méthode:
        Crée une texture Clouds, attache un mod Displace puis l'applique immédiatement.
    """
    tex = bpy.data.textures.new(f"BruitInit_{objet.name}", type='CLOUDS')
    tex.noise_scale = taille
    mod = objet.modifiers.new(name="DeformationInit", type='DISPLACE')
    mod.texture = tex
    mod.strength = force
    mod.mid_level = 0.5
    bpy.context.view_layer.objects.active = objet
    bpy.ops.object.modifier_apply(modifier=mod.name)


def appliquer_bruit_final_agressif(objet, force_finale, echelle_finale, niveau_subdivision=2):
    """
    Applique subsurf puis displacement final avec texture Clouds.

    Args:
        objet: cible.
        force_finale: intensity du displacement final.
        echelle_finale: noise_scale du bruit final.
        niveau_subdivision: niveaux de subdivision.

    Returns:
        None

    Méthode:
        Ajoute Subsurf + Displace, configure les textures puis applique les deux modifiers.
    """
    bpy.ops.object.select_all(action='DESELECT')
    objet.select_set(True)
    bpy.context.view_layer.objects.active = objet

    mod_sub = objet.modifiers.new(name="SubdivisionFinale", type='SUBSURF')
    mod_sub.levels = niveau_subdivision
    mod_sub.render_levels = niveau_subdivision

    tex = bpy.data.textures.new(f"BruitFinal_{objet.name}", type='CLOUDS')
    tex.noise_scale = echelle_finale
    tex.noise_depth = 4

    mod_disp = objet.modifiers.new(name="DeformationFinale", type='DISPLACE')
    mod_disp.texture = tex
    mod_disp.strength = force_finale
    mod_disp.mid_level = 0.5

    bpy.ops.object.modifier_apply(modifier=mod_sub.name)
    bpy.ops.object.modifier_apply(modifier=mod_disp.name)


# ------------------------------------------------------------------
# CRÉATION DU CRÂNE
# ------------------------------------------------------------------
def creer_crane_final_onigashima(
    location=(0, 0, 8.0),
    rayon_base = 13.0,
    echelle_crane = (1.45, 1.05, 1.15),
    force_roche_initiale = 0.4,

    force_roche_finale = 0.35,
    echelle_roche_finale = 1.5,

    rayon_oeil = 4.8,
    ecart_yeux_x = 5.5,
    hauteur_yeux_z = 12.5,
    profondeur_yeux_y = -11.0,
    inclinaison_yeux = 24.0,

    taille_nez_base = 4.2,
    hauteur_nez_z = 8.0,
    profondeur_nez_y = -13.0,
    angle_nez = 100.0,

    largeur_bouche_x = 9.5,
    hauteur_arche_z = 3.5,
    profondeur_bouche_y = -9.0,

    taille_creusage_interne = 11.0,
    position_creusage_y = 3.5,

    puissance_lumiere = 120.0
):
    """
    Construit le crâne complet avec découpes (yeux, nez, bouche, cavité) et lumières internes.

    Args:
        Paramètres de géométrie et d'éclairage (voir signatures).

    Returns:
        crane (bpy.types.Object)

    Méthode:
        Crée une sphère dense, applique matériaux, effectue des booleans avec des primitives outils,
        applique bruit initial et final, puis ajoute des objets lumineux parentés au crâne.
    """
    configurer_rendu_eevee()
    mat_roche = creer_materiau_roche_hostile()
    mat_feu = creer_materiau_lumiere(puissance_lumiere)

    # bloc crâne
    bpy.ops.mesh.primitive_uv_sphere_add(radius=rayon_base, location=location, segments=160, ring_count=80)
    crane = bpy.context.active_object
    crane.name = "Crâne_Final_Hostile"
    crane.scale = echelle_crane
    bpy.ops.object.transform_apply(scale=True)
    crane.data.materials.append(mat_roche)
    bpy.ops.object.shade_smooth()
    ajouter_bruit_initial(crane, force_roche_initiale, taille=6.0)

    # outils: yeux, nez, bouche, cavité
    bpy.ops.mesh.primitive_uv_sphere_add(radius=rayon_oeil, location=(ecart_yeux_x, profondeur_yeux_y, hauteur_yeux_z))
    oeil_G = bpy.context.active_object
    oeil_G.scale = (1.0, 1.5, 0.7)
    oeil_G.rotation_euler = (0, math.radians(inclinaison_yeux), 0)

    bpy.ops.mesh.primitive_uv_sphere_add(radius=rayon_oeil, location=(-ecart_yeux_x, profondeur_yeux_y, hauteur_yeux_z))
    oeil_D = bpy.context.active_object
    oeil_D.scale = (1.0, 1.5, 0.7)
    oeil_D.rotation_euler = (0, math.radians(-inclinaison_yeux), 0)

    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=taille_nez_base, radius2=0.0, depth=9.0, location=(0, profondeur_nez_y, hauteur_nez_z))
    nez = bpy.context.active_object
    nez.rotation_euler = (math.radians(angle_nez), 0, math.radians(180))

    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=1.0, depth=30.0, location=(0, profondeur_bouche_y, 0.0))
    bouche = bpy.context.active_object
    bouche.rotation_euler = (math.radians(90), 0, 0)
    bouche.scale = (largeur_bouche_x, hauteur_arche_z, 1.0)

    bpy.ops.mesh.primitive_uv_sphere_add(radius=taille_creusage_interne, location=(0, position_creusage_y, 8.0))
    outil_creusage = bpy.context.active_object
    outil_creusage.scale = (1.1, 0.7, 1.2)

    # exécution des découpes
    appliquer_booleen(crane, oeil_G)
    appliquer_booleen(crane, oeil_D)
    appliquer_booleen(crane, nez)
    appliquer_booleen(crane, bouche)
    appliquer_booleen(crane, outil_creusage)

    # bruit final
    appliquer_bruit_final_agressif(crane, force_finale=force_roche_finale, echelle_finale=echelle_roche_finale, niveau_subdivision=2)

    # lumières internes
    offset_fond_oeil_y = 1.0
    bpy.ops.mesh.primitive_uv_sphere_add(radius=rayon_oeil*0.6, location=(ecart_yeux_x, profondeur_yeux_y + offset_fond_oeil_y, hauteur_yeux_z))
    lum_G = bpy.context.active_object
    lum_G.scale = (1.0, 0.2, 0.7)
    lum_G.rotation_euler = (0, math.radians(inclinaison_yeux), 0)
    lum_G.data.materials.append(mat_feu)

    bpy.ops.mesh.primitive_uv_sphere_add(radius=rayon_oeil*0.6, location=(-ecart_yeux_x, profondeur_yeux_y + offset_fond_oeil_y, hauteur_yeux_z))
    lum_D = bpy.context.active_object
    lum_D.scale = (1.0, 0.2, 0.7)
    lum_D.rotation_euler = (0, math.radians(-inclinaison_yeux), 0)
    lum_D.data.materials.append(mat_feu)

    bpy.ops.object.light_add(type='POINT', radius=10.0, location=(0, 5.0, 5.0))
    grosse_lumiere = bpy.context.active_object
    grosse_lumiere.data.energy = puissance_lumiere * 200
    grosse_lumiere.data.color = (1.0, 0.05, 0.01)

    # parentage lumières
    lum_G.parent = crane
    lum_G.matrix_parent_inverse = crane.matrix_world.inverted()
    lum_D.parent = crane
    lum_D.matrix_parent_inverse = crane.matrix_world.inverted()
    grosse_lumiere.parent = crane
    grosse_lumiere.matrix_parent_inverse = crane.matrix_world.inverted()

    return crane


# ------------------------------------------------------------------
# CORNES ADAPTATIVES
# ------------------------------------------------------------------

def ajouter_cornes_adaptatives(
    objet_cible,
    taille_relative = 0.95,
    epaisseur_relative = 0.15,
    finesse_pointe = 0.005,
    angle_courbure = -135.0,
    pos_rel_x = 0.42,
    pos_rel_y = -0.05,
    pos_rel_z = 0.20,
    rotation_deg = (0.0, 65.0, -10.0),
    nom_materiau = "Mat_Roche_Hostile"
):
    """
    Génère et attache des cornes coniques, symétrisées et parentées à l'objet cible.

    Args:
        Voir la signature pour les paramètres de proportion, position et rotation.

    Returns:
        corne (bpy.types.Object) ou None si objet_cible est absent.

    Méthode:
        Crée un cône, ajoute Subsurf + Bend, place et miroir pour obtenir la paire, puis parent.
    """
    if not objet_cible:
        print("ERREUR : L'objet cible est manquant.")
        return None

    largeur_ref = objet_cible.dimensions.x
    longueur_corne = largeur_ref * taille_relative
    rayon_base = largeur_ref * epaisseur_relative
    rayon_pointe = largeur_ref * finesse_pointe

    bpy.ops.mesh.primitive_cone_add(
        vertices=128,
        radius1=rayon_base,
        radius2=rayon_pointe,
        depth=longueur_corne,
        location=(0, 0, longueur_corne / 2)
    )
    corne = bpy.context.active_object
    corne.name = "Corne_Onigashima"

    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

    mod_sub = corne.modifiers.new(name="Subdivision", type='SUBSURF')
    mod_sub.levels = 3
    mod_sub.render_levels = 3

    mod_bend = corne.modifiers.new(name="Courbure", type='SIMPLE_DEFORM')
    mod_bend.deform_method = 'BEND'
    mod_bend.angle = math.radians(angle_courbure)
    mod_bend.deform_axis = 'Y'

    loc_x = objet_cible.location.x + (objet_cible.dimensions.x * pos_rel_x)
    loc_y = objet_cible.location.y + (objet_cible.dimensions.y * pos_rel_y)
    loc_z = objet_cible.location.z + (objet_cible.dimensions.z * pos_rel_z)
    corne.location = (loc_x, loc_y, loc_z)

    rot_rad = [math.radians(a) for a in rotation_deg]
    corne.rotation_euler = rot_rad

    mod_mirror = corne.modifiers.new(name="Symetrie", type='MIRROR')
    mod_mirror.use_axis[0] = True
    mod_mirror.mirror_object = objet_cible

    corne.parent = objet_cible
    corne.matrix_parent_inverse = objet_cible.matrix_world.inverted()

    bpy.ops.object.shade_smooth()
    mat = bpy.data.materials.get(nom_materiau)
    if mat:
        corne.data.materials.append(mat)

    return corne


# ------------------------------------------------------------------
# FONCTION D'ASSEMBLAGE
# ------------------------------------------------------------------
def construire(
    ile_base,
    ratio_taille = 0.65,
    enfoncement_z = 0.0,
    decalage_y = 0.0
):
    """
    Orquestre la génération complète et positionne le crâne sur l'île donnée.

    Args:
        ile_base: objet représentant l'île.
        ratio_taille: portion de la largeur de l'île pour la taille du crâne.
        enfoncement_z: profondeur d'enfoncement.
        decalage_y: décalage sur l'axe Y.

    Returns:
        None

    Méthode:
        Appelle creer_crane_final_onigashima(), ajoute les cornes, met à l'échelle selon l'île
        et parent le crâne à l'île si fournie.
    """
    print(f"--- DÉBUT DE LA CONSTRUCTION SUR L'ÎLE : {ile_base.name if ile_base else 'Aucune'} ---")

    crane = creer_crane_final_onigashima()
    if not crane:
        print("Erreur lors de la génération du crâne.")
        return None

    ajouter_cornes_adaptatives(objet_cible=crane)

    if ile_base:
        largeur_voulue = ile_base.dimensions.x * ratio_taille
        facteur_echelle = largeur_voulue / crane.dimensions.x
        crane.scale = (
            crane.scale.x * facteur_echelle,
            crane.scale.y * facteur_echelle,
            crane.scale.z * facteur_echelle
        )
        bpy.context.view_layer.update()
        crane.location = (
            ile_base.location.x,
            ile_base.location.y + decalage_y,
            ile_base.location.z - enfoncement_z
        )
        crane.parent = ile_base
        crane.matrix_parent_inverse = ile_base.matrix_world.inverted()
        print(f"Assemblage terminé ! Crâne placé en {crane.location}")
    else:
        print("Aucune île fournie, le crâne reste au centre de la scène.")


# ------------------------------------------------------------------
# EXECUTION DIRECTE
# ------------------------------------------------------------------
if __name__ == "__main__":
    ile = creer_crane_final_onigashima()
    if ile:
        ajouter_cornes_adaptatives(objet_cible=ile)
    else:
        print("Cible introuvable.")
