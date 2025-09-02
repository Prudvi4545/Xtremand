from mongoengine import *
from datetime import datetime

# ------------------------
# Audio, Video, Document Files
# ------------------------
class AudioFile(Document):
    filename = StringField(max_length=255, unique=True, required=True)
    content = StringField()
    status = StringField(max_length=50, default='pending')
    meta_data = DictField()
    created_at = DateTimeField(default=datetime.utcnow, required=True)


class VideoFile(Document):
    filename = StringField(max_length=255, unique=True, required=True)
    content = StringField()
    status = StringField(max_length=50, default='pending')
    meta_data = DictField()
    created_at = DateTimeField(default=datetime.utcnow, required=True)


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


# ------------------------
# Images
# ------------------------
class ImageFile(Document):
    file_name = StringField(max_length=255, unique=True, required=True)
    file_path = StringField(max_length=1024)
    file_size = IntField()
    width = IntField()
    height = IntField()
    format = StringField(max_length=50)
    meta_data = DictField()
    created_at = DateTimeField(default=datetime.utcnow, required=True)

    def __str__(self):
        return self.file_name