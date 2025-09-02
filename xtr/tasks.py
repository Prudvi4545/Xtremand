from celery import shared_task
import os, tempfile, platform, zipfile, tarfile, json, yaml
import pandas as pd
import PyPDF2
from docx import Document
import xml.etree.ElementTree as ET
import whisper, ffmpeg
from pptx import Presentation
from pydub import AudioSegment
from PIL import Image

from .models import (
    AudioFile, VideoFile, ImageFile, DocumentFile, HtmlFile,
    JsonFile, XmlFile, LogFile, PPTFile, SpreadsheetFile, ArchiveFile, YamlFile
)
from .minio_client import minio_client, list_objects
from .utils import detect_file_type, SPREADSHEET_EXTENSIONS

# ✅ FFMPEG & Whisper setup
if platform.system() == "Windows":
    FFMPEG_EXE = r"C:\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"
    FFPROBE_EXE = r"C:\ffmpeg-7.1.1-essentials_build\bin\ffprobe.exe"
else:
    FFMPEG_EXE = "/usr/bin/ffmpeg"
    FFPROBE_EXE = "/usr/bin/ffprobe"

AudioSegment.converter = FFMPEG_EXE
AudioSegment.ffmpeg = FFMPEG_EXE
AudioSegment.ffprobe = FFPROBE_EXE


# ====================================
# Master bucket scanner
# ====================================
@shared_task
def fetch_all_buckets_and_objects():
    print("[TASK] 🚀 Fetching all buckets and their objects from MinIO...")
    try:
        for bucket in minio_client.list_buckets():
            bucket_name = bucket.name
            print(f"[TASK] 📂 Bucket: {bucket_name}")
            for obj in list_objects(bucket_name):
                filename = obj.object_name
                auto_discover_and_process.delay(bucket_name, filename)
    except Exception as e:
        print(f"[TASK] ❌ Error fetching buckets/objects: {e}")


# ====================================
# Dispatcher
# ====================================
@shared_task
def auto_discover_and_process(bucket_name=None, filename=None):
    if not bucket_name:
        print("[TASK] ⚠️ Missing bucket_name")
        return

    files = [type("obj", (object,), {"object_name": filename})] if filename else list_objects(bucket_name)

    for obj in files:
        fname = obj.object_name.strip()
        ftype = detect_file_type(fname)
        print(f"[TASK] ➡️ Found: {fname} (type: {ftype})")

        # Dispatch
        if ftype == "audio" and not AudioFile.objects(filename=fname).first():
            process_audio.delay(bucket_name, fname)
        elif ftype == "video" and not VideoFile.objects(filename=fname).first():
            process_video.delay(bucket_name, fname)
        elif ftype == "image" and not ImageFile.objects(file_name=fname).first():
            process_image.delay(bucket_name, fname)
        elif ftype == "document" and not DocumentFile.objects(filename=fname).first():
            process_doc.delay(bucket_name, fname)
        elif ftype == "presentation" and not PPTFile.objects(filename=fname).first():
            process_ppt.delay(bucket_name, fname)
        elif ftype == "spreadsheet" and not SpreadsheetFile.objects(filename=fname).first():
            process_spreadsheet.delay(bucket_name, fname)
        elif ftype == "html" and not HtmlFile.objects(filename=fname).first():
            process_html.delay(bucket_name, fname)
        elif ftype == "json" and not JsonFile.objects(filename=fname).first():
            process_json.delay(bucket_name, fname)
        elif ftype == "xml" and not XmlFile.objects(filename=fname).first():
            process_xml.delay(bucket_name, fname)
        elif ftype == "log" and not LogFile.objects(filename=fname).first():
            process_log.delay(bucket_name, fname)
        elif ftype == "archive" and not ArchiveFile.objects(filename=fname).first():
            process_archive.delay(bucket_name, fname)
        elif ftype == "yaml" and not YamlFile.objects(filename=fname).first():
            process_yaml.delay(bucket_name, fname)
        else:
            print(f"[TASK] ⏭️ Skipped or unknown: {fname}")


