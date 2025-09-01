from celery import shared_task
import os
import tempfile
from pptx import Presentation
import whisper
import ffmpeg
import pandas as pd
import PyPDF2
import zipfile
import tarfile
import json
from docx import Document
import xml.etree.ElementTree as ET
import yaml
from PIL import Image
from pydub import AudioSegment
from .models import (
    AudioFile, VideoFile, ImageFile, DocumentFile, HtmlFile,
    JsonFile, XmlFile, LogFile, PPTFile, SpreadsheetFile, ArchiveFile, YamlFile
)
from .minio_client import minio_client, list_objects
from .utils import detect_file_type, SPREADSHEET_EXTENSIONS

# FFMPEG & Whisper setup

import platform
if platform.system() == "Windows":
    FFMPEG_EXE = r"C:\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"
    FFPROBE_EXE = r"C:\ffmpeg-7.1.1-essentials_build\bin\ffprobe.exe"
else:
    # Common Linux path, adjust if needed for your server
    FFMPEG_EXE = "/usr/bin/ffmpeg"
    FFPROBE_EXE = "/usr/bin/ffprobe"
AudioSegment.converter = FFMPEG_EXE
AudioSegment.ffmpeg = FFMPEG_EXE
AudioSegment.ffprobe = FFPROBE_EXE



@shared_task
def fetch_all_buckets_and_objects():
    print("[TASK] 🚀 Fetching all buckets and their objects from MinIO...")
    try:
        for bucket in minio_client.list_buckets():
            bucket_name = bucket.name
            print(f"[TASK] Processing bucket: {bucket_name}")
            objects = list(list_objects(bucket_name))
            print(f"[TASK] Found {len(objects)} objects in bucket: {bucket_name}")
            for obj in objects:
                filename = obj.object_name
                auto_discover_and_process.delay(bucket_name, filename)
    except Exception as e:
        print(f"[TASK] Error fetching buckets/objects: {e}")

@shared_task
def auto_discover_and_process(bucket_name=None, filename=None):
    bucket_name = bucket_name 

    if filename:
        objects = [type('obj', (object,), {'object_name': filename})]
        print(f"[TASK] Processing specific file: {filename} in bucket: {bucket_name}")
    else:
        print(f"[TASK] 🔍 Scanning bucket: {bucket_name}")
        objects = list_objects(bucket_name)

    for obj in objects:
        filename = obj.object_name.strip()
        ftype = detect_file_type(filename)
        print(f"[TASK] ➡️ Found: {filename} (type: {ftype}) in bucket: {bucket_name}")

        if ftype == "audio":
            if not AudioFile.objects.filter(filename=filename).exists():
                process_audio.delay(bucket_name, filename)
            else:
                print(f"[TASK] ⏭️ Skipped: {filename} (already processed)")
        elif ftype == "video":
            if not VideoFile.objects.filter(filename=filename).exists():
                process_video.delay(bucket_name, filename)
            else:
                print(f"[TASK] ⏭️ Skipped: {filename} (already processed)")
        elif ftype == "image":
            if not ImageFile.objects.filter(file_name=filename).exists():
                process_image.delay(bucket_name, filename)
            else:
                print(f"[TASK] ⏭️ Skipped: {filename} (already processed)")
        elif ftype == "document":
            if not DocumentFile.objects.filter(filename=filename).exists():
                process_doc.delay(bucket_name, filename)
            else:
                print(f"[TASK] ⏭️ Skipped: {filename} (already processed)")
        elif ftype == "presentation":
            if not PPTFile.objects.filter(filename=filename).exists():
                process_ppt.delay(bucket_name, filename)
            else:
                print(f"[TASK] ⏭️ Skipped: {filename} (already processed)")
        elif ftype == "spreadsheet":
            if not SpreadsheetFile.objects.filter(filename=filename, status="completed").exists():
                process_spreadsheet.delay(bucket_name, filename)
            else:
                print(f"[TASK] ⏭️ Skipped: {filename} (already processed)")
        elif ftype == "html":
            if not HtmlFile.objects.filter(filename=filename).exists():
                process_html.delay(bucket_name, filename)
            else:
                print(f"[TASK] ⏭️ Skipped: {filename} (already processed)")
        elif ftype == "json":
            if not JsonFile.objects.filter(filename=filename).exists():
                process_json.delay(bucket_name, filename)
            else:
                print(f"[TASK] ⏭️ Skipped: {filename} (already processed)")
        elif ftype == "xml":
            if not XmlFile.objects.filter(filename=filename).exists():
                process_xml.delay(bucket_name,filename)
            else:
                print(f"[TASK] ⏭️ Skipped: {filename} (already processed)")
        elif ftype == "log":
            if not LogFile.objects.filter(filename=filename).exists():
                process_log.delay(bucket_name,filename)
            else:
                print(f"[TASK] ⏭️ Skipped: {filename} (already processed)")
        elif ftype == "archive":
            if not ArchiveFile.objects.filter(filename=filename).exists():
                process_archive.delay(bucket_name, filename)
            else:
                print(f"[TASK] ⏭️ Skipped: {filename} (already processed)")
        elif ftype == "yaml":
            if not YamlFile.objects.filter(filename=filename).exists():
                process_yaml.delay(bucket_name, filename)
            else:
                print(f"[TASK] ⏭️ Skipped: {filename} (already processed)")
        else:
            print(f"[TASK] ⚠️ Unknown file type: {filename}")


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_image(self, bucket_name, object_name):
    print(f"[TASK] 📷 Processing image: {object_name} from bucket: {bucket_name}")
    temp_path = None

    try:
        # Create temp file
        suffix = os.path.splitext(object_name)[-1]
        fd, temp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)

        # Get MinIO client
        client = minio_client

        # Download object to temp file
        client.fget_object(bucket_name, object_name, temp_path)

        # Extract metadata with Pillow
        with Image.open(temp_path) as img:
            width, height = img.size
            format = img.format

            # Save record in DB
            ImageFile.objects.create(
                file_name=object_name,
                file_path=temp_path,  # local temp path (optional)
                file_size=os.path.getsize(temp_path),
                width=width,
                height=height,
                format=format,
                meta_data={
                    "mode": img.mode,
                    "info": img.info
                }
            )

            print(f"[TASK] ✅ Image processed and stored in DB: {object_name}")

    except Exception as e:
        print(f"[TASK] ❌ Error processing image {object_name}: {e}")
        raise self.retry(exc=e)
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)  # clean up
            except Exception:
                pass

