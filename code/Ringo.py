import bpy
import random
import math



def creer_tempete_neige(ile_cible, rayon, hauteur_nuage=30.0, nb_flocons=15000):
    """
    Crée un système de particules circulaire simulant une chute de neige.
    
    Args:
        ile_cible (bpy.types.Object): L'objet servant de base pour la position.
        rayon (float): Le rayon du disque émetteur de particules.
        hauteur_nuage (float): L'altitude de l'émetteur par rapport à l'île.
        nb_flocons (int): Nombre total de particules à générer.
    """
    print("Génération de la tempête de neige circulaire...")

    # Calcul de la position du nuage au-dessus de l'île
    location = (ile_cible.location.x, ile_cible.location.y, ile_cible.location.z + hauteur_nuage)

    # --- 1. Création du modèle de flocon ---
    # Création d'une sphère de base placée loin sous la scène pour ne pas être vue
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.15, location=(0, 0, -100))
    flocon = bpy.context.active_object
    flocon.name = "Flocon_Master"
    flocon.visible_shadow = False # Désactivation des ombres pour plus de clarté

    # Création d'un matériau émissif pour que les flocons brillent même dans l'ombre
    mat_neige = bpy.data.materials.new(name="Mat_Flocon_Particule")
    mat_neige.use_nodes = True
    mat_neige.diffuse_color = (1.0, 1.0, 1.0, 1.0)

    nodes = mat_neige.node_tree.nodes
    links = mat_neige.node_tree.links
    for n in nodes: nodes.remove(n) # Nettoyage des noeuds par défaut

    sortie = nodes.new(type='ShaderNodeOutputMaterial')
    emission = nodes.new(type='ShaderNodeEmission')
    emission.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    emission.inputs['Strength'].default_value = 3.0 # Intensité de la brillance
    links.new(emission.outputs['Emission'], sortie.inputs['Surface'])

    flocon.data.materials.append(mat_neige)
    flocon.hide_render = True # On cache l'objet original au rendu final

    # --- 2. Création de l'émetteur (le nuage invisible) ---
    # Utilisation d'un cercle pour limiter la chute à la forme de l'île
    bpy.ops.mesh.primitive_circle_add(vertices=64, radius=rayon, fill_type='NGON', location=location)
    nuage = bpy.context.active_object
    nuage.name = "Nuage_Emetteur"

    # Création d'un matériau transparent pour l'émetteur
    mat_invis = bpy.data.materials.new(name="Mat_Nuage_Invisible")
    mat_invis.use_nodes = True
    mat_invis.blend_method = 'CLIP' # Mode de transparence pour Eevee
    mat_invis.diffuse_color = (0, 0, 0, 0) # Alpha à zéro

    n_nodes = mat_invis.node_tree.nodes
    n_links = mat_invis.node_tree.links
    for n in n_nodes: n_nodes.remove(n)
    
    n_out = n_nodes.new('ShaderNodeOutputMaterial')
    n_transp = n_nodes.new('ShaderNodeBsdfTransparent') 
    n_links.new(n_transp.outputs['BSDF'], n_out.inputs['Surface'])

    nuage.data.materials.append(mat_invis)

    # Configuration de l'affichage du nuage dans l'interface
    nuage.show_instancer_for_viewport = True
    nuage.show_instancer_for_render = True
    nuage.display_type = 'TEXTURED'

    # Parentage pour que le nuage suive les mouvements de l'île
    nuage.parent = ile_cible
    nuage.matrix_parent_inverse = ile_cible.matrix_world.inverted()

    # --- 3. Configuration du système de particules ---
    nuage.modifiers.new("Reglages_Neige", type='PARTICLE_SYSTEM')
    part_sys = nuage.particle_systems[0].settings

    # Paramètres d'émission
    part_sys.count = nb_flocons
    part_sys.frame_start = 1 
    part_sys.frame_end = 500         
    part_sys.lifetime = 600          
    part_sys.lifetime_random = 0.2   

    # Physique des particules (gravité et vent aléatoire)
    part_sys.physics_type = 'NEWTON'
    part_sys.mass = 0.5              
    part_sys.normal_factor = 0.0     
    part_sys.factor_random = 0.5     
    part_sys.brownian_factor = 5.0 # Ajoute du mouvement chaotique aux flocons  
    part_sys.drag_factor = 0.05      

    # Rendu des particules sous forme d'objets
    part_sys.render_type = 'OBJECT'
    part_sys.instance_object = flocon
    part_sys.particle_size = 0.3     
    part_sys.size_random = 0.6       
    part_sys.display_method = 'RENDER'

    # --- 4. Rafraîchissement de la simulation ---
    # On force Blender à calculer les particules en changeant de frame
    bpy.context.scene.frame_set(2)
    nuage.update_tag()
    bpy.context.view_layer.update()
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()



