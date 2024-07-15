import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import os
from threading import Thread
import logging
from main import app  # Importa seu aplicativo Flask do arquivo main.py

class FlaskService(win32serviceutil.ServiceFramework):
    _svc_name_ = "FlaskService"
    _svc_display_name_ = "Flask Web Service"
    _svc_description_ = "A simple Flask web service running as a Windows service."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.server_thread = Thread(target=self.run_server)
        self.is_running = True
        logging.info("FlaskService - Service initialized.")

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        logging.info("FlaskService - Stopping service...")
        self.is_running = False
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        logging.info("FlaskService - Service is starting...")
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ''))
        self.server_thread.start()
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
        logging.info("FlaskService - Service is stopped.")

    def run_server(self):
        logging.info("FlaskService - Starting Flask server...")
        try:
            app.run(debug=False, host='0.0.0.0', port=5000)
        except Exception as e:
            logging.error(f"FlaskService - Error running Flask server: {e}")
            servicemanager.LogErrorMsg(f"FlaskService - Error running Flask server: {e}")

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(FlaskService)