@shared_task
def process_audio(bucket_name, filename):
    print(f"[TASK] 🎧 Processing audio: {filename} from bucket: {bucket_name}")
    tmp_path = None
    output_wav = None
    try:
        # Lazy-load Whisper model for compatibility
        model = whisper.load_model("base")
        # Download file to temp
        fd, tmp_path = tempfile.mkstemp(suffix=os.path.splitext(filename)[-1])
        os.close(fd)
        minio_client.fget_object(bucket_name, filename, tmp_path)

        ext = os.path.splitext(filename)[-1].lower()
        if ext != ".wav":
            output_wav = tmp_path + ".wav"
            AudioSegment.from_file(tmp_path).export(output_wav, format="wav")
        else:
            output_wav = tmp_path

        # Transcribe
        result = model.transcribe(output_wav)
        transcript = result.get("text", "").strip()
        lang = result.get("language", "unknown")

        # Save to DB
        AudioFile.objects.create(
            filename=filename,
            content=transcript,
            status="completed",
            meta_data={"detected_language": lang}
        )
        print(f"[TASK] ✅ Completed audio: {filename}")
    except Exception as e:
        print(f"[TASK] ❌ Error processing audio {filename}: {e}")
        AudioFile.objects.create(
            filename=filename,
            content=str(e),
            status="failed",
            meta_data={"error": str(e)}
        )
    finally:
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
            if output_wav and output_wav != tmp_path and os.path.exists(output_wav):
                os.remove(output_wav)
        except Exception:
            pass

@shared_task
def process_video(bucket_name, filename):
    print(f"[TASK] 🎬 Processing video: {filename}")
    temp_video_path = None
    temp_audio_path = None
    try:
        # Lazy-load Whisper model for compatibility
        model = whisper.load_model("base")
        with minio_client.get_object(bucket_name, filename) as data:
            fd, temp_video_path = tempfile.mkstemp(suffix=os.path.splitext(filename)[-1])
            os.close(fd)
            with open(temp_video_path, 'wb') as f:
                f.write(data.read())

        # Extract audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_audio:
            temp_audio_path = tmp_audio.name
        ffmpeg.input(temp_video_path).output(temp_audio_path, format='wav', acodec='pcm_s16le', ac=1, ar='16000').run(quiet=True, overwrite_output=True)

        # Transcribe audio
        result = model.transcribe(temp_audio_path)
        text = result["text"].strip()

        # Save
        VideoFile.objects.create(
            filename=filename,
            content=text,
            status='completed',
            meta_data={
                'duration': None,
                'bit_rate': None,
                'streams': None
            }
        )
        print(f"[TASK] ✅ Completed video: {filename}")
    except Exception as e:
        print(f"[TASK] ❌ Error processing video {filename}: {e}")
    finally:
        try:
            if temp_video_path and os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
        except Exception:
            pass


