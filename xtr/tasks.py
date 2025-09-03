from indic_transliteration import sanscript
import datetime
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
import logging

from .models import (
    AudioFile, VideoFile, ImageFile, DocumentFile, HtmlFile,
    JsonFile, XmlFile, LogFile, PPTFile, SpreadsheetFile, ArchiveFile, YamlFile
)
from .minio_client import minio_client, list_objects
from .utils import detect_file_type, SPREADSHEET_EXTENSIONS

# ✅ FFMPEG & Whisper setup
# Make ffmpeg/ffprobe paths configurable for server environments
FFMPEG_EXE = os.environ.get("FFMPEG_PATH")
FFPROBE_EXE = os.environ.get("FFPROBE_PATH")
if not FFMPEG_EXE or not FFPROBE_EXE:
    if platform.system() == "Windows":
        FFMPEG_EXE = FFMPEG_EXE or r"C:\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"
        FFPROBE_EXE = FFPROBE_EXE or r"C:\ffmpeg-7.1.1-essentials_build\bin\ffprobe.exe"
    else:
        FFMPEG_EXE = FFMPEG_EXE or "/usr/bin/ffmpeg"
        FFPROBE_EXE = FFPROBE_EXE or "/usr/bin/ffprobe"

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


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ----------------------------
# Load Whisper model once per worker
# ----------------------------
MODEL_NAME = os.environ.get("WHISPER_MODEL", "base")
try:
    WHISPER_MODEL = whisper.load_model(MODEL_NAME)
    logger.info(f"Loaded Whisper model: {MODEL_NAME}")
except Exception as e:
    logger.error(f"Failed to load Whisper model: {e}")
    WHISPER_MODEL = None

# ----------------------------
# Indic language script mapping
# ----------------------------
LANGUAGE_SCRIPT_MAP = {
    "te": sanscript.TELUGU,
    "hi": sanscript.DEVANAGARI,
    "kn": sanscript.KANNADA,
    "ml": sanscript.MALAYALAM,
    "ta": sanscript.TAMIL,
    "bn": sanscript.BENGALI,
}


def fix_script(text: str, detected_lang: str) -> str:
    """
    Convert text into the expected script for the detected language.
    """
    target_script = LANGUAGE_SCRIPT_MAP.get(detected_lang)
    if not target_script:
        return text  # Unknown language, skip

    # Detect Devanagari chars in text for non-Hindi languages
    if detected_lang != "hi" and any("\u0900" <= ch <= "\u097F" for ch in text):
        try:
            return transliterate(text, Subscript.DEVANAGARI, target_script) # type: ignore
        except Exception:
            return text
    return text


# ----------------------------
# Celery task
# ----------------------------
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_audio(self, bucket_name, filename):
    if WHISPER_MODEL is None:
        logger.error("Whisper model is not loaded. Task aborted.")
        return

    tmp_file, wav_file = None, None
    try:
        logger.info(f"[TASK] 🎧 Processing audio: {filename}")

        # Download file from MinIO
        fd, tmp_file = tempfile.mkstemp(suffix=os.path.splitext(filename)[-1])
        os.close(fd)
        minio_client.fget_object(bucket_name, filename, tmp_file)

        # Convert to WAV if not already
        if not filename.lower().endswith(".wav"):
            wav_file = tmp_file + ".wav"
            AudioSegment.from_file(tmp_file).export(wav_file, format="wav")
        else:
            wav_file = tmp_file

        # Transcribe using Whisper
        result = WHISPER_MODEL.transcribe(wav_file, task="transcribe")
        text = result.get("text", "").strip()
        detected_lang = result.get("language")

        # Fix Indic scripts if needed
        text = fix_script(text, detected_lang)

        # Calculate accurate duration from segments
        segments = result.get("segments", [])
        duration_sec = segments[-1]["end"] if segments else None

        # Save transcription in MongoDB
        AudioFile.objects.create(
            filename=filename,
            content=text,
            status="completed",
            meta_data={
                "detected_language": detected_lang,
                "duration_sec": duration_sec,
            },
        )

        logger.info(f"[TASK] ✅ Audio processed: {filename}")

    except Exception as exc:
        logger.error(f"[TASK] ❌ Failed audio {filename}: {exc}")
        AudioFile.objects.create(
            filename=filename,
            content="",
            status="failed",
            meta_data={"error": str(exc)},
        )
        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error(f"[TASK] Max retries reached for {filename}")

    finally:
        # Clean up temp files
        for path in [tmp_file, wav_file]:
            if path and os.path.exists(path):
                os.remove(path)

