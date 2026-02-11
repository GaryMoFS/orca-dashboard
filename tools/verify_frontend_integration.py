import os

def verify_frontend():
    path = r"C:\Users\Gary\Documents\Projects\Orca AI dashboard\orca_dashboard\web\index.html"
    if not os.path.exists(path):
        print(f"FAILED: {path} does not exist")
        return False
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for Persona Switcher
    if "id=\"persona-list\"" not in content:
        print("FAILED: persona-list container missing")
        return False
    
    # Check for Locked Banner
    if "id=\"locked-banner\"" not in content:
        print("FAILED: locked-banner missing")
        return False
    
    # Check for Persona logic in scripts
    if "async function loadPersonas()" not in content:
        print("FAILED: loadPersonas function missing")
        return False
    
    if "function applyPersonaLayout" not in content:
        print("FAILED: applyPersonaLayout function missing")
        return False
    
    # Check for Orca Modules
    if "class=\"orca-module\"" not in content:
        print("FAILED: orca-module classes missing")
        return False

    print("PASS: Frontend Persona integration verified in source code.")
    return True

if __name__ == "__main__":
    if verify_frontend():
        exit(0)
    else:
        exit(1)