def creer_materiau_neige_pure():
    """
    Génère un matériau de neige réaliste avec une légère teinte bleutée.
    
    Returns:
        bpy.types.Material: Le matériau de neige créé.
    """
    mat_neige = bpy.data.materials.get("Mat_Neige_Cap_Pure")
    if not mat_neige:
        mat_neige = bpy.data.materials.new(name="Mat_Neige_Cap_Pure")
        mat_neige.use_nodes = True

        # Nettoyage des noeuds par défaut pour une config perso
        for n in mat_neige.node_tree.nodes: 
            mat_neige.node_tree.nodes.remove(n)

        nodes = mat_neige.node_tree.nodes
        links = mat_neige.node_tree.links

        # Configuration de la sortie matérielle
        sortie = nodes.new(type='ShaderNodeOutputMaterial')
        sortie.location = (300, 0)

        # Shader principal (BSDF) configuré pour un aspect poudreux
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.location = (0, 0)
        bsdf.inputs["Base Color"].default_value = (0.92, 0.94, 1.0, 1.0) # Blanc cassé bleu
        bsdf.inputs["Roughness"].default_value = 0.35

        # Activation de la translucidité (Subsurface) si disponible dans la version
        if "Subsurface Weight" in bsdf.inputs: 
             bsdf.inputs["Subsurface Weight"].default_value = 1.0
             bsdf.inputs["Subsurface Radius"].default_value = (1.0, 1.0, 1.0)

        links.new(bsdf.outputs['BSDF'], sortie.inputs['Surface'])
    return mat_neige



def ajouter_manteau_neigeux(ile_cible, hauteur_sol_z, epaisseur=0.5):
    """
    Ajoute une géométrie de sol enneigée avec du relief sur l'île.
    
    Args:
        ile_cible (bpy.types.Object): L'objet sur lequel poser la neige.
        hauteur_sol_z (float): Décalage vertical du sol.
        epaisseur (float): Épaisseur de la couche de neige générée.
    """
    print(f"Ajout du manteau neigeux au sol (épaisseur : {epaisseur}m)...")
    bpy.ops.object.select_all(action='DESELECT')

    # Rayon légèrement réduit pour éviter les artefacts sur les bords de l'île
    rayon_ile = ile_cible.dimensions.x / 2.0
    rayon_neige = rayon_ile * 0.95

    # Placement du disque de neige juste au-dessus du sol
    cz = ile_cible.location.z + hauteur_sol_z + 0.1
    bpy.ops.mesh.primitive_circle_add(
        vertices=128, 
        radius=rayon_neige, 
        fill_type='NGON',
        location=(ile_cible.location.x, ile_cible.location.y, cz)
    )
    neige = bpy.context.active_object
    neige.name = "Manteau_Neigeux_Sol"

    # Ajout d'une subdivision pour permettre la déformation (relief)
    mod_sub = neige.modifiers.new(name="Subdivision_Neige", type='SUBSURF')
    mod_sub.levels = 4
    mod_sub.render_levels = 4

    # Création d'une texture procédurale pour générer des bosses
    tex_neige = bpy.data.textures.new("Tex_Neige_Relief", type='CLOUDS')
    tex_neige.noise_scale = 3.0  
    tex_neige.noise_depth = 2

    # Application de la déformation par texture
    mod_disp = neige.modifiers.new(name="Deformation_Neige", type='DISPLACE')
    mod_disp.texture = tex_neige
    mod_disp.strength = 0.3 
    mod_disp.mid_level = 0.0

    # Transformation du disque plat en volume 3D
    mod_solid = neige.modifiers.new(name="Epaisseur_Neige", type='SOLIDIFY')
    mod_solid.thickness = epaisseur 
    mod_solid.offset = 1.0 

    # Lissage visuel
    bpy.ops.object.shade_smooth()

    # Assignation du matériau de neige
    mat_neige_pure = creer_materiau_neige_pure()
    neige.data.materials.append(mat_neige_pure)

    # Liaison à l'île pour la hiérarchie
    neige.parent = ile_cible
    neige.matrix_parent_inverse = ile_cible.matrix_world.inverted()

    return neige



