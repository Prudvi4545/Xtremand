from mongoengine import *
from datetime import datetime, timezone
from mongoengine import Document, StringField, IntField, DictField, DateTimeField

# ------------------------
# Audio, Video, Document Files
# ------------------------
class VideoFile(Document):
    filename = StringField(max_length=255, unique=True, required=True)
    content = StringField()
    status = StringField(max_length=50, default='pending')
    meta_data = DictField()
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc), required=True)
    meta = {
        'collection': 'video_file'  # Custom collection name
    }

class AudioFile(Document):
    filename = StringField(max_length=255, unique=True, required=True)
    content = StringField()
    status = StringField(max_length=50, default='pending')
    meta_data = DictField()
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc), required=True)


class DocumentFile(Document):
    filename = StringField(max_length=255, unique=True, required=True)
    content = StringField()
    status = StringField(max_length=50, default='pending')
    meta_data = DictField()
    created_at = DateTimeField(default=datetime.utcnow, required=True)


class HtmlFile(Document):
    filename = StringField(max_length=255, unique=True, required=True)
    content = StringField()
    status = StringField(max_length=50, default='pending')
    meta_data = DictField()
    created_at = DateTimeField(default=datetime.utcnow, required=True)


class JsonFile(Document):
    filename = StringField(max_length=255, unique=True, required=True)
    content = StringField()
    status = StringField(max_length=50, default='pending')
    meta_data = DictField()
    created_at = DateTimeField(default=datetime.utcnow, required=True)


class XmlFile(Document):
    filename = StringField(max_length=255, unique=True, required=True)
    content = StringField()
    status = StringField(max_length=50, default='pending')
    meta_data = DictField()
    created_at = DateTimeField(default=datetime.utcnow, required=True)


class LogFile(Document):
    filename = StringField(max_length=255, unique=True, required=True)
    content = StringField()
    status = StringField(max_length=50, default='pending')
    meta_data = DictField()
    created_at = DateTimeField(default=datetime.utcnow, required=True)


class PPTFile(Document):
    filename = StringField(max_length=255, unique=True, required=True)
    content = StringField()
    status = StringField(max_length=50, default='pending')
    meta_data = DictField()
    created_at = DateTimeField(default=datetime.utcnow, required=True)
    meta = {
        'collection': 'ppt_file'  # Custom collection name
    }

class SpreadsheetFile(Document):
    filename = StringField(max_length=255, unique=True, required=True)
    content = StringField()
    status = StringField(max_length=50, default='pending')
    meta_data = DictField()
    created_at = DateTimeField(default=datetime.utcnow, required=True)


class ArchiveFile(Document):
    filename = StringField(max_length=255, unique=True, required=True)
    content = StringField()
    status = StringField(max_length=50, default='pending')
    meta_data = DictField()
    created_at = DateTimeField(default=datetime.utcnow, required=True)


class YamlFile(Document):
    filename = StringField(max_length=255, unique=True, required=True)
    content = StringField()
    status = StringField(max_length=20, default='pending')
    created_at = DateTimeField(default=datetime.utcnow, required=True)
    meta_data = DictField() 

# ------------------------
# Images
# ------------------------



class ImageFile(Document):
    filename = StringField(max_length=255, unique=True, required=True)
    file_path = StringField(max_length=1024)
    file_size = IntField()
    width = IntField()
    height = IntField()
    format = StringField(max_length=50)
    meta_data = DictField()
    created_at = DateTimeField(default=datetime.utcnow, required=True)
    # ✅ NEW:
    updated_at = DateTimeField(default=datetime.utcnow)
    status = StringField(max_length=50, default="completed")

    def __str__(self):
        return self.filename

    # ✅ OPTIONAL convenience (used in task)
    def mark_completed(self):
        self.status = "completed"
        self.updated_at = datetime.utcnow()
        self.save()

    def mark_failed(self, error_message: str):
        self.status = "failed"
        self.meta_data = {"error": error_message}
        self.updated_at = datetime.utcnow()
        self.save()