# ====================================
# Individual processors
# ====================================
@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_image(self, bucket_name, object_name):
    print(f"[TASK] 📷 Image: {object_name}")
    tmp_path = None
    try:
        suffix = os.path.splitext(object_name)[-1]
        fd, tmp_path = tempfile.mkstemp(suffix=suffix); os.close(fd)
        minio_client.fget_object(bucket_name, object_name, tmp_path)

        with Image.open(tmp_path) as img:
            ImageFile.objects.create(
                file_name=object_name,
                file_size=os.path.getsize(tmp_path),
                width=img.size[0],
                height=img.size[1],
                format=img.format,
                meta_data={"mode": img.mode, "info": img.info},
            )
        print(f"[TASK] ✅ Image processed: {object_name}")
    except Exception as e:
        print(f"[TASK] ❌ Error image {object_name}: {e}")
        raise self.retry(exc=e)
    finally:
        if tmp_path and os.path.exists(tmp_path): os.remove(tmp_path)


@shared_task
def process_audio(bucket_name, filename):
    print(f"[TASK] 🎧 Audio: {filename}")
    tmp, wav_path = None, None
    try:
        model = whisper.load_model("base")
        fd, tmp = tempfile.mkstemp(suffix=os.path.splitext(filename)[-1]); os.close(fd)
        minio_client.fget_object(bucket_name, filename, tmp)

        if not filename.lower().endswith(".wav"):
            wav_path = tmp + ".wav"
            AudioSegment.from_file(tmp).export(wav_path, format="wav")
        else:
            wav_path = tmp

        result = model.transcribe(wav_path)
        AudioFile.objects.create(
            filename=filename,
            content=result.get("text", ""),
            status="completed",
            meta_data={"detected_language": result.get("language")},
        )
        print(f"[TASK] ✅ Audio processed: {filename}")
    except Exception as e:
        AudioFile.objects.create(filename=filename, content="", status="failed", meta_data={"error": str(e)})
    finally:
        for p in [tmp, wav_path]:
            if p and os.path.exists(p): os.remove(p)


@shared_task
def process_video(bucket_name, filename):
    print(f"[TASK] 🎬 Video: {filename}")
    vpath, apath = None, None
    try:
        model = whisper.load_model("base")
        fd, vpath = tempfile.mkstemp(suffix=os.path.splitext(filename)[-1]); os.close(fd)
        with minio_client.get_object(bucket_name, filename) as data:
            with open(vpath, "wb") as f: f.write(data.read())

        apath = tempfile.mktemp(suffix=".wav")
        ffmpeg.input(vpath).output(apath, format="wav", acodec="pcm_s16le", ac=1, ar="16000").run(quiet=True, overwrite_output=True)

        result = model.transcribe(apath)
        VideoFile.objects.create(filename=filename, content=result.get("text", ""), status="completed")
        print(f"[TASK] ✅ Video processed: {filename}")
    except Exception as e:
        VideoFile.objects.create(filename=filename, content="", status="failed", meta_data={"error": str(e)})
    finally:
        for p in [vpath, apath]:
            if p and os.path.exists(p): os.remove(p)


@shared_task
def process_doc(bucket_name, filename):
    print(f"[TASK] 📄 Document: {filename}")
    ext, tmp = os.path.splitext(filename)[-1].lower(), None
    try:
        fd, tmp = tempfile.mkstemp(suffix=ext); os.close(fd)
        minio_client.fget_object(bucket_name, filename, tmp)

        text = ""
        if ext == ".pdf":
            reader = PyPDF2.PdfReader(open(tmp, "rb"))
            text = "\n".join([p.extract_text() or "" for p in reader.pages])
        elif ext == ".docx":
            doc = Document(tmp); text = "\n".join([p.text for p in doc.paragraphs])
        else:
            text = open(tmp, encoding="utf-8", errors="ignore").read()

        DocumentFile.objects.create(filename=filename, content=text, status="completed", meta_data={"ext": ext})
        print(f"[TASK] ✅ Document processed: {filename}")
    except Exception as e:
        DocumentFile.objects.create(filename=filename, content="", status="failed", meta_data={"error": str(e)})
    finally:
        if tmp and os.path.exists(tmp): os.remove(tmp)


@shared_task
def process_html(bucket_name, filename):
    try:
        data = minio_client.get_object(bucket_name, filename).read().decode()
        HtmlFile.objects.create(filename=filename, content=data, status="completed")
        print(f"[TASK] ✅ HTML processed: {filename}")
    except Exception as e:
        HtmlFile.objects.create(filename=filename, content="", status="failed", meta_data={"error": str(e)})


@shared_task
def process_json(bucket_name, filename):
    try:
        raw = minio_client.get_object(bucket_name, filename).read().decode()
        JsonFile.objects.create(filename=filename, content=raw, status="completed")
        print(f"[TASK] ✅ JSON processed: {filename}")
    except Exception as e:
        JsonFile.objects.create(filename=filename, content="", status="failed", meta_data={"error": str(e)})