def creer_materiaux_cimetiere():
    """
    Initialise les matériaux de base pour les éléments du cimetière.
    
    Returns:
        tuple: Contient les matériaux (pierre, métal, bois, feuilles).
    """
    # Pierre pour les stèles et rochers
    mat_pierre = bpy.data.materials.get("Mat_Pierre_Tombe")
    if not mat_pierre:
        mat_pierre = bpy.data.materials.new(name="Mat_Pierre_Tombe")
        mat_pierre.use_nodes = True
        bsdf_p = mat_pierre.node_tree.nodes.get("Principled BSDF")
        bsdf_p.inputs["Base Color"].default_value = (0.2, 0.22, 0.25, 1.0) 
        bsdf_p.inputs["Roughness"].default_value = 0.9

    # Métal pour les lames d'épées
    mat_metal = bpy.data.materials.get("Mat_Metal_Epee")
    if not mat_metal:
        mat_metal = bpy.data.materials.new(name="Mat_Metal_Epee")
        mat_metal.use_nodes = True
        bsdf_m = mat_metal.node_tree.nodes.get("Principled BSDF")
        bsdf_m.inputs["Base Color"].default_value = (0.7, 0.75, 0.8, 1.0) 
        bsdf_m.inputs["Metallic"].default_value = 1.0
        bsdf_m.inputs["Roughness"].default_value = 0.3
        
    # Bois pour les troncs d'arbres
    mat_bois = bpy.data.materials.get("Mat_Bois")
    if not mat_bois:
        mat_bois = bpy.data.materials.new(name="Mat_Bois")
        mat_bois.use_nodes = True
        bsdf_b = mat_bois.node_tree.nodes.get("Principled BSDF")
        bsdf_b.inputs["Base Color"].default_value = (0.15, 0.08, 0.05, 1.0) 
        bsdf_b.inputs["Roughness"].default_value = 1.0
        
    # Teinte sombre pour les aiguilles/feuilles de sapins
    mat_feuilles = bpy.data.materials.get("Mat_Feuilles_Mortes")
    if not mat_feuilles:
        mat_feuilles = bpy.data.materials.new(name="Mat_Feuilles_Mortes")
        mat_feuilles.use_nodes = True
        bsdf_f = mat_feuilles.node_tree.nodes.get("Principled BSDF")
        bsdf_f.inputs["Base Color"].default_value = (0.1, 0.15, 0.2, 1.0) 
        bsdf_f.inputs["Roughness"].default_value = 0.8

    return mat_pierre, mat_metal, mat_bois, mat_feuilles



