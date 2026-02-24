import math

import bpy


def create_water(name="Ocean", radius=150.0, location=(0, 0, 0)):
    """
    Génère un immense disque d'eau pour remplir le cratère.
    """
    # Création du disque d'eau (un cylindre très plat)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64, 
        radius=radius, 
        depth=1.0, 
        location=location
    )
    water = bpy.context.active_object
    water.name = name
    
    #  Lissage
    bpy.ops.object.shade_smooth()

    #  Le Matériau de l'eau
    mat_name = "Water_Material"
    if mat_name not in bpy.data.materials:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")
        
        if bsdf:
            # Bleu profond
            bsdf.inputs["Base Color"].default_value = (0.02, 0.2, 0.6, 1.0) 
            # Très lisse pour faire miroir
            bsdf.inputs["Roughness"].default_value = 0.05 
            # Un peu métallique pour mieux refléter le ciel
            bsdf.inputs["Metallic"].default_value = 0.1 
            # (Optionnel) Transparence
            if "Transmission" in bsdf.inputs:
                bsdf.inputs["Transmission"].default_value = 0.8
    else:
        mat = bpy.data.materials[mat_name]

    water.data.materials.append(mat)
    
    return water


def create_water(name="Ocean", radius=150.0, location=(0, 0, 0)):
    """
    Génère un immense disque d'eau pour remplir le cratère.
    """
    # 1. Création du disque d'eau (un cylindre très plat)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64, 
        radius=radius, 
        depth=1.0, 
        location=location
    )
    water = bpy.context.active_object
    water.name = name
    
    # 2. Lissage
    bpy.ops.object.shade_smooth()

    # 3. Le Matériau de l'eau
    mat_name = "Water_Material"
    if mat_name not in bpy.data.materials:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")
        
        if bsdf:
            # couleur de l'eau
            bsdf.inputs["Base Color"].default_value = (0.02, 0.05, 0.1, 1.0)
            # "dureté" du matériaux
            bsdf.inputs["Roughness"].default_value = 0.05 
            # Un peu métallique pour mieux refléter le ciel
            bsdf.inputs["Metallic"].default_value = 0.1 
            #  Transparence
            if "Transmission" in bsdf.inputs:
                bsdf.inputs["Transmission"].default_value = 0.5
    else:
        mat = bpy.data.materials[mat_name]

    water.data.materials.append(mat)
    
    return water




def create_waterfall(name="Cascade_Wano", width=40.0, height=150.0, location=(0, -145, 0)):
    """
    Génère une cascade avec un bord  courbé.
    """
  #On utilise une "Grid" pour avoir plein de sommets à courber (comme un tapis roulant)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=2, y_subdivisions=64, size=1.0, location=location)
    cascade = bpy.context.active_object
    cascade.name = name
    
    # la "douceur" de la courbure
    rayon_courbure = 15.0
    
    # on courbe le haut de la cascade
    for v in cascade.data.vertices:
        # x va de -0.5 à +0.5, on le multiplie pour avoir la largeur totale
        x = v.co.x * width
        
        # h_norm va de 0 tout en bas, à 1 tout en haut
        h_norm = v.co.y + 0.5 
        distance_depuis_haut = (1.0 - h_norm) * height
        
        #si on est dans les 15 derniers mètres du haut, on courbe
        if distance_depuis_haut < rayon_courbure:
            #calcul de l'angle 
            angle = (1.0 - (distance_depuis_haut / rayon_courbure)) * (math.pi / 2.0)
            
            z = -rayon_courbure + math.sin(angle) * rayon_courbure
            y = rayon_courbure - math.cos(angle) * rayon_courbure
        else:
            # Sinon, l'eau chute tout droit vers la mer
            z = -distance_depuis_haut
            y = 0.0
            
        # on donne les nouvelles coordonnées au ppoint
        v.co.x = x
        v.co.y = y
        v.co.z = z
        
    bpy.ops.object.shade_smooth()
    
   # definition du Matériau
    mat_name = "Waterfall_Material"
    
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear() 

    # Nœuds finaux
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (200, 0)
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        
    # Nœuds des rayures
    node_tex_coord = nodes.new(type='ShaderNodeTexCoord')
    node_mapping = nodes.new(type='ShaderNodeMapping')
    node_noise = nodes.new(type='ShaderNodeTexNoise') 
    node_ramp = nodes.new(type='ShaderNodeValToRGB')
    
    node_sep = nodes.new(type='ShaderNodeSeparateXYZ') # Sépare les UV pour récupérer la hauteur
    node_mask = nodes.new(type='ShaderNodeValToRGB') # Crée le dégradé Noir/Blanc
    node_mix = nodes.new(type='ShaderNodeMixRGB') # Mélange le Lac et la Cascade
    
    node_tex_coord.location = (-1000, 0)
    node_mapping.location = (-800, -100)
    node_noise.location = (-600, -100)
    node_ramp.location = (-400, -100)
    
    node_sep.location = (-800, 200)
    node_mask.location = (-500, 200)
    node_mix.location = (-100, 100)

    # les rayures

    node_mapping.inputs['Scale'].default_value = (10.0, 0.1, 1.0)
    node_noise.inputs['Scale'].default_value = 3.0 
    node_noise.inputs['Detail'].default_value = 2.0 
    node_noise.inputs['Roughness'].default_value = 0.5 

    node_ramp.color_ramp.elements[0].position = 0.4
    node_ramp.color_ramp.elements[0].color = (0.02, 0.2, 0.6, 1.0) 
    node_ramp.color_ramp.elements[1].position = 0.6
    node_ramp.color_ramp.elements[1].color = (0.8, 0.95, 1.0, 1.0) 


    #À partir de 75% de hauteur, on reduit l'écume pour avoir un bleu +- uni
    node_mask.color_ramp.elements[0].position = 0.75
    node_mask.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0) # Blanc = Affiche les rayures
    #Tout en haut (92%), on est 100% le bleu pur du lac"
    node_mask.color_ramp.elements[1].position = 0.92
    node_mask.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0) # Noir = Affiche le Lac

    # Configuration du Mélangeur (Mix)
    node_mix.inputs[1].default_value = (0.02, 0.2, 0.6, 1.0) # Entrée 1 (Quand Masque Noir) : Bleu du Lac
    
    # On branche les rayures
    links.new(node_tex_coord.outputs['UV'], node_mapping.inputs['Vector'])
    links.new(node_mapping.outputs['Vector'], node_noise.inputs['Vector'])
    links.new(node_noise.outputs['Fac'], node_ramp.inputs['Fac'])
    
    # On branche le masque de hauteur
    links.new(node_tex_coord.outputs['UV'], node_sep.inputs['Vector'])
    links.new(node_sep.outputs['Y'], node_mask.inputs['Fac'])
    
    links.new(node_mask.outputs['Color'], node_mix.inputs['Fac'])
    links.new(node_ramp.outputs['Color'], node_mix.inputs[2]) # L'entrée 2 reçoit les rayures
    
    #on envoie au shader final
    links.new(node_mix.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs["Roughness"].default_value = 0.1
    
    if "Emission Color" in bsdf.inputs:
        links.new(node_mix.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 0.2
    elif "Emission" in bsdf.inputs:
        links.new(node_mix.outputs['Color'], bsdf.inputs['Emission'])
                
    cascade.data.materials.append(mat)
    return cascade
