# import json
# import subprocess
# from server.celery import app
#
#
# def worker_is_on():
#     bash_command = "heroku ps --app cirs-dev worker --json"
#     process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
#     output, error = process.communicate()
#     if output:
#         worker_response = json.loads(output.decode('utf-8'))
#         return worker_response[0].get('state') == 'up' or 'starting'
#     else:
#         return False
#
#
# def no_jobs_in_queue():
#     celery_info = app.control.inspect()
#     worker_status = celery_info.app.current_worker_task
#     if not worker_status:
#         return True
#     else:
#         return False
#
#
# def start_worker():
#     if not worker_is_on():
#         bash_command = "heroku ps:scale --app cirs-dev worker=1:performance-l"
#         subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
#     return
#
#
# def stop_worker():
#     if worker_is_on():
#         bash_command = "heroku ps:scale --app cirs-dev worker=0:performance-l"
#         subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
#     return