@shared_task
def process_doc(bucket_name, object_name):
    print(f"[TASK] 📄 Processing document: {object_name}")
    ext = os.path.splitext(object_name)[-1].lower()
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=ext)
        os.close(fd)
        minio_client.fget_object(bucket_name, object_name, tmp_path)
        content = ""
        if ext == ".pdf":
            with open(tmp_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text = page.extract_text() or ""
                    content += text + "\n"
        elif ext == ".docx":
            doc = Document(tmp_path)
            content = "\n".join([para.text for para in doc.paragraphs])
        elif ext in [".txt", ".md", ".rtf", ".odt"]:
            with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        else:
            content = f"Unsupported extension: {ext}"
        DocumentFile.objects.update_or_create(
            filename=object_name,
            defaults={
                "content": content,
                "status": "completed",
                "meta_data": {
                    "ext": ext,
                    "length": len(content)
                }
            }
        )
        print(f"[TASK] ✅ Document processed: {object_name}")
    except Exception as e:
        print(f"[TASK] ❌ Error processing document {object_name}: {e}")
        DocumentFile.objects.update_or_create(
            filename=object_name,
            defaults={
                "content": "",
                "status": "failed",
                "meta_data": {"error": str(e)}
            }
        )
    finally:
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

@shared_task
def process_html(bucket_name, filename):
    print(f"[TASK] 🌐 Processing HTML: {filename}")
    try:
        data = minio_client.get_object(bucket_name, filename).read().decode()
        HtmlFile.objects.create(
            filename=filename,
            content=data,
            status="completed",
            meta_data={}
        )
        print(f"[TASK] ✅ HTML processed: {filename}")
    except Exception as e:
        print(f"[TASK] ❌ Error processing HTML {filename}: {e}")
        HtmlFile.objects.create(
            filename=filename,
            content="",
            status="failed",
            meta_data={"error": str(e)}
        )

@shared_task
def process_json(bucket_name, filename):
    print(f"[TASK] 🗂️ Processing JSON: {filename}")
    try:
        data_bytes = minio_client.get_object(bucket_name, filename).read()
        data_str = data_bytes.decode()
        json_data = json.loads(data_str)
        keys = list(json_data[0].keys()) if isinstance(json_data, list) and json_data else list(json_data.keys())
        JsonFile.objects.create(
            filename=filename,
            content=data_str,
            status="completed",
            meta_data={"keys": keys}
        )
        print(f"[TASK] ✅ JSON processed: {filename}")
    except Exception as e:
        print(f"[TASK] ❌ Error processing JSON {filename}: {e}")
        JsonFile.objects.create(
            filename=filename,
            content="",
            status="failed",
            meta_data={"error": str(e)}
        )

@shared_task
def process_xml(bucket_name, filename):
    print(f"[TASK] 📄 Processing XML: {filename}")
    try:
        with minio_client.get_object(bucket_name, filename) as data:
            xml_content_bytes = data.read()
            xml_content_str = xml_content_bytes.decode()
            root = ET.fromstring(xml_content_str)
            metadata = {
                "root_tag": root.tag,
                "num_children": len(root)
            }
            XmlFile.objects.create(
                filename=filename,
                content=xml_content_str,
                status="completed",
                meta_data=metadata
            )
            print(f"[TASK] ✅ XML processed: {filename}")
    except Exception as e:
        print(f"[TASK] ❌ Error processing XML {filename}: {e}")
        XmlFile.objects.create(
            filename=filename,
            content="",
            status="failed",
            meta_data={"error": str(e)}
        )

@shared_task
def process_log(bucket_name, filename):
    print(f"[TASK] 📜 Processing log: {filename}")
    try:
        data_bytes = minio_client.get_object(bucket_name, filename).read()
        data_str = data_bytes.decode()
        LogFile.objects.create(
            filename=filename,
            content=data_str,
            status="completed",
            meta_data={"length": len(data_str)}
        )
        print(f"[TASK] ✅ Log processed: {filename}")
    except Exception as e:
        print(f"[TASK] ❌ Error processing log {filename}: {e}")
        LogFile.objects.create(
            filename=filename,
            content="",
            status="failed",
            meta_data={"error": str(e)}
        )

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_ppt(self, bucket_name, filename):
    print(f"[TASK] 📑 PPT: {filename}")
    tmp_path = None

    try:
        # Create a temporary file
        fd, tmp_path = tempfile.mkstemp(suffix=".pptx")
        os.close(fd)

        # ✅ Correct MinIO download
        minio_client.fget_object(bucket_name, filename, tmp_path)

        # ✅ Extract PPT content
        presentation = Presentation(tmp_path)

        extracted_text = []
        for slide in presentation.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    extracted_text.append(shape.text)

        content = "\n".join(extracted_text) if extracted_text else "No text extracted"

        # ✅ Metadata (must be JSON serializable)
        props = presentation.core_properties
        meta_data = {
                "author": str(props.author or ""),
                "title": str(props.title or ""),
                "subject": str(props.subject or ""),
                "category": str(props.category or ""),
                "keywords": str(props.keywords or ""),
                "slides_count": int(len(presentation.slides)),
            }

        # ✅ Save to DB
        PPTFile.objects.create(
            filename=filename,
            content=content,
            status="completed",
            meta_data=meta_data,
        )

        print(f"[TASK] ✅ PPT processed: {filename}")

    except Exception as e:
        print(f"[TASK] ❌ Error processing PPT {filename}: {e}")
        raise self.retry(exc=e)

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

@shared_task
def process_spreadsheet(bucket_name, object_name):
    print(f"[TASK] 📊 Processing spreadsheet: {object_name}")
    tmp_path = None
    try:
        ext = os.path.splitext(object_name)[-1].lower()
        if ext not in SPREADSHEET_EXTENSIONS:
            raise ValueError(f"Unsupported spreadsheet extension: {ext}")

        fd, tmp_path = tempfile.mkstemp(suffix=ext)
        os.close(fd)
        minio_client.fget_object(bucket_name, object_name, tmp_path)

        # Read data
        if ext == ".csv":
            df = pd.read_csv(tmp_path)
        elif ext in [".xls", ".xlsx"]:
            df = pd.read_excel(tmp_path, engine="openpyxl")
        elif ext == ".ods":
            df = pd.read_excel(tmp_path, engine="odf")
        else:
            raise ValueError(f"Unhandled extension: {ext}")

        SpreadsheetFile.objects.create(
            filename=object_name,
            content=df.to_csv(index=False),
            status="completed",
            meta_data={
                "columns": list(df.columns),
                "num_rows": len(df)
            }
        )
        print(f"[TASK] ✅ Spreadsheet processed: {object_name}")
    except Exception as e:
        print(f"[TASK] ❌ Error processing spreadsheet {object_name}: {e}")
        SpreadsheetFile.objects.create(
            filename=object_name,
            content=str(e),
            status="failed",
            meta_data={"error": str(e)}
        )
    finally:
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

@shared_task
def process_archive(bucket_name, object_name):
    print(f"[TASK] 📦 Archive: {object_name} in bucket: {bucket_name}")
    tmp_path = None
    extract_path = None
    try:
        ext = os.path.splitext(object_name)[-1].lower()
        if ext not in [".zip", ".tar.gz", ".tgz", ".tar"]:
            raise ValueError(f"Unsupported archive extension: {ext}")

        fd, tmp_path = tempfile.mkstemp(suffix=ext)
        os.close(fd)
        minio_client.fget_object(bucket_name, object_name, tmp_path)

        extracted_files = []

        if ext == ".zip":
            with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                extract_path = tempfile.mkdtemp()
                zip_ref.extractall(extract_path)
                extracted_files = zip_ref.namelist()
        elif ext in [".tar.gz", ".tgz", ".tar"]:
            with tarfile.open(tmp_path, "r:*") as tar_ref:
                extract_path = tempfile.mkdtemp()
                tar_ref.extractall(path=extract_path)
                extracted_files = tar_ref.getnames()
        else:
            raise ValueError(f"Unsupported archive type: {ext}")

        ArchiveFile.objects.create(
            filename=object_name,
            content="\n".join(extracted_files),
            status="completed",
            meta_data={
                "num_files": len(extracted_files),
                "extract_path": extract_path
            }
        )
        print(f"[TASK] ✅ Archive processed: {object_name} with {len(extracted_files)} files.")
    except Exception as e:
        print(f"[TASK] ❌ Error processing archive {object_name}: {e}")
        ArchiveFile.objects.create(
            filename=object_name,
            content=str(e),
            status="failed",
            meta_data={"error": str(e)}
        )
    finally:
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
            if extract_path and os.path.exists(extract_path):
                import shutil
                shutil.rmtree(extract_path, ignore_errors=True)
        except Exception:
            pass

@shared_task
def process_yaml(bucket_name, filename):
    print(f"[TASK] 🗂️ YAML: {filename}")
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".yaml")
        os.close(fd)
        minio_client.fget_object(bucket_name, filename, tmp_path)
        with open(tmp_path, "r") as f:
            data = yaml.safe_load(f)
        YamlFile.objects.create(
            filename=filename,
            content=str(data),
            status="completed"
        )
        print(f"[TASK] ✅ YAML processed: {filename}")
    except Exception as e:
        print(f"[TASK] ❌ Error processing YAML {filename}: {e}")
        YamlFile.objects.create(
            filename=filename,
            content="",
            status="failed"
        )
    finally:
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

@shared_task
def process_minio_file(bucket_name, object_key):
    """Triggered by MinIO event webhook for new files."""
    print(f"[TASK] 🚀 New file event: {object_key} in bucket: {bucket_name}")
    auto_discover_and_process(bucket_name, object_key)