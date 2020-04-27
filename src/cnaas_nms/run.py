import os
import coverage
import atexit
import signal
import threading
import time
from typing import List
from gevent import monkey, signal as gevent_signal
from redis import StrictRedis

from cnaas_nms.tools.get_apidata import get_apidata
# Do late imports for anything cnaas/flask related so we can do gevent monkey patch, see below


os.environ['PYTHONPATH'] = os.getcwd()


print("Code coverage collection for worker in pid {}: {}".format(
    os.getpid(), ('COVERAGE' in os.environ)))
if 'COVERAGE' in os.environ:
    cov = coverage.coverage(
        data_file='/coverage/.coverage-{}'.format(os.getpid()),
        concurrency="gevent")
    cov.start()

    def save_coverage():
        cov.stop()
        cov.save()

    atexit.register(save_coverage)
    gevent_signal(signal.SIGTERM, save_coverage)
    gevent_signal(signal.SIGINT, save_coverage)


def get_app():
    from cnaas_nms.scheduler.scheduler import Scheduler
    from cnaas_nms.plugins.pluginmanager import PluginManagerHandler
    from cnaas_nms.db.session import sqla_session
    from cnaas_nms.db.joblock import Joblock
    from cnaas_nms.db.job import Job
    # If running inside uwsgi, a separate "mule" will run the scheduler
    try:
        import uwsgi
        print("Running inside uwsgi")
    except (ModuleNotFoundError, ImportError):
        scheduler = Scheduler()
        scheduler.start()

    pmh = PluginManagerHandler()
    pmh.load_plugins()

    try:
        with sqla_session() as session:
            Joblock.clear_locks(session)
    except Exception as e:
        print("Unable to clear old locks from database at startup: {}".format(str(e)))

    try:
        with sqla_session() as session:
            Job.clear_jobs(session)
    except Exception as e:
        print("Unable to clear jobs with invalid states: {}".format(str(e)))
    return app.app


def socketio_emit(message: str, rooms: List[str]):
    if not app.socketio:
        return
    for room in rooms:
        app.socketio.emit("events", message, room=room)


def loglevel_to_rooms(levelname: str) -> List[str]:
    if levelname == 'DEBUG':
        return ['DEBUG']
    elif levelname == 'INFO':
        return ['DEBUG', 'INFO']
    elif levelname == 'WARNING':
        return ['DEBUG', 'INFO', 'WARNING']
    elif levelname == 'ERROR':
        return ['DEBUG', 'INFO', 'WARNING', 'ERROR']
    elif levelname == 'CRITICAL':
        return ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


def parse_redis_event(item):
    try:
        # [stream, [(messageid, {datadict})]
        if item[0] == "events":
            return item[1][0][1]
    except Exception as e:
        return None


def thread_websocket_events():
    redis: StrictRedis
    with redis_session() as redis:
        while True:
            result = redis.xread({"events": b"$"}, count=10, block=200)
            for item in result:
                item = parse_redis_event(item)
                if not item:
                    continue
                if item['type'] == "log":
                    socketio_emit(item['message'], loglevel_to_rooms(item['level']))
                elif item['type'] == "job_id":
                    socketio_emit(item['message'], ["job_id_{}".format(item['job_id'])])
                elif item['type'] == "device_id":
                    socketio_emit(item['message'], ["device_id_{}".format(item['device_id'])])
                elif item['type'] == "update":
                    socketio_emit(item['message'], ["update_{}".format(item['update_type'])])


if __name__ == '__main__':
    # Starting via python run.py
    # gevent monkey patching required if you start flask with the auto-reloader (debug mode)
    monkey.patch_all()
    from cnaas_nms.api import app
    from cnaas_nms.db.session import redis_session

    t_websocket_events = threading.Thread(target=thread_websocket_events)
    t_websocket_events.start()

    apidata = get_apidata()
    if isinstance(apidata, dict) and 'host' in apidata:
        app.socketio.run(get_app(), debug=True, host=apidata['host'])
    else:
        app.socketio.run(get_app(), debug=True)

    if 'COVERAGE' in os.environ:
        save_coverage()
else:
    # Starting via uwsgi
    from cnaas_nms.api import app
    from cnaas_nms.db.session import redis_session

    t_websocket_events = threading.Thread(target=thread_websocket_events)
    t_websocket_events.start()

    cnaas_app = get_app()

    if 'COVERAGE' in os.environ:
        save_coverage()