@shared_task
def process_video(video_id):
    try:
        # Fetch the VideoFile instance
        video = VideoFile.objects.get(id=video_id)
        s3_key = video.s3_key  # Your stored S3 object key

        print(f"[TASK] 🎬 Video: {s3_key}")

        if WHISPER_MODEL is None:
            raise RuntimeError("Whisper model not loaded on worker")
        
        # Create a temporary file for the video
        fd, vpath = tempfile.mkstemp(suffix=os.path.splitext(s3_key)[-1])
        os.close(fd)

        # Download the video from S3
        with minio_client.get_object(bucket_name, s3_key) as data:
            with open(vpath, "wb") as f:
                f.write(data.read())

        apath = tempfile.mktemp(suffix=".wav")
        # Use ffmpeg to extract audio track
        ffmpeg.input(vpath).output(apath, format="wav", acodec="pcm_s16le", ac=1, ar="16000").run(quiet=True, overwrite_output=True)

        # Transcribe audio
        result = WHISPER_MODEL.transcribe(apath)

        # Save result in database
        VideoFile.objects.filter(id=video_id).update(
            content=result.get("text", ""),
            status="completed"
        )
        print(f"[TASK] ✅ Video processed: {s3_key}")

    except Exception as e:
        # Handle errors and update status
        VideoFile.objects.filter(id=video_id).update(
            content="",
            status="failed",
            meta_data={"error": str(e)}
        )
        print(f"[TASK] ❌ Error processing video: {s3_key} - {str(e)}")
    finally:
        # Cleanup temporary files
        for p in [vpath, apath]:
            if p and os.path.exists(p):
                os.remove(p)                

# @shared_task
# def process_video(bucket_name, filename):
#     print(f"[TASK] 🎬 Video: {filename}")
#     vpath, apath = None, None
#     try:
#         if WHISPER_MODEL is None:
#             raise RuntimeError("Whisper model not loaded on worker")
#         fd, vpath = tempfile.mkstemp(suffix=os.path.splitext(filename)[-1]); os.close(fd)
#         with minio_client.get_object(bucket_name, filename) as data:
#             with open(vpath, "wb") as f: f.write(data.read())

#         apath = tempfile.mktemp(suffix=".wav")
#         # Use ffmpeg to extract audio track
#         ffmpeg.input(vpath).output(apath, format="wav", acodec="pcm_s16le", ac=1, ar="16000").run(quiet=True, overwrite_output=True)

#         result = WHISPER_MODEL.transcribe(apath)
#         VideoFile.objects.create(filename=filename, content=result.get("text", ""), status="completed")
#         print(f"[TASK] ✅ Video processed: {filename}")
#     except Exception as e:
#         VideoFile.objects.create(filename=filename, content="", status="failed", meta_data={"error": str(e)})
#     finally:
#         for p in [vpath, apath]:
#             if p and os.path.exists(p): os.remove(p)


