import os
import json
import uuid
import hashlib
from datetime import datetime

def generate_minimal_ifc(room_name, width, depth, height):
    """Generates a minimal IFC4 text file representing a room box."""
    ifc_content = f"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ORCA Generated Room'),'2;1');
FILE_NAME('{room_name}.ifc','{datetime.now().isoformat()}',('ORCA'),('Antigravity'),'ORCA v0.1','ORCA','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPERSON($,'Antigravity',$,$,$,$,$,$);
#2=IFCORGANIZATION($,'ORCA AI',$,$,$);
#3=IFCPERSONANDORGANIZATION(#1,#2,$);
#4=IFCAPPLICATION(#2,'0.1','ORCA','ORCA');
#5=IFCOWNERHISTORY(#3,#4,$,.ADDED.,$,$,$,{int(datetime.now().timestamp())});
#10=IFCPROJECT('{str(uuid.uuid4())}',#5,'{room_name}',$,$,$,$,$,#20);
#20=IFCUNITASSIGNMENT((#21));
#21=IFCSIUNIT(*,.LENGTHUNIT.,.MILLI.,.METRE.);
#30=IFCSITE('{str(uuid.uuid4())}',#5,'Site',$,$,$,$,$,.ELEMENT.,$,$,$,$,$);
#40=IFCBUILDING('{str(uuid.uuid4())}',#5,'Building',$,$,$,$,$,.ELEMENT.,$,$,$);
#50=IFCBUILDINGSTOREY('{str(uuid.uuid4())}',#5,'Storey',$,$,$,$,$,.ELEMENT.,0.0);
#100=IFCSPACE('{str(uuid.uuid4())}',#5,'{room_name}',$,$,$,$,$,.ELEMENT.,.SPACE.,$);
#110=IFCCARTESIANPOINT((0.0,0.0,0.0));
#111=IFCDIRECTION((0.0,0.0,1.0));
#112=IFCDIRECTION((1.0,0.0,0.0));
#113=IFCAXIS2PLACEMENT3D(#110,#111,#112);
#114=IFCLOCALPLACEMENT($,#113);
#200=IFCSHAPEREPRESENTATION(#20,'Body','SweptSolid',(#210));
#210=IFCEXTRUDEDAREASOLID(#220,#230,#111,{float(height)});
#220=IFCRECTANGLEPROFILEDEF(.AREA.,$,#221,{float(width)},{float(depth)});
#221=IFCAXIS2PLACEMENT2D(#222,#223);
#222=IFCCARTESIANPOINT((0.0,0.0));
#223=IFCDIRECTION((1.0,0.0));
#230=IFCAXIS2PLACEMENT3D(#110,#111,#112);
#300=IFCPRODUCTDEFINITIONSHAPE($,$,(#200));
#400=IFCRELCONTAINEDINSPATIALSTRUCTURE('{str(uuid.uuid4())}',#5,'Container',$,(#100),#50);
ENDSEC;
END-ISO-10303-21;
"""
    return ifc_content

def run(input_txt_path=None, out_dir=None, **params):
    """
    Unified entrypoint for cap.txt_to_ifc.
    Can be called with input_txt_path (M14) or direct params (M15).
    """
    if not out_dir:
        out_dir = os.path.join("runtime", "director_state", "artifacts", "cap.txt_to_ifc", datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(out_dir, exist_ok=True)
    
    spec = {}
    
    # Handle direct params (M15)
    if params:
        spec['name'] = params.get('name', 'Room')
        spec['width'] = params.get('width_mm', params.get('width', 4000))
        spec['depth'] = params.get('depth_mm', params.get('depth', 3000))
        spec['height'] = params.get('height_mm', params.get('height', 2700))
    # Handle file input (M14)
    elif input_txt_path and os.path.exists(input_txt_path):
        with open(input_txt_path, "r") as f:
            line = f.readline().strip()
        parts = line.split()
        if parts and parts[0] == "ROOM":
            for p in parts[1:]:
                if "=" in p:
                    k, v = p.split("=")
                    spec[k] = v
    
    room_name = spec.get('name', 'DefaultRoom')
    width = float(spec.get('width', 4000))
    depth = float(spec.get('depth', 3000))
    height = float(spec.get('height', 2700))
    
    # 2. Generate IFC
    ifc_content = generate_minimal_ifc(room_name, width, depth, height)
    ifc_filename = f"{room_name}.ifc"
    ifc_path = os.path.join(out_dir, ifc_filename)
    with open(ifc_path, "w") as f:
        f.write(ifc_content)
        
    # 3. Create Manifest
    manifest = {
        "capability_id": "cap.txt_to_ifc",
        "ts": datetime.now().isoformat(),
        "files": [
            {
                "name": ifc_filename,
                "hash": hashlib.sha256(ifc_content.encode()).hexdigest(),
                "size": len(ifc_content)
            }
        ]
    }
    manifest_path = os.path.join(out_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        
    # 4. Create Run Receipt
    receipt_id = f"receipt_{str(uuid.uuid4())[:8]}"
    receipt = {
        "receipt_id": receipt_id,
        "ts": datetime.now().isoformat(),
        "capability_id": "cap.txt_to_ifc",
        "status": "success",
        "inputs": [input_txt_path if input_txt_path else "params"],
        "outputs": [ifc_filename, "manifest.json"],
        "command": f"txt_to_ifc {params}",
        "exit_code": 0,
        "hashes": {
            ifc_filename: manifest["files"][0]["hash"],
            "manifest.json": hashlib.sha256(json.dumps(manifest, indent=2).encode()).hexdigest()
        },
        "notes": f"Generated room '{room_name}' ({width}x{depth}x{height})"
    }
    receipt_path = os.path.join(out_dir, f"{receipt_id}.json")
    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2)
        
    return {
        "ifc_path": ifc_path,
        "manifest_path": manifest_path,
        "receipt_path": receipt_path,
        "receipt": receipt,
        "artifact_dir": out_dir
    }
