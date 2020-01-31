import os
import uuid

from flask import Blueprint, send_from_directory
from flask import current_app as app
from flask import render_template, request
from flask import session
# Set up a Blueprint
from werkzeug.utils import secure_filename

from webapp import db
from webapp.models import Uploads, RecognitionJob
from webapp.recognition.task import do_the_job
uploader_bp = Blueprint('uploader_bp', __name__,
                        template_folder='templates',
                        static_folder='static')


@uploader_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        #        photos = UploadSet('photos', IMAGES)
        #        configure_uploads(app, photos)
        # set session for image results
        if "file_urls" not in session:
            session['file_urls'] = []
        # list to hold our uploaded image urls
        file_urls = session['file_urls']

        # list to hold our uploaded image urls
        file_obj = request.files
        for f in file_obj:
            file = request.files.get(f)
            incoming_file = secure_filename(file.filename)
            base, ext = os.path.splitext(incoming_file)
            new_filename = os.path.join(app.config['UPLOADED_PATH'], "{}{}".format(uuid.uuid4(), ext))
            file.save(new_filename)

            uploaded_model = Uploads(filename=new_filename)
            uploaded_model.username = 'test'
            db.session.add(uploaded_model)
            db.session.commit()

            recognition_job = RecognitionJob(uploaded_model.id)
            db.session.add(recognition_job)
            db.session.commit()
            do_the_job.send(recognition_job.job_id)
        return 'uploaded successfully'
    else:
        return render_template('upload.html')


@uploader_bp.route('/upload_complete')
def upload_complete():
    imglist = Uploads.query.all()
    return render_template('upload_results.html', uploaded_list=imglist)


@uploader_bp.route('/uploads/<filename>')
def render_file(filename):
    return send_from_directory(app.config['UPLOADED_PATH'], filename)
