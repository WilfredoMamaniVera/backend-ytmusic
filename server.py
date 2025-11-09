# server.py (VERSIÓN CLOUD-READY)
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
import yt_dlp
import os
import uuid
import asyncio
import tempfile

app = FastAPI()

TEMP_DIR = tempfile.gettempdir()

async def cleanup_file(path: str):
    await asyncio.sleep(30) 
    try:
        if os.path.exists(path): os.remove(path)
    except: pass

@app.get("/")
async def root():
    return {"status": "Music Backend Running OK!"}

@app.get("/download")
async def download_music(url: str, quality: str, background_tasks: BackgroundTasks):
    print(f"Nube Descargando: {url} | Calidad: {quality}")
    temp_id = str(uuid.uuid4())
    
    ydl_opts = {
        'quiet': True, 'no_warnings': True,
        # Usar el directorio temporal del sistema
        'outtmpl': os.path.join(TEMP_DIR, f"{temp_id}.%(ext)s")
    }

    # Configurar calidad
    ext = "mp3"
    if quality == 'mp3_320':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}]
    elif quality == 'mp3_192':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
    elif quality == 'm4a':
        ydl_opts['format'] = 'bestaudio[ext=m4a]/best'
        ext = "m4a"
    elif quality == 'flac':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'flac'}]
        ext = "flac"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'audio').replace('/', '_').replace('\\', '_')
            
            final_path = None
            for f in os.listdir(TEMP_DIR):
                if f.startswith(temp_id):
                    final_path = os.path.join(TEMP_DIR, f)
                    break
            
            if not final_path: raise Exception("Error: Archivo no encontrado tras descarga")

        background_tasks.add_task(cleanup_file, final_path)
        # Importante: filename='...' ayuda a que Flutter reciba el nombre correcto
        return FileResponse(final_path, filename=f"{title}.{ext}", media_type='application/octet-stream')

    except Exception as e:
        print(f"Error en servidor: {e}")
        return HTTPException(status_code=500, detail=str(e))