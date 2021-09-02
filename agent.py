import os
import tempfile
from threading import Thread

from waitress import serve
from flask_cors import CORS
from flask import Flask, send_file

from flask_restplus import Resource, Api, reqparse
from werkzeug.datastructures import FileStorage

from extractor import run_extractor
from job_manager import write_progress, read_progress
from utils import current_milli_time, store_and_verify_file


def create_app():
    app = Flask("foo", instance_relative_config=True)

    api = Api(
        app,
        version='1.0.0',
        title='Matlab Agent App',
        description='Matlab Agent App',
        default='Matlab Agent App',
        default_label=''
    )

    CORS(app)

    get_extraction_parser = reqparse.RequestParser()
    get_extraction_parser.add_argument('job_id',
                                       type=str,
                                       help='job_id',
                                       required=True)

    @api.route('/get_extracted_data')
    @api.expect(get_extraction_parser)
    class GetExtractedDataService(Resource):
        @api.expect(get_extraction_parser)
        def post(self):
            try:
                args = get_extraction_parser.parse_args()
                job_id = args['job_id']
                result_file_path = job_id + '.zip'
                return send_file(result_file_path,
                                 mimetype='zip',
                                 attachment_filename=result_file_path,
                                 as_attachment=True)
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404

    get_progress_parser = reqparse.RequestParser()
    get_progress_parser.add_argument('job_id',
                                     type=str,
                                     help='job_id',
                                     required=True)

    @api.route('/get_progress')
    @api.expect(get_progress_parser)
    class GetProgressService(Resource):
        @api.expect(get_progress_parser)
        @api.doc(responses={"response": 'json'})
        def post(self):
            try:
                args = get_progress_parser.parse_args()
                job_id = args['job_id']
                percent = read_progress(job_id)
                rv = dict()
                rv['percent'] = percent
                return rv, 200
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404

    extractor_parser = reqparse.RequestParser()
    extractor_parser.add_argument('payload',
                                  location='files',
                                  type=FileStorage,
                                  help='The payload.',
                                  required=False)

    @api.route('/extract')
    @api.expect(extractor_parser)
    class ExtractionService(Resource):
        @api.expect(extractor_parser)
        @api.doc(responses={"response": 'json'})
        def post(self):
            try:
                args = extractor_parser.parse_args()
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404
            try:
                payload_from_request = args['payload']
                work_dir = tempfile.mkdtemp()
                ret, status_or_payload_filepath = store_and_verify_file(payload_from_request, work_dir)
                if ret != 0:
                    rv = dict()
                    rv['status'] = status_or_payload_filepath
                    return rv, 404
                else:
                    job_id = current_milli_time()
                    os.mkdir(job_id)
                    write_progress(job_id, '0')
                    thread = Thread(target=run_extractor, args=(job_id, status_or_payload_filepath, ))
                    thread.start()
                    rv = dict()
                    rv['status'] = job_id
                    return rv, 202
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404

    return app


if __name__ == "__main__":
    serve(create_app(), host='0.0.0.0', port=5000, threads=20)