def creer_tombe_maitre(mat_pierre, mat_metal, mat_neige, epaisseur_neige):
    """
    Génère le modèle de référence d'une tombe avec une épée plantée et de la neige.
    """
    bpy.ops.object.select_all(action='DESELECT')
    elements = []

    # Construction de la stèle
    bpy.ops.mesh.primitive_cube_add(scale=(0.6, 0.2, 0.8), location=(0, 0, 0.8))
    stele = bpy.context.active_object
    stele.data.materials.append(mat_pierre)
    elements.append(stele)

    # Ajout d'une couche de neige géométrique sur le dessus
    if epaisseur_neige > 0:
        bpy.ops.mesh.primitive_cube_add(scale=(0.62, 0.22, epaisseur_neige), location=(0, 0, 1.6 + (epaisseur_neige/2)))
        neige_stele = bpy.context.active_object
        neige_stele.data.materials.append(mat_neige)
        elements.append(neige_stele)

    # Construction de l'épée (lame, garde, manche)
    bpy.ops.mesh.primitive_cube_add(scale=(0.05, 0.02, 0.7), location=(0, 0.3, 0.7))
    elements.append(bpy.context.active_object)
    bpy.context.active_object.data.materials.append(mat_metal)

    bpy.ops.mesh.primitive_cube_add(scale=(0.25, 0.04, 0.02), location=(0, 0.3, 1.4))
    elements.append(bpy.context.active_object)
    bpy.context.active_object.data.materials.append(mat_metal)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.3, location=(0, 0.3, 1.55))
    manche = bpy.context.active_object
    manche.data.materials.append(mat_pierre) 
    elements.append(manche)

    # Fusion des éléments en un seul objet
    for obj in elements: obj.select_set(True)
    bpy.context.view_layer.objects.active = stele
    bpy.ops.object.join()

    # Configuration du point d'origine au sol et masquage de l'original
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    stele.hide_viewport = True
    stele.hide_render = True
    return stele



def creer_rocher_maitre(mat_pierre, mat_neige, epaisseur_neige):
    """
    Génère le modèle de référence d'un rocher enneigé.
    """
    bpy.ops.object.select_all(action='DESELECT')
    elements = []
    
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=(0, 0, 0.5))
    rocher = bpy.context.active_object
    rocher.data.materials.append(mat_pierre)
    rocher.scale = (1.5, 1.2, 0.8)
    bpy.ops.object.transform_apply(scale=True)
    elements.append(rocher)
    
    # Ajout d'une calotte neigeuse
    if epaisseur_neige > 0:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=(0, 0, 1.1 + (epaisseur_neige/2)))
        neige_roc = bpy.context.active_object
        neige_roc.data.materials.append(mat_neige)
        neige_roc.scale = (1.4, 1.1, epaisseur_neige)
        bpy.ops.object.transform_apply(scale=True)
        elements.append(neige_roc)

    for obj in elements: obj.select_set(True)
    bpy.context.view_layer.objects.active = rocher
    bpy.ops.object.join()

    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    rocher.hide_viewport = True
    rocher.hide_render = True
    return rocher


def creer_arbre_maitre(mat_bois, mat_feuilles, mat_neige, epaisseur_neige):
    """
    Génère le modèle de référence d'un sapin enneigé.
    """
    bpy.ops.object.select_all(action='DESELECT')
    elements = []

    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=3.0, location=(0, 0, 1.5))
    tronc = bpy.context.active_object
    tronc.data.materials.append(mat_bois)
    elements.append(tronc)

    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=1.5, depth=4.0, location=(0, 0, 4.0))
    feuillage = bpy.context.active_object
    feuillage.data.materials.append(mat_feuilles)
    elements.append(feuillage)

    # Ajout d'une couche de neige épousant la forme du cône
    if epaisseur_neige > 0:
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=1.52, depth=4.0, location=(0, 0, 4.0 + epaisseur_neige))
        neige_arbre = bpy.context.active_object
        neige_arbre.data.materials.append(mat_neige)
        elements.append(neige_arbre)

    for obj in elements: obj.select_set(True)
    bpy.context.view_layer.objects.active = tronc
    bpy.ops.object.join()

    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    tronc.hide_viewport = True
    tronc.hide_render = True
    return tronc