@shared_task
def process_xml(bucket_name, filename):
    try:
        raw = minio_client.get_object(bucket_name, filename).read().decode()
        root = ET.fromstring(raw)
        XmlFile.objects.create(filename=filename, content=raw, status="completed", meta_data={"root_tag": root.tag})
        print(f"[TASK] ✅ XML processed: {filename}")
    except Exception as e:
        XmlFile.objects.create(filename=filename, content="", status="failed", meta_data={"error": str(e)})


@shared_task
def process_log(bucket_name, filename):
    try:
        raw = minio_client.get_object(bucket_name, filename).read().decode()
        LogFile.objects.create(filename=filename, content=raw, status="completed", meta_data={"length": len(raw)})
        print(f"[TASK] ✅ Log processed: {filename}")
    except Exception as e:
        LogFile.objects.create(filename=filename, content="", status="failed", meta_data={"error": str(e)})


@shared_task
def process_ppt(bucket_name, filename):
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(suffix=".pptx"); os.close(fd)
        minio_client.fget_object(bucket_name, filename, tmp)
        prs = Presentation(tmp)
        text = "\n".join([sh.text for sl in prs.slides for sh in sl.shapes if hasattr(sh, "text")])
        PPTFile.objects.create(filename=filename, content=text, status="completed", meta_data={"slides": len(prs.slides)})
        print(f"[TASK] ✅ PPT processed: {filename}")
    except Exception as e:
        PPTFile.objects.create(filename=filename, content="", status="failed", meta_data={"error": str(e)})
    finally:
        if tmp and os.path.exists(tmp): os.remove(tmp)


@shared_task
def process_spreadsheet(bucket_name, filename):
    tmp = None
    try:
        ext = os.path.splitext(filename)[-1].lower()
        fd, tmp = tempfile.mkstemp(suffix=ext); os.close(fd)
        minio_client.fget_object(bucket_name, filename, tmp)

        if ext == ".csv":
            df = pd.read_csv(tmp)
        else:
            df = pd.read_excel(tmp)

        SpreadsheetFile.objects.create(
            filename=filename,
            content=df.to_csv(index=False),
            status="completed",
            meta_data={"columns": list(df.columns), "num_rows": len(df)},
        )
        print(f"[TASK] ✅ Spreadsheet processed: {filename}")
    except Exception as e:
        SpreadsheetFile.objects.create(filename=filename, content="", status="failed", meta_data={"error": str(e)})
    finally:
        if tmp and os.path.exists(tmp): os.remove(tmp)


@shared_task
def process_archive(bucket_name, filename):
    tmp, extract_path = None, None
    try:
        ext = os.path.splitext(filename)[-1].lower()
        fd, tmp = tempfile.mkstemp(suffix=ext); os.close(fd)
        minio_client.fget_object(bucket_name, filename, tmp)

        extracted = []
        if ext == ".zip":
            with zipfile.ZipFile(tmp) as z: extracted = z.namelist()
        else:
            with tarfile.open(tmp, "r:*") as t: extracted = t.getnames()

        ArchiveFile.objects.create(filename=filename, content="\n".join(extracted), status="completed", meta_data={"num_files": len(extracted)})
        print(f"[TASK] ✅ Archive processed: {filename}")
    except Exception as e:
        ArchiveFile.objects.create(filename=filename, content="", status="failed", meta_data={"error": str(e)})
    finally:
        if tmp and os.path.exists(tmp): os.remove(tmp)


@shared_task
def process_yaml(bucket_name, filename):
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(suffix=".yaml"); os.close(fd)
        minio_client.fget_object(bucket_name, filename, tmp)
        data = yaml.safe_load(open(tmp))
        YamlFile.objects.create(filename=filename, content=str(data), status="completed")
        print(f"[TASK] ✅ YAML processed: {filename}")
    except Exception as e:
        YamlFile.objects.create(filename=filename, content="", status="failed", meta_data={"error": str(e)})
    finally:
        if tmp and os.path.exists(tmp): os.remove(tmp)


# ====================================
# MinIO event handler
# ====================================
@shared_task
def process_minio_file(bucket_name, object_key):
    print(f"[TASK] 🚀 New file event: {object_key} in bucket: {bucket_name}")
    auto_discover_and_process.delay(bucket_name, object_key)
