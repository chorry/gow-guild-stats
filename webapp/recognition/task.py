import json

import dramatiq
from dramatiq.brokers.redis import RedisBroker

from webapp import create_app, db
from webapp.models import RecognitionJob, RecognitionResults
from webapp.recognition.recognition import Recognizer

redis_broker = RedisBroker(host="redis", port=6379)
dramatiq.set_broker(redis_broker)

@dramatiq.actor
def do_the_job(job_id):
    print("Got job id of {}".format(job_id))
    app = create_app()
    app.app_context().push()
    recognizer = Recognizer(debug=True)
    task = RecognitionJob.query.filter_by(job_id=job_id).first()

    parsed_data = recognizer.recognize_image('uploads/' + task.uploaded_file.filename)
    for result in parsed_data:
        print("{} {}".format(result['number'], result['names']))
    json_data = json.dumps(parsed_data)
    task.status = 'processed'
    db.session.add(task)
    result = RecognitionResults.query.filter_by(job_id=job_id).first()
    if result is None:
        result = RecognitionResults(task, json_data)
    else:
        result.job_id = job_id
        result.results = json_data

    db.session.add(result)
    db.session.commit()
