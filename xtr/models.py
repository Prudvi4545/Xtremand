from djongo import models  # Using Djongo for MongoDB


class AudioFile(models.Model):
    filename = models.CharField(max_length=255, unique=True)
    content = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, default='pending')
    meta_data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audio_file"


class VideoFile(models.Model):
    filename = models.CharField(max_length=255, unique=True)
    content = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, default='pending')
    meta_data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "video_file"



class DocumentFile(models.Model):
    filename = models.CharField(max_length=255, unique=True)
    content = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, default="pending")
    meta_data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "document_file"



class HtmlFile(models.Model):
    filename = models.CharField(max_length=255, unique=True)
    content = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, default='pending')
    meta_data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "html_file"


class JsonFile(models.Model):
    filename = models.CharField(max_length=255, unique=True)
    content = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, default='pending')
    meta_data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "json_file"


class XmlFile(models.Model):
    """
    Stores XML file metadata and content.
    """
    filename = models.CharField(max_length=255, unique=True)  # Name of the XML file
    content = models.TextField(blank=True, null=True)  # XML content as text
    status = models.CharField(max_length=50, default='pending')  # Processing status
    meta_data = models.JSONField(blank=True, null=True)  # Additional metadata
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of creation

    class Meta:
        db_table = "xml_file"


class LogFile(models.Model):
    """
    Stores log file metadata and content.
    """
    filename = models.CharField(max_length=255, unique=True)  # Name of the log file
    content = models.TextField(blank=True, null=True)  # Log content
    status = models.CharField(max_length=50, default='pending')  # Processing status
    meta_data = models.JSONField(blank=True, default=dict)  # Additional metadata
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of creation

    class Meta:
        db_table = "log_file"



class PPTFile(models.Model):
    """
    Stores PowerPoint presentation file metadata and extracted content.
    """
    filename = models.CharField(max_length=255, unique=True)  # Name of the PPT file
    content = models.TextField(blank=True, null=True)  # Extracted text content
    status = models.CharField(max_length=50, default='pending')  # Processing status
    meta_data = models.JSONField(blank=True, null=True)  # Additional metadata (slide count, etc.)
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of creation

    class Meta:
        db_table = "ppt_file"


class SpreadsheetFile(models.Model):
    """
    Stores spreadsheet file metadata and extracted content (CSV, XLSX, etc.).
    """
    filename = models.CharField(max_length=255, unique=True)  # Name of the spreadsheet file
    content = models.TextField(blank=True, null=True)  # Extracted content (CSV as text)
    status = models.CharField(max_length=50, default='pending')  # Processing status
    meta_data = models.JSONField(blank=True, null=True)  # Additional metadata
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of creation

    class Meta:
        db_table = "spreadsheet_file"


class ArchiveFile(models.Model):
    """
    Stores archive file metadata and content list (ZIP, TAR, etc.).
    """
    filename = models.CharField(max_length=255, unique=True)  # Name of the archive file
    content = models.TextField(blank=True, null=True)  # List of files inside the archive
    status = models.CharField(max_length=50, default='pending')  # Processing status
    meta_data = models.JSONField(blank=True, null=True)  # Additional metadata
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of creation

    class Meta:
        db_table = "archive_file"


class YamlFile(models.Model):
    """
    Stores YAML file metadata and content.
    """
    filename = models.CharField(max_length=255, unique=True)  # Name of the YAML file
    content = models.TextField()  # YAML content as text
    status = models.CharField(max_length=20, default="pending")  # Processing status
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of creation

    class Meta:
        db_table = 'yaml_file'   # ✅ Force table name to yaml_file



class ImageFile(models.Model):
    """
    Stores image file metadata and properties.
    """
    file_name = models.CharField(max_length=255, unique=True)  # Name of the image file
    file_path = models.CharField(max_length=1024, blank=True, null=True)  # Path to the image file
    file_size = models.BigIntegerField(blank=True, null=True)  # Size in bytes
    width = models.IntegerField(blank=True, null=True)  # Image width in pixels
    height = models.IntegerField(blank=True, null=True)  # Image height in pixels
    format = models.CharField(max_length=50, blank=True, null=True)  # Image format (JPEG, PNG, etc.)
    meta_data = models.JSONField(blank=True, null=True)  # Additional metadata
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of creation

    class Meta:
        db_table = "image_file"

    def __str__(self):
        # String representation returns the file name
        return self.file_name
