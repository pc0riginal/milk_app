@app.get("/debug/static")
async def debug_static():
    import os
    static_path = "app/static"
    css_path = "app/static/css"
    
    return {
        "static_exists": os.path.exists(static_path),
        "css_exists": os.path.exists(css_path),
        "static_files": os.listdir(static_path) if os.path.exists(static_path) else [],
        "css_files": os.listdir(css_path) if os.path.exists(css_path) else [],
        "working_dir": os.getcwd()
    }