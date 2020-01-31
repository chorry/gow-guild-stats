import json
import os

from webapp import db

_PLURALS = {"y": "ies"}


class Uploads(db.Model):
    __table_args__ = {'sqlite_autoincrement': True}
    __tablename__ = 'uploads'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    filename = db.Column(db.String(80))
    filename_original = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,
                           default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    jobs = db.relationship("RecognitionJob", lazy=True, backref="uploaded_file")
    results = db.relationship("RecognitionResults")

    def __init__(self, filename):
        self.filename = os.path.basename(filename)


class RecognitionJob(db.Model):
    __table_args__ = {'sqlite_autoincrement': True}
    __tablename__ = 'recognition_jobs'
    job_id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('uploads.id'))
    status = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,
                           default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())

    def __init__(self, file_id):
        self.file_id = file_id
        self.status = 'new'


class RecognitionMapping(db.Model):
    __tablename__ = 'recognition_mapping'
    id = db.Column(db.Integer, primary_key=True)
    str_from = db.Column(db.String(100))
    str_to = db.Column(db.String(100))
    guild_id = db.Column(db.Integer)


class RecognitionParsedData():
    pass


class RecognitionResults(db.Model):
    __tablename__ = 'recognition_results'
    file_id = db.Column(
        db.Integer,
        db.ForeignKey('uploads.id')
    )
    job_id = db.Column(
        db.Integer,
        db.ForeignKey('recognition_jobs.job_id'),
        primary_key=True
    )
    results = db.Column(db.String(1200))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,
                           default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())

    def __init__(self, job, results):
        """
        :param job:  RecognitionJob
        :param results:  string
        """
        self.job_id = job.job_id
        self.file_id = job.file_id
        self.results = results

    def get_parsed(self):
        return json.loads(self.results)
