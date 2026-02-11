import ifcopenshell
import ifcopenshell.api
import ifcopenshell.geom
import uuid
import time
import numpy as np
import trimesh

class IFCBuilder:
    def __init__(self, filename="output.ifc"):
        self.filename = filename
        self.file = ifcopenshell.file()
        self.project = None
        self.site = None
        self.building = None
        self.storey = None
        self.body_context = None
        
        self._init_project()

    def _init_project(self):
        """Initialize the basic IFC project structure"""
        # Create project using API to ensure proper initialization (GlobalId, OwnerHistory, etc.)
        self.project = ifcopenshell.api.run("root.create_entity", self.file, ifc_class="IfcProject", name="Orca Sketch Project")
        
        # Units
        ifcopenshell.api.run("unit.assign_unit", self.file)
        
        # Geometry Contexts
        # Create a 3D Model context
        model_context = ifcopenshell.api.run("context.add_context", self.file, context_type="Model")
        
        # Create a 'Body' subcontext for 3D body representations
        self.body_context = ifcopenshell.api.run("context.add_context", self.file, 
                                            context_type="Model", 
                                            context_identifier="Body", 
                                            target_view="MODEL_VIEW", 
                                            parent=model_context)

        # Hierarchy
        self.site = ifcopenshell.api.run("root.create_entity", self.file, ifc_class="IfcSite", name="Sketch Site")
        self.building = ifcopenshell.api.run("root.create_entity", self.file, ifc_class="IfcBuilding", name="Sketch Building")
        self.storey = ifcopenshell.api.run("root.create_entity", self.file, ifc_class="IfcBuildingStorey", name="Level 0")
        
        ifcopenshell.api.run("aggregate.assign_object", self.file, relating_object=self.project, products=[self.site])
        ifcopenshell.api.run("aggregate.assign_object", self.file, relating_object=self.site, products=[self.building])
        ifcopenshell.api.run("aggregate.assign_object", self.file, relating_object=self.building, products=[self.storey])
        
        # Geometry Context
        self.body_context = ifcopenshell.api.run("context.add_context", self.file, context_type="Model")

    def create_extrusion(self, width, height, depth, context):
        """Helper to create a simple rectangular extrusion"""
        # 1. Profile
        profile = self.file.create_entity("IfcRectangleProfileDef", 
                                          ProfileType="AREA", 
                                          XDim=float(width), 
                                          YDim=float(depth))
        
        # 2. Placement for extrusion (local to profile)
        placement = self.file.createIfcAxis2Placement3D(
            self.file.createIfcCartesianPoint((0.0, 0.0, 0.0)),
            self.file.createIfcDirection((0.0, 0.0, 1.0)),
            self.file.createIfcDirection((1.0, 0.0, 0.0))
        )
        
        # 3. Solid
        solid = self.file.create_entity("IfcExtrudedAreaSolid", 
                                        SweptArea=profile, 
                                        Position=placement, 
                                        ExtrudedDirection=self.file.createIfcDirection((0.0, 0.0, 1.0)), 
                                        Depth=float(height))
                                        
        # 4. Representation
        rep = self.file.create_entity("IfcShapeRepresentation", 
                                      ContextOfItems=context, 
                                      RepresentationIdentifier="Body", 
                                      RepresentationType="SweptSolid", 
                                      Items=[solid])
                                      
        return rep

    def add_slab(self, footprint_points):
        """Create a floor slab based on the footprint"""
        if not footprint_points:
            return

        min_x = min(p[0] for p in footprint_points)
        max_x = max(p[0] for p in footprint_points)
        min_y = min(p[1] for p in footprint_points)
        max_y = max(p[1] for p in footprint_points)
        
        # Add some offset
        min_x -= 1.0; max_x += 1.0; min_y -= 1.0; max_y += 1.0
        
        length = float(max_x - min_x)
        width = float(max_y - min_y)
        depth = 0.3
        
        slab = ifcopenshell.api.run("root.create_entity", self.file, ifc_class="IfcSlab", name="Floor Slab")
        ifcopenshell.api.run("spatial.assign_container", self.file, relating_structure=self.storey, products=[slab])
        
        # Manual Geometry
        rep = self.create_extrusion(length, depth, width, self.body_context) # Profile X=Length, Y=Width (depth in profile terms)
        
        product_shape = self.file.create_entity("IfcProductDefinitionShape", Representations=[rep])
        slab.Representation = product_shape
        
        # Placement
        cx = (min_x + max_x) / 2
        cy = (min_y + max_y) / 2
        
        point = self.file.createIfcCartesianPoint((float(cx), float(cy), 0.0))
        axis2placement = self.file.createIfcAxis2Placement3D(point)
        local_placement = self.file.createIfcLocalPlacement(self.storey.ObjectPlacement, axis2placement)
        slab.ObjectPlacement = local_placement

    def build_from_schema(self, schema: dict):
        """Construct IFC geometry from the JSON schema"""
        
        all_points = []
        
        # Create Walls
        for wall_data in schema.get("walls", []):
            start = wall_data["start"]
            end = wall_data["end"]
            thickness = wall_data.get("thickness", 0.2)
            height = wall_data.get("height", 2.5)
            
            all_points.append(start)
            all_points.append(end)
            
            # Calculate length and rotation
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            length = float(np.sqrt(dx**2 + dy**2))
            height = float(height)
            thickness = float(thickness)
            
            # Create Wall Type
            wall_type = ifcopenshell.api.run("root.create_entity", self.file, ifc_class="IfcWallType", name="Standard Wall")
            
            # Create Wall instance
            wall = ifcopenshell.api.run("root.create_entity", self.file, ifc_class="IfcWall", name="Wall")
            ifcopenshell.api.run("type.assign_type", self.file, related_objects=[wall], relating_type=wall_type)
            ifcopenshell.api.run("spatial.assign_container", self.file, relating_structure=self.storey, products=[wall])
            
            # Geometry (Extruded Area Solid)
            angle = float(np.arctan2(dy, dx))
            
            # Manual Geometry Creation
            # Profile X = Length, Y = Thickness
            rep = self.create_extrusion(length, height, thickness, self.body_context)
            
            product_shape = self.file.create_entity("IfcProductDefinitionShape", Representations=[rep])
            wall.Representation = product_shape
            
            # Move wall to correct location and rotation
            # Center of the wall at start point? No, extrusion usually starts at origin of placement.
            # If standard profile is center-aligned?
            # IfcRectangleProfileDef is centered at its Position (default 0,0).
            # So the extrusion will be centered on the placement axis.
            # We want the wall to start at `start` and go to `end`.
            # So the center of the wall segment is at (start + end) / 2.
            
            mid_x = (start[0] + end[0]) / 2
            mid_y = (start[1] + end[1]) / 2
            
            point = self.file.createIfcCartesianPoint((float(mid_x), float(mid_y), 0.0))
            axis = self.file.createIfcDirection((0.0, 0.0, 1.0))
            ref_dir = self.file.createIfcDirection((float(np.cos(angle)), float(np.sin(angle)), 0.0))
            
            axis2placement = self.file.createIfcAxis2Placement3D(point, axis, ref_dir)
            local_placement = self.file.createIfcLocalPlacement(self.storey.ObjectPlacement, axis2placement)
            wall.ObjectPlacement = local_placement

        # Add generic floor if we have points
        if all_points:
            self.add_slab(all_points)

    def save(self):
        self.file.write(self.filename)
        return self.filename

    def export_glb(self, output_glb="output.glb"):
        """
        Export the IFC geometry to GLB for web viewing.
        Uses ifcopenshell.geom to triangulate and trimesh to export.
        """
        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)
        
        # Temporary workaround: ifcopenshell might fail to find schemas if not standard
        # We assume standard schema is loaded by default
        
        scene = trimesh.Scene()
        
        try:
            iterator = ifcopenshell.geom.iterator(settings, self.file) # multiprocessing removed
            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    verts = shape.geometry.verts
                    faces = shape.geometry.faces
                    
                    # Verts is flat list [x,y,z, x,y,z...]
                    # Faces is flat list [v1,v2,v3...]
                    
                    if not verts or not faces:
                         if not iterator.next(): break
                         continue

                    v = np.array(verts).reshape((-1, 3))
                    f = np.array(faces).reshape((-1, 3))
                    
                    mesh = trimesh.Trimesh(vertices=v, faces=f)
                    scene.add_geometry(mesh)
                    
                    if not iterator.next():
                        break
        except Exception as e:
            # Fallback if iterator fails or ifcopenshell setup is tricky without proper schema/deps
            print(f"Geometry extraction warning: {e}")
            pass
            
        scene.export(output_glb)
        return output_glb
