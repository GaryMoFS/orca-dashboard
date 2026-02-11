import json
import os
import sys

try:
    from jsonschema import validate, ValidationError
except ImportError:
    print("Error: 'jsonschema' library not found. Please install it with: pip install jsonschema")
    sys.exit(1)

def validate_json(instance_path, schema_path):
    print(f"Validating {instance_path} against {schema_path}...")
    try:
        with open(instance_path, 'r') as f:
            instance = json.load(f)
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        validate(instance=instance, schema=schema)
        print("  PASS")
        return True
    except FileNotFoundError as e:
        print(f"  FAIL: File not found: {e.filename}")
    except json.JSONDecodeError as e:
        print(f"  FAIL: Invalid JSON in {instance_path}: {e}")
    except ValidationError as e:
        print(f"  FAIL: Validation error: {e.message}")
    except Exception as e:
        print(f"  FAIL: Unexpected error: {e}")
    return False

def main():
    root = os.getcwd()
    schema_dir = os.path.join(root, "orca", "engine", "schemas")
    
    pack_schema = os.path.join(schema_dir, "orca.ui.persona.pack@0.1.schema.json")
    theme_schema = os.path.join(schema_dir, "orca.ui.theme@0.1.schema.json")
    catalog_schema = os.path.join(schema_dir, "orca.ui.catalog@0.1.schema.json")
    grants_schema = os.path.join(schema_dir, "orca.license.grants@0.1.schema.json")
    
    targets = [
        ("orca/personas/installed/persona.home@0.1/persona.pack.json", pack_schema),
        ("orca/personas/installed/persona.home@0.1/theme.json", theme_schema),
        ("orca/personas/installed/persona.work@0.1/persona.pack.json", pack_schema),
        ("orca/personas/installed/persona.work@0.1/theme.json", theme_schema),
        ("orca/marketplace/catalog.json", catalog_schema),
        ("orca/licenses/grants.json", grants_schema)
    ]
    
    all_pass = True
    for instance_rel, schema_path in targets:
        instance_path = os.path.join(root, instance_rel.replace('/', os.sep))
        if not validate_json(instance_path, schema_path):
            all_pass = False
    
    if all_pass:
        print("\nALL FILES VALIDATED SUCCESSFULLY.")
        sys.exit(0)
    else:
        print("\nVALIDATION FAILED FOR ONE OR MORE FILES.")
        sys.exit(1)

if __name__ == "__main__":
    main()
