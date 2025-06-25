ALLOWED_EXTENSIONS = {"py", "java", "js", "ts", "c", "cpp", "cs", "html", "jsp", "sql"}
MAX_FILE_SIZE = 1024 * 1024  # 1MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def file_size_okay(content):
    return len(content) <= MAX_FILE_SIZE