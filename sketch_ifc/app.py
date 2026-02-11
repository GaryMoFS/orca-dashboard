from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import time
from processor import SketchProcessor
from builder import IFCBuilder

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No image selected"}), 400

    job_id = f"job_{int(time.time())}"
    img_path = os.path.join(UPLOAD_FOLDER, f"{job_id}_{file.filename}")
    file.save(img_path)
    
    # Stage 1: Interpret
    processor = SketchProcessor()
    try:
        schema = processor.process_image(img_path)
    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

    # Stage 2 & 3: Construct & Export
    ifc_filename = os.path.join(OUTPUT_FOLDER, f"{job_id}.ifc")
    glb_filename = os.path.join(OUTPUT_FOLDER, f"{job_id}.glb")
    
    builder = IFCBuilder(filename=ifc_filename)
    try:
        builder.build_from_schema(schema)
        builder.save()
        # Stage 4: Preview (GLB Export)
        # Note: IfcOpenShell geom engine might require specific dependencies.
        # If it fails, we handle it gracefully.
        try:
            builder.export_glb(glb_filename)
            has_preview = True
        except Exception as e:
            print(f"GLB export failed: {e}")
            has_preview = False
            
    except Exception as e:
        return jsonify({"error": f"Building failed: {str(e)}"}), 500

    return jsonify({
        "status": "success",
        "job_id": job_id,
        "ifc_url": f"/files/{os.path.basename(ifc_filename)}",
        "glb_url": f"/files/{os.path.basename(glb_filename)}" if has_preview else None,
        "walls_count": len(schema['walls'])
    })

@app.route('/view/<job_id>')
def view(job_id):
    glb_path = f"/files/{job_id}.glb"
    return render_template('viewer.html', glb_url=glb_path)

@app.route('/files/<filename>')
def serve_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