@shared_task
def process_doc(bucket_name, object_name):
    print(f"[TASK]  Document: {object_name}")
    ext = os.path.splitext(object_name)[-1].lower()
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(suffix=ext)
        os.close(fd)
        minio_client.fget_object(bucket_name, object_name, tmp)

        if ext == ".pdf":
            with open(tmp, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text = "\n".join(p.extract_text() or "" for p in reader.pages)
        elif ext == ".docx":
            doc = Document(tmp)
            text = "\n".join(p.text for p in doc.paragraphs)
        elif ext == ".odt":
            try:
                from odf.opendocument import load
                from odf import text as odf_text
                odt_doc = load(tmp)
                parts = []
                for elem in odt_doc.getElementsByType(odf_text.P):
                    parts.append(str(elem))
                text = "\n".join(parts)
            except Exception as e:
                raise RuntimeError(f"Failed to read ODT: {e}")
        elif ext == ".epub":
            try:
                from ebooklib import epub
                from bs4 import BeautifulSoup
                book = epub.read_epub(tmp)
                parts = []
                for item in book.get_items_of_type(9):  # DOCUMENT
                    soup = BeautifulSoup(item.get_content(), "html.parser")
                    parts.append(soup.get_text(" ", strip=True))
                text = "\n".join(parts)
            except Exception as e:
                raise RuntimeError(f"Failed to read EPUB: {e}")
        else:
            with open(tmp, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

        DocumentFile.objects.create(
            filename=object_name,
            content=text,
            status="completed",
            meta_data={"ext": ext, "length": len(text)}
        )
        print(f"[TASK]  Document processed: {object_name}")
    except Exception as e:
        DocumentFile.objects.create(
            filename=object_name,
            content="",
            status="failed",
            meta_data={"error": str(e)}
        )
        print(f"[TASK]  Failed processing {object_name} — {e}")
    finally:
        if tmp and os.path.exists(tmp):
            try:
                os.remove(tmp)
            except PermissionError as e:
                print(f"[TASK]  Could not delete temp file {tmp}: {e}") 


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


import os
import tempfile
import subprocess
from pptx import Presentation
from celery import shared_task
from .models import PPTFile
from .minio_client import minio_client


@shared_task
def process_ppt(bucket_name, filename):
    tmp, converted = None, None
    try:
        ext = os.path.splitext(filename)[-1].lower()

        # Download file from MinIO
        fd, tmp = tempfile.mkstemp(suffix=ext)
        os.close(fd)
        minio_client.fget_object(bucket_name, filename, tmp)

        # Handle .ppt (convert to .pptx)
        if ext == ".ppt":
            outdir = os.path.dirname(tmp)
            basename = os.path.splitext(os.path.basename(tmp))[0]
            libreoffice_bin = os.environ.get("LIBREOFFICE_BIN", "libreoffice")
            try:
                subprocess.run(
                    [libreoffice_bin, "--headless", "--convert-to", "pptx", "--outdir", outdir, tmp],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            except subprocess.CalledProcessError as e:
                # Try fallback to 'soffice' binary
                fallback_bin = os.environ.get("LIBREOFFICE_FALLBACK_BIN", "soffice")
                subprocess.run(
                    [fallback_bin, "--headless", "--convert-to", "pptx", "--outdir", outdir, tmp],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            converted = os.path.join(outdir, basename + ".pptx")
            if not os.path.exists(converted):
                raise RuntimeError("Failed to convert .ppt to .pptx. Ensure LibreOffice is installed.")
            tmp = converted  # switch to converted file

        # Read presentation
        prs = Presentation(tmp)
        text = "\n".join(
            [sh.text for sl in prs.slides for sh in sl.shapes if hasattr(sh, "text")]
        )

        # Save result in DB
        PPTFile.objects.create(
            filename=filename,
            content=text,
            status="completed",
            meta_data={"slides": len(prs.slides)},
        )
        print(f"[TASK] ✅ PPT processed: {filename}")

    except Exception as e:
        PPTFile.objects.create(
            filename=filename,
            content="",
            status="failed",
            meta_data={"error": str(e)},
        )
        print(f"[TASK] ❌ Failed PPT {filename}: {e}")

    finally:
        for f in [tmp, converted]:
            if f and os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass


@shared_task(bind=True, autoretry_for=(OSError,), retry_backoff=True, max_retries=3)
def process_spreadsheet(self, bucket_name, filename):
    tmp = None
    try:
        ext = os.path.splitext(filename)[-1].lower()
        fd, tmp = tempfile.mkstemp(suffix=ext)
        os.close(fd)

        # Download file from MinIO
        minio_client.fget_object(bucket_name, filename, tmp)

        # Read spreadsheet based on extension
        if ext == ".csv":
            df = pd.read_csv(tmp)

        elif ext == ".xlsx":
            try:
                import openpyxl
                df = pd.read_excel(tmp, engine="openpyxl")
            except ImportError as ie:
                raise RuntimeError(
                    "Missing dependency 'openpyxl'. Install with `pip install openpyxl`."
                ) from ie

        elif ext == ".xls":
            try:
                import xlrd
                df = pd.read_excel(tmp, engine="xlrd")
            except ImportError as ie:
                raise RuntimeError(
                    "Missing dependency 'xlrd'. Install with `pip install xlrd`."
                ) from ie

        elif ext == ".ods":
            try:
                df = pd.read_excel(tmp, engine="odf")
            except ImportError as ie:
                raise RuntimeError(
                    "Missing dependency 'odfpy'. Install with `pip install odfpy`."
                ) from ie

        else:
            raise ValueError(f"Unsupported spreadsheet format: {ext}")

        # Save result
        SpreadsheetFile.objects.create(
            filename=filename,
            content=df.to_csv(index=False),
            status="completed",
            meta_data={"columns": list(df.columns), "num_rows": len(df)},
        )
        print(f"[TASK] ✅ Spreadsheet processed: {filename}")

    except Exception as e:
        SpreadsheetFile.objects.create(
            filename=filename,
            content="",
            status="failed",
            meta_data={"error": str(e)},
        )
        print(f"[TASK] ❌ Failed spreadsheet {filename}: {e}")

    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)


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