def construire(ile_cible, nb_tombes=150, nb_rochers=30, nb_arbres=40, ratio_vide_centre=0.3, marge_bordure_pct=0.1, hauteur_sol_z=0.0, variation_echelle=(0.7, 1.3), inclinaison_max_deg=15.0, epaisseur_neige_objets=0.4):
    """
    Point d'entrée principal pour la génération procédurale du cimetière.
    Gère le placement aléatoire, les collisions et l'instanciation des objets.
    """
    if not ile_cible:
        return

    # Initialisation des ressources
    mat_pierre, mat_metal, mat_bois, mat_feuilles = creer_materiaux_cimetiere()
    mat_neige_cap = creer_materiau_neige_pure()

    # Création des gabarits
    tombe_master = creer_tombe_maitre(mat_pierre, mat_metal, mat_neige_cap, epaisseur_neige_objets)
    rocher_master = creer_rocher_maitre(mat_pierre, mat_neige_cap, epaisseur_neige_objets)
    arbre_master = creer_arbre_maitre(mat_bois, mat_feuilles, mat_neige_cap, epaisseur_neige_objets)

    # Calcul des zones de spawn
    rayon_ile = ile_cible.dimensions.x / 2.0
    rayon_min = rayon_ile * ratio_vide_centre
    rayon_max = rayon_ile * (1.0 - marge_bordure_pct) 

    cx, cy, cz = ile_cible.location.x, ile_cible.location.y, ile_cible.location.z + hauteur_sol_z
    objets_places = []

    def trouver_position_libre(rayon_collision, max_essais=50):
        """Recherche une coordonnée (x,y) n'intersectant pas d'objet existant."""
        for _ in range(max_essais):
            angle = random.uniform(0, 2 * math.pi)
            r = math.sqrt(random.uniform(rayon_min**2, rayon_max**2))
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)
            collision = False
            for ox, oy, orayon in objets_places:
                if math.hypot(px - ox, py - oy) < (rayon_collision + orayon):
                    collision = True
                    break 
            if not collision: return px, py 
        return None 

    def placer_elements(master_obj, quantite, nom_base, rayon_collision, pencher=True, echelle_base=1.0):
        """Instancie et transforme les objets sur l'île."""
        for i in range(quantite):
            pos = trouver_position_libre(rayon_collision)
            if not pos: continue 
            
            px, py = pos
            objets_places.append((px, py, rayon_collision))
            
            # Copie de l'objet maître
            n_obj = master_obj.copy()
            n_obj.data = master_obj.data 
            bpy.context.collection.objects.link(n_obj)
            
            # Transformation aléatoire (Position, Rotation, Échelle)
            n_obj.location = (px, py, cz - random.uniform(0.0, 0.4))
            n_obj.rotation_euler[2] = random.uniform(0, 2 * math.pi)
            if pencher:
                n_obj.rotation_euler[0] = math.radians(random.uniform(-inclinaison_max_deg, inclinaison_max_deg))
                n_obj.rotation_euler[1] = math.radians(random.uniform(-inclinaison_max_deg, inclinaison_max_deg))
            
            s = random.uniform(variation_echelle[0], variation_echelle[1]) * echelle_base
            n_obj.scale = (s, s, s)
            n_obj.hide_viewport = n_obj.hide_render = False
            n_obj.parent = ile_cible
            n_obj.matrix_parent_inverse = ile_cible.matrix_world.inverted()

    # Exécution du placement
    placer_elements(arbre_master, nb_arbres, "Arbre", 2.0, False, 1.5)
    placer_elements(rocher_master, nb_rochers, "Rocher", 1.5, True, 1.0)
    placer_elements(tombe_master, nb_tombes, "Tombe", 0.8, True, 1.0)

    # Finalisation environnementale
    ajouter_manteau_neigeux(ile_cible, hauteur_sol_z, epaisseur_neige_objets)
    creer_tempete_neige(ile_cible, rayon_ile * 0.95)



if __name__ == "__main__":
    # Nettoyage de la scène
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    # Création de la base de l'île
    bpy.ops.mesh.primitive_cylinder_add(radius=50.0, depth=10.0, location=(0, 0, 5.0))
    ile = bpy.context.active_object
    ile.name = "Ringo_Base"

    # Lancement du générateur
    construire(ile_cible=ile, hauteur_sol_z=5.0)
